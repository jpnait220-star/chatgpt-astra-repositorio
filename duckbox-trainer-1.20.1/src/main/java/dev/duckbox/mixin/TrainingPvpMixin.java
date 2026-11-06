package dev.duckbox.mixin;

import dev.duckbox.DuckBox;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.server.network.ServerPlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(ServerPlayerEntity.class)
public abstract class TrainingPvpMixin {
  @Inject(method = "method_7256", at = @At("HEAD"), cancellable = true, remap = false)
  private void duckbox$duel(PlayerEntity other, CallbackInfoReturnable<Boolean> cir) {
    if (DuckBox.opponents((PlayerEntity) (Object) this, other)) cir.setReturnValue(true);
  }
}
