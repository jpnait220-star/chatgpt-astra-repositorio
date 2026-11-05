package dev.duckbox.panels;

import net.minecraft.client.render.*;
import net.minecraft.client.render.block.entity.BlockEntityRenderer;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.math.RotationAxis;

public final class PanelBlockRenderer implements BlockEntityRenderer<MapPanelEntity> {
  public void render(
      MapPanelEntity panel,
      float delta,
      MatrixStack matrices,
      VertexConsumerProvider consumers,
      int light,
      int overlay) {
    if (!(panel.getCachedState().getBlock() instanceof MapPanelBlock block)) return;
    matrices.push();
    matrices.translate(.5f, .5f, .5f);
    matrices.multiply(
        RotationAxis.POSITIVE_Y.rotationDegrees(
            180 - panel.getCachedState().get(MapPanelBlock.FACING).getPositiveHorizontalDegrees()));
    matrices.translate(-.5f, -.5f, -.5f);
    PanelGraphics.draw(
        matrices,
        consumers,
        block.textureId,
        block.texture.equals("start_sheet") ? 2f / 3 : 1,
        -.001f,
        true,
        15728880,
        overlay);
    matrices.pop();
  }
}
