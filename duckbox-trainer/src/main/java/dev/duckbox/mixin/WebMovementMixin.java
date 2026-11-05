package dev.duckbox.mixin;

import dev.duckbox.DuckBox;
import net.minecraft.block.*;
import net.minecraft.entity.Entity;
import net.minecraft.util.math.Vec3d;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;

@Mixin(Entity.class)
public abstract class WebMovementMixin {
  @ModifyVariable(method = "method_5844", at = @At("HEAD"), argsOnly = true, remap = false)
  private Vec3d duckbox$web(Vec3d multiplier, BlockState state, Vec3d original) {
    return state.isOf(Blocks.COBWEB) && DuckBox.ignoreWeb((Entity) (Object) this)
        ? DuckBox.WEB_SLOWDOWN
        : multiplier;
  }
}
