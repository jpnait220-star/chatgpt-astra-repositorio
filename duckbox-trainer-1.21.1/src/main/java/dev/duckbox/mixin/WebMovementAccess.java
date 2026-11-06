package dev.duckbox.mixin;

import net.minecraft.entity.Entity;
import net.minecraft.util.math.Vec3d;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

@Mixin(Entity.class)
public interface WebMovementAccess {
  @Accessor(value = "field_17046", remap = false)
  Vec3d duckbox$getWebSlowdown();

  @Accessor(value = "field_17046", remap = false)
  void duckbox$setWebSlowdown(Vec3d value);
}
