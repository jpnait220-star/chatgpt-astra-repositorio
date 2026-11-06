package dev.duckbox.mixin;

import dev.duckbox.DuckBox;
import net.minecraft.entity.MovementType;
import net.minecraft.server.network.*;
import net.minecraft.util.math.Vec3d;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;

@Mixin(ServerPlayNetworkHandler.class)
public abstract class WebPacketMovementMixin {
  @Redirect(
      method = "method_12063",
      at =
          @At(
              value = "INVOKE",
              target =
                  "Lnet/minecraft/class_3222;method_5784(Lnet/minecraft/class_1313;Lnet/minecraft/class_243;)V"),
      remap = false)
  private void duckbox$webPacketMove(ServerPlayerEntity player, MovementType type, Vec3d movement) {
    // The packet already contains client web slowdown. Keep normal block collision checks.
    var access = (WebMovementAccess) player;
    if (DuckBox.ignoreWeb(player) && access.duckbox$getWebSlowdown().equals(DuckBox.WEB_SLOWDOWN))
      access.duckbox$setWebSlowdown(Vec3d.ZERO);
    player.move(type, movement);
  }
}
