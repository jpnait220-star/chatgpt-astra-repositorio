package dev.duckbox.cosmetic;

import com.google.gson.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import net.minecraft.client.model.ModelPart;
import net.minecraft.client.render.*;
import net.minecraft.client.render.entity.model.PlayerEntityModel;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.RotationAxis;

/**
 * Cached original pack geometry. Direct live vertices avoid constructor-cached UVs in optimization
 * mods.
 */
public final class BedrockCosmetic {
  public final String id;
  private static final float[] HEAD = {0, 24, 0}, LEFT = {5, 22, 0}, RIGHT = {-5, 22, 0};
  private final List<Bone> roots = new ArrayList<>();
  private final Map<String, Bone> bones = new HashMap<>();
  private final Map<String, Map<String, List<Key>>> tracks = new HashMap<>();
  private float length;
  private final Identifier[] textures;
  private float lastTime = Float.NaN;

  private record Key(float time, float[] value, String easing) {}

  private record Face(float[] vertices, float[] uv, float nx, float ny, float nz) {}

  private static final class Cube {
    float[] offset, rotation;
    List<Face> faces = new ArrayList<>();
  }

  private static final class Bone {
    String name, anchor;
    float[] pivot, rotation;
    final float[] pos = new float[3], rot = new float[3], scale = {1, 1, 1};
    List<Bone> children = new ArrayList<>();
    List<Cube> cubes = new ArrayList<>();
  }

  private static JsonObject json(String path) {
    try (var in = BedrockCosmetic.class.getResourceAsStream("/assets/duckbox/cosmetics/" + path)) {
      if (in == null) return null;
      return JsonParser.parseReader(new InputStreamReader(in, StandardCharsets.UTF_8))
          .getAsJsonObject();
    } catch (IOException e) {
      throw new IllegalStateException(path, e);
    }
  }

  private static float[] vector(JsonElement value, float fallback) {
    if (value == null) return new float[] {fallback, fallback, fallback};
    if (value.isJsonObject()) value = value.getAsJsonObject().get("vector");
    if (value == null) return new float[] {fallback, fallback, fallback};
    if (value.isJsonPrimitive()) {
      float f = value.getAsFloat();
      return new float[] {f, f, f};
    }
    var a = value.getAsJsonArray();
    return new float[] {a.get(0).getAsFloat(), a.get(1).getAsFloat(), a.get(2).getAsFloat()};
  }

  private static float[] vec(JsonObject o, String key) {
    return vector(o.get(key), 0);
  }

  public BedrockCosmetic(String id) {
    this.id = id;
    var model = json(id + "/model.json");
    if (model == null) throw new IllegalStateException("Cosmetico ausente: " + id);
    var geometry = model.getAsJsonArray("minecraft:geometry").get(0).getAsJsonObject();
    var desc = geometry.getAsJsonObject("description");
    float tw = desc.get("texture_width").getAsFloat(), th = desc.get("texture_height").getAsFloat();
    for (var value : geometry.getAsJsonArray("bones")) {
      var j = value.getAsJsonObject();
      Bone bone = new Bone();
      bone.name = j.get("name").getAsString();
      bone.pivot = vec(j, "pivot");
      bone.rotation = vec(j, "rotation");
      if (j.has("cubes"))
        for (var c : j.getAsJsonArray("cubes"))
          bone.cubes.add(cube(c.getAsJsonObject(), bone.pivot, tw, th));
      bones.put(bone.name, bone);
    }
    for (var value : geometry.getAsJsonArray("bones")) {
      var j = value.getAsJsonObject();
      Bone b = bones.get(j.get("name").getAsString());
      if (j.has("parent") && bones.containsKey(j.get("parent").getAsString()))
        bones.get(j.get("parent").getAsString()).children.add(b);
      else {
        b.anchor = b.name.toLowerCase(Locale.ROOT);
        roots.add(b);
      }
    }
    var animation = json(id + "/animation.json");
    if (animation != null) {
      var animations = animation.getAsJsonObject("animations");
      var anim = animations.entrySet().iterator().next().getValue().getAsJsonObject();
      length = anim.has("animation_length") ? anim.get("animation_length").getAsFloat() : 0;
      var animated = anim.getAsJsonObject("bones");
      if (animated != null)
        for (var e : animated.entrySet()) {
          Map<String, List<Key>> channels = new HashMap<>();
          for (var channel : e.getValue().getAsJsonObject().entrySet()) {
            List<Key> keys = new ArrayList<>();
            var value = channel.getValue();
            if (value.isJsonArray()
                || value.isJsonPrimitive()
                || value.getAsJsonObject().has("vector"))
              keys.add(
                  new Key(0, vector(value, channel.getKey().equals("scale") ? 1 : 0), "linear"));
            else
              for (var frame : value.getAsJsonObject().entrySet()) {
                var v = frame.getValue();
                String easing =
                    v.isJsonObject() && v.getAsJsonObject().has("easing")
                        ? v.getAsJsonObject().get("easing").getAsString()
                        : "linear";
                keys.add(new Key(Float.parseFloat(frame.getKey()), vector(v, 0), easing));
              }
            keys.sort(Comparator.comparingDouble(Key::time));
            channels.put(channel.getKey(), keys);
          }
          tracks.put(e.getKey(), channels);
        }
    }
    textures =
        id.equals("demon2024bloodfists")
            ? new Identifier[] {
              texture("texture.png"), texture("frame_001.png"), texture("frame_002.png")
            }
            : new Identifier[] {texture("texture.png")};
  }

  private Identifier texture(String file) {
    return Identifier.of("duckbox", "cosmetics/" + id + "/" + file);
  }

  private static void sample(List<Key> keys, float t, float[] out, float fallback) {
    if (keys == null || keys.isEmpty()) {
      Arrays.fill(out, fallback);
      return;
    }
    Key a = keys.get(0), b = a;
    for (var key : keys) {
      b = key;
      if (t <= key.time) break;
      a = key;
    }
    float f = b.time <= a.time ? 0 : Math.max(0, Math.min(1, (t - a.time) / (b.time - a.time)));
    if (a.easing.equals("step")) f = 0;
    else if (a.easing.equals("easeInSine")) f = (float) (1 - Math.cos(f * Math.PI / 2));
    for (int k = 0; k < 3; k++) out[k] = a.value[k] + (b.value[k] - a.value[k]) * f;
  }

  private void pose(float time) {
    if (lastTime == time) return;
    lastTime = time;
    float t = length > 0 ? time % length : time;
    for (var e : tracks.entrySet()) {
      Bone b = bones.get(e.getKey());
      if (b == null) continue;
      sample(e.getValue().get("position"), t, b.pos, 0);
      sample(e.getValue().get("rotation"), t, b.rot, 0);
      sample(e.getValue().get("scale"), t, b.scale, 1);
    }
  }

  public void draw(
      PlayerEntityModel model,
      MatrixStack stack,
      VertexConsumerProvider provider,
      int light,
      float time) {
    draw(model, stack, provider, light, time, null);
  }

  public void draw(
      PlayerEntityModel model,
      MatrixStack stack,
      VertexConsumerProvider provider,
      int light,
      float time,
      Boolean leftOnly) {
    pose(time);
    var texture = textures[(int) (time * 5) % textures.length];
    var buffer = provider.getBuffer(net.minecraft.client.render.RenderLayers.entityCutout(texture));
    for (Bone root : roots) {
      boolean left = root.anchor.contains("leftarm"), right = root.anchor.contains("rightarm");
      if (leftOnly != null && ((leftOnly && !left) || (!leftOnly && !right))) continue;
      ModelPart part =
          root.anchor.contains("head")
              ? model.head
              : left ? model.leftArm : right ? model.rightArm : model.body;
      float[] anchor = root.anchor.contains("head") ? HEAD : left ? LEFT : right ? RIGHT : HEAD;
      stack.push();
      if (!id.equals("theobaldmoneyaura")) part.applyTransform(stack);
      else stack.translate(part.originX / 16f, part.originY / 16f, part.originZ / 16f);
      drawBone(root, anchor, stack, buffer, light);
      stack.pop();
    }
  }

  private static void rotate(MatrixStack m, float x, float y, float z) {
    if (z != 0) m.multiply(RotationAxis.POSITIVE_Z.rotationDegrees(-z));
    if (y != 0) m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(y));
    if (x != 0) m.multiply(RotationAxis.POSITIVE_X.rotationDegrees(-x));
  }

  private static void drawBone(
      Bone b, float[] parent, MatrixStack m, VertexConsumer out, int light) {
    if (b.scale[0] == 0 || b.scale[1] == 0 || b.scale[2] == 0) return;
    m.push();
    m.translate(
        (b.pivot[0] - parent[0] + b.pos[0]) / 16f,
        (parent[1] - b.pivot[1] - b.pos[1]) / 16f,
        (b.pivot[2] - parent[2] + b.pos[2]) / 16f);
    rotate(m, b.rotation[0] + b.rot[0], b.rotation[1] + b.rot[1], b.rotation[2] + b.rot[2]);
    m.scale(b.scale[0], b.scale[1], b.scale[2]);
    for (Cube cube : b.cubes) {
      m.push();
      m.translate(cube.offset[0] / 16f, -cube.offset[1] / 16f, cube.offset[2] / 16f);
      rotate(m, cube.rotation[0], cube.rotation[1], cube.rotation[2]);
      for (Face f : cube.faces)
        for (int v = 0; v < 4; v++)
          out.vertex(m.peek(), f.vertices[v * 3], f.vertices[v * 3 + 1], f.vertices[v * 3 + 2])
              .color(-1)
              .texture(f.uv[v * 2], f.uv[v * 2 + 1])
              .overlay(OverlayTexture.DEFAULT_UV)
              .light(light)
              .normal(m.peek(), f.nx, f.ny, f.nz);
      m.pop();
    }
    for (Bone child : b.children) drawBone(child, b.pivot, m, out, light);
    m.pop();
  }

  private static Cube cube(JsonObject j, float[] bone, float tw, float th) {
    Cube c = new Cube();
    c.rotation = vec(j, "rotation");
    float[] pivot = j.has("pivot") ? vec(j, "pivot") : bone;
    boolean rotated = c.rotation[0] != 0 || c.rotation[1] != 0 || c.rotation[2] != 0;
    if (!rotated) pivot = bone;
    c.offset = new float[] {pivot[0] - bone[0], pivot[1] - bone[1], pivot[2] - bone[2]};
    float[] origin = vec(j, "origin"), size = vec(j, "size");
    float inflate = j.has("inflate") ? j.get("inflate").getAsFloat() : 0;
    float x0 = origin[0] - pivot[0] - inflate,
        x1 = origin[0] + size[0] - pivot[0] + inflate,
        y0 = pivot[1] - origin[1] - size[1] - inflate,
        y1 = pivot[1] - origin[1] + inflate,
        z0 = origin[2] - pivot[2] - inflate,
        z1 = origin[2] + size[2] - pivot[2] + inflate;
    boolean mirrored = j.has("mirror") && j.get("mirror").getAsBoolean();
    if (mirrored) {
      float swap = x0;
      x0 = x1;
      x1 = swap;
    }
    float[][] vertices = {
      {x0, y0, z0},
      {x1, y0, z0},
      {x1, y1, z0},
      {x0, y1, z0},
      {x0, y0, z1},
      {x1, y0, z1},
      {x1, y1, z1},
      {x0, y1, z1}
    };
    String[] names = {"north", "east", "south", "west", "up", "down"};
    int[][] face = {
      {1, 0, 3, 2}, {5, 1, 2, 6}, {4, 5, 6, 7}, {0, 4, 7, 3}, {5, 4, 0, 1}, {2, 3, 7, 6}
    };
    float[][] normals = {{0, 0, -1}, {1, 0, 0}, {0, 0, 1}, {-1, 0, 0}, {0, -1, 0}, {0, 1, 0}};
    JsonElement uv = j.get("uv");
    for (int side = 0; side < 6; side++) {
      float u, v, uw, vh;
      if (uv.isJsonObject()) {
        var f = uv.getAsJsonObject().getAsJsonObject(names[side]);
        if (f == null) continue;
        var a = f.getAsJsonArray("uv");
        var s = f.getAsJsonArray("uv_size");
        u = a.get(0).getAsFloat();
        v = a.get(1).getAsFloat();
        uw = s.get(0).getAsFloat();
        vh = s.get(1).getAsFloat();
        if (uw == 0 || vh == 0) continue;
      } else {
        float bu = uv.getAsJsonArray().get(0).getAsFloat(),
            bv = uv.getAsJsonArray().get(1).getAsFloat(),
            x = size[0],
            y = size[1],
            z = size[2];
        float[] offset =
            switch (side) {
              case 0 -> new float[] {z, z, x, y};
              case 1 -> new float[] {z + x, z, z, y};
              case 2 -> new float[] {z + x + z, z, x, y};
              case 3 -> new float[] {0, z, z, y};
              case 4 -> new float[] {z, 0, x, z};
              default -> new float[] {z + x, z, x, -z};
            };
        u = bu + offset[0];
        v = bv + offset[1];
        uw = offset[2];
        vh = offset[3];
      }
      float[] positions = new float[12];
      for (int k = 0; k < 4; k++)
        for (int axis = 0; axis < 3; axis++)
          positions[k * 3 + axis] = vertices[face[side][k]][axis] / 16f;
      float[] tex = {
        (u + uw) / tw, v / th, u / tw, v / th, u / tw, (v + vh) / th, (u + uw) / tw, (v + vh) / th
      };
      if (mirrored)
        for (int a = 0; a < 2; a++) {
          int b = 3 - a;
          for (int k = 0; k < 3; k++) {
            float temp = positions[a * 3 + k];
            positions[a * 3 + k] = positions[b * 3 + k];
            positions[b * 3 + k] = temp;
          }
          for (int k = 0; k < 2; k++) {
            float temp = tex[a * 2 + k];
            tex[a * 2 + k] = tex[b * 2 + k];
            tex[b * 2 + k] = temp;
          }
        }
      c.faces.add(
          new Face(
              positions,
              tex,
              mirrored ? -normals[side][0] : normals[side][0],
              normals[side][1],
              normals[side][2]));
    }
    return c;
  }

  public int faceCount() {
    return bones.values().stream()
        .mapToInt(b -> b.cubes.stream().mapToInt(c -> c.faces.size()).sum())
        .sum();
  }
}
