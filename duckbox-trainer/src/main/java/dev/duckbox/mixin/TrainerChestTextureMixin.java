package dev.duckbox.mixin;

import dev.duckbox.TrainerChests;
import net.minecraft.block.entity.*;
import net.minecraft.block.enums.ChestType;
import net.minecraft.client.render.TexturedRenderLayers;
import net.minecraft.client.util.SpriteIdentifier;
import net.minecraft.util.Identifier;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(TexturedRenderLayers.class)
public abstract class TrainerChestTextureMixin {
  private static final SpriteIdentifier DUCKBOX_STOCK =
      new SpriteIdentifier(
          TexturedRenderLayers.CHEST_ATLAS_TEXTURE, Identifier.of("duckbox", "entity/chest/stock"));
  private static final SpriteIdentifier DUCKBOX_PROFILE =
      new SpriteIdentifier(
          TexturedRenderLayers.CHEST_ATLAS_TEXTURE,
          Identifier.of("duckbox", "entity/chest/profile"));

  @Inject(method = "method_24062", at = @At("HEAD"), cancellable = true, remap = false)
  private static void duckbox$texture(
      BlockEntity entity,
      ChestType type,
      boolean christmas,
      CallbackInfoReturnable<SpriteIdentifier> cir) {
    if (type == ChestType.SINGLE && entity instanceof ChestBlockEntity chest) {
      int role = TrainerChests.profile(chest);
      if (role >= 0) cir.setReturnValue(role == 0 ? DUCKBOX_STOCK : DUCKBOX_PROFILE);
    }
  }
}
