package dev.duckbox.panels;

import net.minecraft.client.render.*;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;

public final class PanelGraphics {
  public static void draw(
      MatrixStack matrices,
      VertexConsumerProvider consumers,
      Identifier texture,
      float height,
      float z,
      boolean north,
      int light,
      int overlay) {
    if (whiteBackground(texture))
      drawLayer(matrices, consumers, Identifier.ofVanilla("textures/misc/white.png"),
          height, z + (north ? .0005f : -.0005f), north, light, overlay, false);
    drawLayer(matrices, consumers, texture, height, z, north, light, overlay,
        whiteBackground(texture));
  }

  public static boolean whiteBackground(Identifier texture) {
    return switch (texture.getPath()) {
      case "textures/map_panels/easy.png", "textures/map_panels/hard.png",
          "textures/map_panels/harder.png", "textures/map_panels/insane_feature.png" -> true;
      default -> false;
    };
  }

  private static void drawLayer(MatrixStack matrices, VertexConsumerProvider consumers,
      Identifier texture, float height, float z, boolean north, int light, int overlay,
      boolean translucent) {
    var entry = matrices.peek();
    var vertices = consumers.getBuffer(translucent ? RenderLayer.getEntityTranslucent(texture)
        : RenderLayer.getEntityCutoutNoCull(texture));
    float left = north ? 1 : 0,
        right = north ? 0 : 1,
        top = .5f + height / 2,
        bottom = .5f - height / 2;
    vertex(vertices, entry, left, top, z, 0, 0, light, overlay, north);
    vertex(vertices, entry, left, bottom, z, 0, 1, light, overlay, north);
    vertex(vertices, entry, right, bottom, z, 1, 1, light, overlay, north);
    vertex(vertices, entry, right, top, z, 1, 0, light, overlay, north);
  }

  private static void vertex(
      VertexConsumer v,
      MatrixStack.Entry entry,
      float x,
      float y,
      float z,
      float u,
      float w,
      int light,
      int overlay,
      boolean north) {
    v.vertex(entry.getPositionMatrix(), x, y, z)
        .color(255, 255, 255, 255)
        .texture(u, w)
        .overlay(overlay)
        .light(light)
        .normal(entry, 0, 0, north ? -1 : 1);
  }
}
