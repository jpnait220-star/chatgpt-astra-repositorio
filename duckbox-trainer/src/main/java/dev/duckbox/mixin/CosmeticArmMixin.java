package dev.duckbox.mixin;

import dev.duckbox.cosmetic.CosmeticFeature;
import net.minecraft.client.model.ModelPart;
import net.minecraft.client.render.VertexConsumerProvider;
import net.minecraft.client.render.entity.PlayerEntityRenderer;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(PlayerEntityRenderer.class)
public abstract class CosmeticArmMixin {
  @Inject(method = "method_23205", at = @At("TAIL"), remap = false)
  private void duckbox$bloodArm(
      MatrixStack matrices,
      VertexConsumerProvider provider,
      int light,
      Identifier skin,
      ModelPart arm,
      boolean sleeve,
      CallbackInfo ci) {
    var model = ((PlayerEntityRenderer) (Object) this).getModel();
    CosmeticFeature.firstPerson(model, matrices, provider, light, arm == model.leftArm);
  }
}
