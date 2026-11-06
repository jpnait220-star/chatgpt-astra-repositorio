package dev.duckbox.mixin;
import net.minecraft.client.network.PlayerListEntry;
import net.minecraft.util.Identifier;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
@Mixin(PlayerListEntry.class)
public abstract class BotSkinEntryMixin {
 @Inject(method="method_2968",at=@At("HEAD"),cancellable=true,remap=false)
 private void duckbox$skin(CallbackInfoReturnable<Identifier> ci){if(dev.duckbox.cosmetic.CosmeticState.isBot(((PlayerListEntry)(Object)this).getProfile().getId()))ci.setReturnValue(dev.duckbox.cosmetic.BotSkin.TEXTURE);}
 @Inject(method={"method_2979()Lnet/minecraft/class_2960;","method_2957()Lnet/minecraft/class_2960;"},at=@At("HEAD"),cancellable=true,remap=false)
 private void duckbox$cape(CallbackInfoReturnable<Identifier> ci){if(dev.duckbox.cosmetic.CosmeticState.isBot(((PlayerListEntry)(Object)this).getProfile().getId()))ci.setReturnValue(dev.duckbox.cosmetic.BotSkin.CAPE);}
}
