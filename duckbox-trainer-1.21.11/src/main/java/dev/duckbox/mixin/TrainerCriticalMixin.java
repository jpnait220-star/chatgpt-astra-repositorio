package dev.duckbox.mixin;

import net.minecraft.entity.player.PlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;

@Mixin(PlayerEntity.class)
public abstract class TrainerCriticalMixin {
  // Elytra movement can clear fallDistance even while descending. Read a scoped
  // descent value only for the vanilla critical predicate; never alter physics.
  @Redirect(method = "method_75197", at = @At(value = "FIELD",
      target = "Lnet/minecraft/class_1657;field_6017:D", opcode = 180), remap = false)
  private double duckbox$critDescent(PlayerEntity player) {
    return dev.duckbox.DuckBox.criticalFallDistance(player);
  }

  // Preserve the first sprint check (knockback); only the critical restriction changes.
  @Redirect(method = "method_75197", at = @At(value = "INVOKE",
      target = "Lnet/minecraft/class_1657;method_5624()Z"), remap = false)
  private boolean duckbox$critSprint(PlayerEntity player) {
    return dev.duckbox.DuckBox.sprintBlocksCritical(player);
  }
}
