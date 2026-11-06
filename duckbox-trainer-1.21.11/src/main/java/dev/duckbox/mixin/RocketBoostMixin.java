package dev.duckbox.mixin;

import dev.duckbox.DuckBox;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.projectile.FireworkRocketEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(FireworkRocketEntity.class)
public abstract class RocketBoostMixin {
  @Accessor(value = "field_7616", remap = false)
  protected abstract LivingEntity duckbox$getShooter();

  @Inject(method = "method_5773", at = @At("HEAD"), remap = false)
  private void duckbox$boost(CallbackInfo ci) {
    LivingEntity shooter = duckbox$getShooter();
    if (shooter != null) DuckBox.rocket(shooter);
  }
}
