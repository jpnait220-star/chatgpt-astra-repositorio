package dev.duckbox.mixin;

import dev.duckbox.TrainerChests;
import dev.duckbox.cosmetic.LegacyChestModel;
import net.minecraft.block.ChestBlock;
import net.minecraft.block.entity.*;
import net.minecraft.client.render.*;
import net.minecraft.client.render.block.entity.ChestBlockEntityRenderer;
import dev.duckbox.cosmetic.CompatChestModel;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.RotationAxis;
import org.spongepowered.asm.mixin.*;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(ChestBlockEntityRenderer.class)
public abstract class TrainerChestRenderMixin {
  @Unique private CompatChestModel duckbox$legacy;
  @Unique private CompatChestModel duckbox$stock;

  @Inject(method = "method_3569", at = @At("HEAD"), cancellable = true, remap = false)
  private void duckbox$draw(
      BlockEntity entity,
      float delta,
      MatrixStack matrices,
      VertexConsumerProvider consumers,
      int light,
      int overlay,
      CallbackInfo ci) {
    if (!(entity instanceof ChestBlockEntity chest)) return;
    int role = TrainerChests.profile(chest);
    if (role < 0 || !chest.getCachedState().contains(ChestBlock.FACING)) return;
    if (duckbox$legacy == null) duckbox$legacy = LegacyChestModel.create();
    if (duckbox$stock == null)
      duckbox$stock =
          new CompatChestModel(CompatChestModel.getSingleTexturedModelData().createModel());
    var model = role == 0 ? duckbox$legacy : duckbox$stock;
    float opening = chest.getAnimationProgress(delta);
    opening = 1 - (1 - opening) * (1 - opening) * (1 - opening);
    model.setLockAndLidPitch(opening);
    matrices.push();
    matrices.translate(.5f, .5f, .5f);
    matrices.multiply(
        RotationAxis.POSITIVE_Y.rotationDegrees(
            -chest.getCachedState().get(ChestBlock.FACING).asRotation()));
    matrices.translate(-.5f, -.5f, -.5f);
    var texture =
        new Identifier(
            "duckbox", "textures/entity/chest/" + (role == 0 ? "stock" : "profile") + ".png");
    model.render(
        matrices, consumers.getBuffer(RenderLayer.getEntityCutout(texture)), light, overlay);
    matrices.pop();
    ci.cancel();
  }
}
