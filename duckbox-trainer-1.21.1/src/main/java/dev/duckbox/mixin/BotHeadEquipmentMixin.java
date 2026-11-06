package dev.duckbox.mixin;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
@Mixin(PlayerEntity.class)
public abstract class BotHeadEquipmentMixin {
 @Inject(method="method_6118",at=@At("HEAD"),cancellable=true,remap=false)
 private void duckbox$skinHead(EquipmentSlot slot,CallbackInfoReturnable<ItemStack> ci){
  var player=(PlayerEntity)(Object)this;
  if(player.getWorld().isClient&&slot==EquipmentSlot.HEAD&&dev.duckbox.cosmetic.CosmeticState.isBot(player.getUuid()))ci.setReturnValue(ItemStack.EMPTY);
 }
}
