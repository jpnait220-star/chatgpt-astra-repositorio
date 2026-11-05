package dev.duckbox.chests;

import dev.duckbox.TrainerChests;
import dev.duckbox.cosmetic.LegacyChestModel;
import net.minecraft.block.ChestBlock;
import net.minecraft.client.render.*;
import net.minecraft.client.render.block.entity.BlockEntityRenderer;
import net.minecraft.client.render.block.entity.model.ChestBlockModel;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.RotationAxis;

public final class DuckChestRenderer implements BlockEntityRenderer<DuckChestEntity> {
  private final ChestBlockModel stock =
      new ChestBlockModel(ChestBlockModel.getSingleTexturedModelData().createModel());
  private final ChestBlockModel profile = LegacyChestModel.create();
  private static final Identifier
      STOCK = Identifier.of("duckbox", "textures/entity/chest/stock.png"),
      PROFILE = Identifier.of("duckbox", "textures/entity/chest/profile.png");

  public void render(
      DuckChestEntity chest,
      float delta,
      MatrixStack matrices,
      VertexConsumerProvider consumers,
      int light,
      int overlay) {
    boolean isStock = TrainerChests.profile(chest) == 0;
    var model = isStock ? stock : profile;
    float open = chest.getAnimationProgress(delta);
    open = 1 - (1 - open) * (1 - open) * (1 - open);
    model.setLockAndLidPitch(open);
    matrices.push();
    matrices.translate(.5f, .5f, .5f);
    matrices.multiply(
        RotationAxis.POSITIVE_Y.rotationDegrees(
            -chest.getCachedState().get(ChestBlock.FACING).getPositiveHorizontalDegrees()));
    matrices.translate(-.5f, -.5f, -.5f);
    model.render(
        matrices,
        consumers.getBuffer(RenderLayer.getEntityCutout(isStock ? STOCK : PROFILE)),
        light,
        overlay);
    matrices.pop();
  }
}
