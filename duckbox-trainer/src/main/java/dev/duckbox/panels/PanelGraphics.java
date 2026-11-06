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
      drawLayer(matrices, consumers, Identifier.of("duckbox", "textures/map_panels/white_background.png"),
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
    boolean sheet = texture.getPath().equals("textures/map_panels/start_sheet.png");
    boolean tile = !sheet && texture.getPath().startsWith("textures/map_panels/start_");
    int columns = sheet ? 3 : 1, rows = sheet ? 2 : 1;
    float insetU = sheet ? 2.5f / 1536 : tile ? 2.5f / 512 : 0;
    float insetV = sheet ? 2.5f / 1024 : tile ? 2.5f / 512 : 0;
    for (int row = 0; row < rows; row++) for (int col = 0; col < columns; col++) {
      float x0 = left + (right - left) * col / columns;
      float x1 = left + (right - left) * (col + 1) / columns;
      float y0 = top + (bottom - top) * row / rows;
      float y1 = top + (bottom - top) * (row + 1) / rows;
      float u0 = (float) col / columns + insetU, u1 = (float) (col + 1) / columns - insetU;
      float v0 = (float) row / rows + insetV, v1 = (float) (row + 1) / rows - insetV;
      vertex(vertices, entry, x0, y0, z, u0, v0, light, overlay, north);
      vertex(vertices, entry, x0, y1, z, u0, v1, light, overlay, north);
      vertex(vertices, entry, x1, y1, z, u1, v1, light, overlay, north);
      vertex(vertices, entry, x1, y0, z, u1, v0, light, overlay, north);
    }
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
