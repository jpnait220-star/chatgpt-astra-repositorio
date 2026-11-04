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

  public static void main(String[] args) {
    SharedConstants.createGameVersion();
    Bootstrap.initialize();
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
