package dev.duckbox.mixin;

import dev.duckbox.TrainerChests;
import net.minecraft.block.entity.ChestBlockEntity;
import net.minecraft.item.*;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.ActionResult;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(BlockItem.class)
public abstract class TrainerChestPlacementMixin {
  @Inject(method = "method_7712", at = @At("RETURN"), remap = false)
  private void duckbox$placed(
      ItemPlacementContext context, CallbackInfoReturnable<ActionResult> cir) {
    if (cir.getReturnValue().isAccepted()
        && context.getWorld() instanceof ServerWorld world
        && world.getBlockEntity(context.getBlockPos()) instanceof ChestBlockEntity chest
        && TrainerChests.profile(chest) >= 0)
      world.getChunkManager().markForUpdate(context.getBlockPos());
  }
}
