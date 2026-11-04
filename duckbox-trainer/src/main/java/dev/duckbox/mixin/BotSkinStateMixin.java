package dev.duckbox.mixin;

import dev.duckbox.cosmetic.BotSkin;
import net.minecraft.client.network.AbstractClientPlayerEntity;
import net.minecraft.client.render.entity.PlayerEntityRenderer;
import net.minecraft.client.render.entity.state.PlayerEntityRenderState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(PlayerEntityRenderer.class)
public abstract class BotSkinStateMixin {
  @Inject(method = "method_62604", at = @At("TAIL"), remap = false)
  private void duckbox$robotState(
      AbstractClientPlayerEntity player,
      PlayerEntityRenderState state,
      float tickDelta,
      CallbackInfo ci) {
    BotSkin.apply(player.getUuid(), state);
  }
}
