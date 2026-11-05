import dev.duckbox.cosmetic.*;
import net.minecraft.*;
import net.minecraft.client.model.*;
import net.minecraft.client.render.*;
import net.minecraft.client.render.entity.model.PlayerEntityModel;
import net.minecraft.client.util.math.MatrixStack;

public final class CosmeticMeshTest {
  static class Recorder implements VertexConsumer {
    int vertices;
    java.util.List<String> tuples = new java.util.ArrayList<>();
    float vx, vy, vz, tu, tv;
    float minY = Float.POSITIVE_INFINITY, maxY = Float.NEGATIVE_INFINITY;

    void finite(float f) {
      if (!Float.isFinite(f)) throw new AssertionError("NaN/Inf cosmetic vertex");
    }

    public VertexConsumer vertex(float x, float y, float z) {
      finite(x);
      finite(y);
      finite(z);
      vertices++;
      vx = x;
      vy = y;
      vz = z;
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
      return this;
    }

    public VertexConsumer color(int r, int g, int b, int a) {
      return this;
    }

    public VertexConsumer texture(float u, float v) {
      finite(u);
      finite(v);
      tu = u;
      tv = v;
      return this;
    }

    public VertexConsumer overlay(int u, int v) {
      return this;
    }

    public VertexConsumer light(int u, int v) {
      return this;
    }

    public VertexConsumer normal(float x, float y, float z) {
      finite(x);
      finite(y);
      finite(z);
      tuples.add(
          Math.round(vx * 10000)
              + ":"
              + Math.round(vy * 10000)
              + ":"
              + Math.round(vz * 10000)
              + ":"
              + Math.round(tu * 10000)
              + ":"
              + Math.round(tv * 10000)
              + ":"
              + Math.round(x * 10000)
              + ":"
              + Math.round(y * 10000)
              + ":"
              + Math.round(z * 10000));
      return this;
    }
  }

  public static void main(String[] args) throws Exception {
    SharedConstants.createGameVersion();
    Bootstrap.initialize();
    NativeModBootstrap.prepare();
    net.minecraft.client.render.item.model.special.SpecialModelTypes.bootstrap();
    var modelTypes =
        net.minecraft.client.render.item.model.special.SpecialModelTypes.class.getDeclaredField(
            "field_55453");
    modelTypes.setAccessible(true);
    @SuppressWarnings("unchecked")
    var mapper =
        (net.minecraft.util.dynamic.Codecs.IdMapper<
                net.minecraft.util.Identifier,
                com.mojang.serialization.MapCodec<
                    ? extends
                        net.minecraft.client.render.item.model.special.SpecialModelRenderer
                            .Unbaked>>)
            modelTypes.get(null);
    mapper.put(
        net.minecraft.util.Identifier.of("duckbox", "panel"),
        dev.duckbox.panels.PanelItemRenderer.Unbaked.CODEC);
    for (String name : dev.duckbox.panels.MapPanels.NAMES) {
      var input =
          CosmeticMeshTest.class.getResourceAsStream(
              "/assets/duckbox/items/painel_" + name + ".json");
      var json =
          com.google.gson.JsonParser.parseReader(
                  new java.io.InputStreamReader(input, java.nio.charset.StandardCharsets.UTF_8))
              .getAsJsonObject();
      var unbaked =
          net.minecraft.client.render.item.model.special.SpecialModelTypes.CODEC
              .parse(
                  com.mojang.serialization.JsonOps.INSTANCE,
                  json.getAsJsonObject("model").getAsJsonObject("model"))
              .getOrThrow();
      var renderer = (dev.duckbox.panels.PanelItemRenderer) unbaked.bake(null);
      var picture = new Recorder();
      renderer.render(
          net.minecraft.item.ModelTransformationMode.GUI,
          new MatrixStack(),
          layer -> picture,
          15728880,
          0,
          false);
      float expectedHeight = name.equals("start_sheet") ? 2f / 3 : 1;
      if (picture.vertices != 4 || Math.abs(picture.maxY - picture.minY - expectedHeight) > .001)
        throw new AssertionError("Native panel item codec/quad geometry/aspect failed: " + name);
    }
    System.out.println(
        "PASS PANEL ITEM MODELS:24 real native special-model JSON codecs, raw-texture quads, finite"
            + " UVs and preserved3to2 sheet aspect without GPU");
    var legacyChest = LegacyChestModel.create();
    var chestVertices = new Recorder();
    legacyChest.setLockAndLidPitch(0);
    legacyChest.render(new MatrixStack(), chestVertices, 15728880, 0);
    if (chestVertices.vertices != 72 || chestVertices.minY < -.001 || chestVertices.maxY > 1.001)
      throw new AssertionError(
          "Legacy chest model must preserve native dimensions and finite UV vertices");
    legacyChest.setLockAndLidPitch(1);
    legacyChest.render(new MatrixStack(), new Recorder(), 15728880, 0);
    System.out.println(
        "PASS LEGACY CHEST: cached native dimensions, original UVs reoriented in geometry, finite"
            + " closed/open mesh vertices");
    var model =
        new PlayerEntityModel(
            PlayerEntityModel.getTexturedModelData(Dilation.NONE, false)
                .getRoot()
                .createPart(64, 64),
            false);
    var actual = new Recorder();
    new BedrockCosmetic("demon2024bloodfists")
        .draw(model, new MatrixStack(), layer -> actual, 15728880, 0);
    var expected = new Recorder();
    for (boolean mirror : new boolean[] {false, true})
      new ModelPart.Cuboid(
              0,
              21,
              mirror ? -7.9f : 3.9f,
              5,
              -2,
              4,
              7,
              4,
              .4f,
              .4f,
              .4f,
              mirror,
              32,
              32,
              java.util.EnumSet.allOf(net.minecraft.util.math.Direction.class))
          .renderCuboid(
              new MatrixStack().peek(), expected, 15728880, OverlayTexture.DEFAULT_UV, -1);
    if (actual.tuples.size() != 48 || expected.tuples.size() != 48)
      throw new AssertionError("Blood vertex count");
    java.util.Collections.sort(actual.tuples);
    java.util.Collections.sort(expected.tuples);
    if (!actual.tuples.equals(expected.tuples)) {
      for (int i = 0; i < actual.tuples.size(); i++)
        if (!actual.tuples.get(i).equals(expected.tuples.get(i)))
          throw new AssertionError(
              "Blood differs from vanilla cuboid at"
                  + i
                  + " actual="
                  + actual.tuples.get(i)
                  + " expected="
                  + expected.tuples.get(i));
    }
    System.out.println(
        "PASS original Blood left/right mirrored UV/position/normal tuples equal native Minecraft"
            + " cuboids");
    for (String id :
        new String[] {
          "demon2024bloodfists", "theobaldmoneyaura", "gamergamerglasses", "spring2025froghat"
        }) {
      var asset = new BedrockCosmetic(id);
      if (asset.faceCount() == 0) throw new AssertionError("empty mesh");
      Recorder collector = new Recorder();
      VertexConsumerProvider provider = layer -> collector;
      for (float t : new float[] {0, .04f, .21f, .5f, 1.4f, 2.78f}) {
        var matrices = new MatrixStack();
        asset.draw(model, matrices, provider, 15728880, t);
        if (!matrices.isEmpty()) throw new AssertionError("Matrix state leaked");
      }
      if (collector.vertices == 0) throw new AssertionError("invisible cosmetic");
      if (id.contains("money") && collector.maxY - collector.minY < 1)
        throw new AssertionError("Aura shrunk into feet");
      System.out.println(
          "PASS ORIGINAL COSMETIC "
              + id
              + ": "
              + asset.faceCount()
              + " quads; animated poses, finite live vertices/UV/normals, balanced matrices;"
              + " boundsY="
              + collector.minY
              + ".."
              + collector.maxY);
    }
  }
}
