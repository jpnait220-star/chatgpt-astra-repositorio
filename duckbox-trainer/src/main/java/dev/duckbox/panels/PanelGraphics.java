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
    var entry = matrices.peek();
    var vertices = consumers.getBuffer(RenderLayer.getEntityCutoutNoCull(texture));
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
