package dev.duckbox.mixin;

import net.minecraft.entity.LivingEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;

@Mixin(LivingEntity.class)
public abstract class TrainerHealingMixin {
  @ModifyVariable(method = "method_6025", at = @At("HEAD"), argsOnly = true, ordinal = 0, remap = false)
  private float duckbox$healingLimit(float amount) {
    return dev.duckbox.DuckBox.limitTrainingHealing((LivingEntity) (Object) this, amount);
  }
}
