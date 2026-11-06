package dev.duckbox.mixin;

import dev.duckbox.TrainerChests;
import net.minecraft.block.entity.*;
import net.minecraft.component.*;
import net.minecraft.nbt.*;
import net.minecraft.network.listener.ClientPlayPacketListener;
import net.minecraft.network.packet.Packet;
import net.minecraft.network.packet.s2c.play.BlockEntityUpdateS2CPacket;
import net.minecraft.registry.RegistryWrapper;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(BlockEntity.class)
public abstract class TrainerChestSyncMixin {
  @Inject(method = "method_16887", at = @At("RETURN"), cancellable = true, remap = false)
  private void duckbox$chestVisual(
      RegistryWrapper.WrapperLookup registries, CallbackInfoReturnable<NbtCompound> cir) {
    if ((Object) this instanceof ChestBlockEntity chest && TrainerChests.profile(chest) >= 0) {
      // Sync only the role component, never the supply inventory on every chunk packet.
      cir.setReturnValue(TrainerChests.visualData(chest, registries, cir.getReturnValue()));
    }
  }

  @Inject(method = "method_58690", at = @At("TAIL"), remap = false)
  private void duckbox$readRole(
      net.minecraft.storage.ReadView data, CallbackInfo ci) {
    if ((Object) this instanceof ChestBlockEntity chest && data.getOptionalInt("duckbox_visual_role").isPresent()) {
      int role = data.getInt("duckbox_visual_role", -1);
      if (role >= 0 && role <= 4) {
        var marker = new NbtCompound();
        marker.putInt("duckbox_chest_profile", role);
        chest.setComponents(
            ComponentMap.builder()
                .addAll(chest.getComponents())
                .add(
                    DataComponentTypes.CUSTOM_DATA,
                    net.minecraft.component.type.NbtComponent.of(marker))
                .build());
      }
    }
  }

  @Inject(method = "method_38235", at = @At("RETURN"), cancellable = true, remap = false)
  private void duckbox$chestPacket(CallbackInfoReturnable<Packet<ClientPlayPacketListener>> cir) {
    if ((Object) this instanceof ChestBlockEntity chest && TrainerChests.profile(chest) >= 0)
      cir.setReturnValue(BlockEntityUpdateS2CPacket.create(chest));
  }
}
