package dev.duckbox.panels;

import com.mojang.serialization.MapCodec;
import net.minecraft.client.render.*;
import net.minecraft.client.render.entity.model.LoadedEntityModels;
import net.minecraft.client.render.item.model.special.*;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.item.ModelTransformationMode;
import net.minecraft.util.Identifier;

public record PanelItemRenderer(Identifier texture) implements SimpleSpecialModelRenderer {
  public void render(
      ModelTransformationMode mode,
      MatrixStack matrices,
      VertexConsumerProvider consumers,
      int light,
      int overlay,
      boolean glint) {
    PanelGraphics.draw(
        matrices,
        consumers,
        texture,
        texture.getPath().contains("start_sheet") ? 2f / 3 : 1,
        .5f,
        false,
        15728880,
        overlay);
  }

  public record Unbaked(Identifier texture) implements SpecialModelRenderer.Unbaked {
    public static final MapCodec<Unbaked> CODEC =
        Identifier.CODEC.fieldOf("texture").xmap(Unbaked::new, Unbaked::texture);

    public MapCodec<? extends SpecialModelRenderer.Unbaked> getCodec() {
      return CODEC;
    }

    public SpecialModelRenderer<?> bake(LoadedEntityModels models) {
      return new PanelItemRenderer(texture);
    }
  }
}
