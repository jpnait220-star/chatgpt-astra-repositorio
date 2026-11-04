package dev.duckbox.mixin;

import dev.duckbox.DuckBox;
import net.minecraft.block.*;
import net.minecraft.entity.Entity;
import net.minecraft.util.math.Vec3d;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(Entity.class)
public abstract class WebMovementMixin {
  // Fixed intermediary target for this 1.21.4-only build.
  @Inject(method = "method_5844", at = @At("HEAD"), cancellable = true, remap = false)
  private void duckbox$web(BlockState state, Vec3d multiplier, CallbackInfo ci) {
    if (state.isOf(Blocks.COBWEB) && DuckBox.ignoreWeb((Entity) (Object) this)) ci.cancel();
  }
}
