package dev.duckbox.mixin;

import dev.duckbox.cosmetic.*;
import net.minecraft.client.network.PlayerListEntry;
import net.minecraft.client.util.SkinTextures;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(PlayerListEntry.class)
public abstract class BotSkinEntryMixin {
  @Inject(method = "method_52810", at = @At("HEAD"), cancellable = true, remap = false)
  private void duckbox$robotSkin(CallbackInfoReturnable<SkinTextures> cir) {
    if (CosmeticState.isBot(((PlayerListEntry) (Object) this).getProfile().getId()))
      cir.setReturnValue(BotSkin.ROBOT);
  }
}
