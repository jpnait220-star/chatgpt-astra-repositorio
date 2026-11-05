package dev.duckbox.mixin;

import dev.duckbox.cosmetic.LegacyChestModel;
import net.minecraft.client.render.TexturedRenderLayers;
import net.minecraft.client.render.entity.model.LoadedEntityModels;
import net.minecraft.client.render.item.model.special.*;
import net.minecraft.util.Identifier;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(ChestModelRenderer.Unbaked.class)
public abstract class TrainerChestItemMixin {
  @Inject(method = "method_65698", at = @At("RETURN"), cancellable = true, remap = false)
  private void duckbox$oldUV(
      LoadedEntityModels models, CallbackInfoReturnable<SpecialModelRenderer<?>> cir) {
    var self = (ChestModelRenderer.Unbaked) (Object) this;
    if (self.texture().equals(Identifier.of("duckbox", "profile")))
      cir.setReturnValue(
          new ChestModelRenderer(
              LegacyChestModel.create(),
              TexturedRenderLayers.createChestTextureId(self.texture()),
              self.openness()));
  }
}
