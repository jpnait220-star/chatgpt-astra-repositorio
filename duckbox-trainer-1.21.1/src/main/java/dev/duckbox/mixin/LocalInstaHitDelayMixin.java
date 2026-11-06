package dev.duckbox.mixin;

import dev.duckbox.ClientTrainingState;
import net.minecraft.client.MinecraftClient;
import org.spongepowered.asm.mixin.*;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.*;

@Mixin(MinecraftClient.class)
public abstract class LocalInstaHitDelayMixin {
  @Shadow private int field_1771;

  @Unique
  private boolean duckbox$localInsta() {
    var client = (MinecraftClient) (Object) this;
    return client.player != null
        && client.world != null
        && client.currentScreen == null
        && ClientTrainingState.localNoHitDelay(client.player.getUuid());
  }

  @Inject(method = "method_1536", at = @At("HEAD"), remap = false)
  private void duckbox$beforeClick(CallbackInfoReturnable<Boolean> ci) {
    if (duckbox$localInsta()) field_1771 = 0;
  }

  @Inject(method = "method_1536", at = @At("RETURN"), remap = false)
  private void duckbox$afterClick(CallbackInfoReturnable<Boolean> ci) {
    if (duckbox$localInsta()) field_1771 = 0;
  }

  @Inject(method = "method_1574", at = @At("TAIL"), remap = false)
  private void duckbox$afterTick(CallbackInfo ci) {
    if (duckbox$localInsta()) field_1771 = 0;
  }
}
