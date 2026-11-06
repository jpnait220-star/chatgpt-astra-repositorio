package dev.duckbox.mixin;

import net.minecraft.entity.player.PlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;

@Mixin(PlayerEntity.class)
public abstract class TrainerCriticalMixin {
  // Preserve the first sprint check (knockback); only the critical restriction changes.
  @Redirect(method = "method_7324", at = @At(value = "INVOKE",
      target = "Lnet/minecraft/class_1657;method_5624()Z", ordinal = 1), remap = false)
  private boolean duckbox$critSprint(PlayerEntity player) {
    return dev.duckbox.DuckBox.sprintBlocksCritical(player);
  }
}
