package dev.duckbox.panels;

import com.mojang.serialization.MapCodec;
import net.minecraft.client.render.*;
import net.minecraft.client.render.entity.model.LoadedEntityModels;
import net.minecraft.client.render.item.model.special.*;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.item.ItemDisplayContext;
import net.minecraft.util.Identifier;

public record PanelItemRenderer(Identifier texture) implements SimpleSpecialModelRenderer {
  public void collectVertices(java.util.function.Consumer<org.joml.Vector3fc> output) {
    for (int x=0;x<2;x++) for(int y=0;y<2;y++) output.accept(new org.joml.Vector3f(x,y,.5f));
  }
  public void render(
      net.minecraft.item.ItemDisplayContext mode,
      MatrixStack matrices,
      net.minecraft.client.render.command.OrderedRenderCommandQueue queue,
      int light,
      int overlay,
      boolean glint, int outline) {
    var consumers = new dev.duckbox.cosmetic.QueuedVertices();
    PanelGraphics.draw(
        matrices,
        consumers,
        texture,
        texture.getPath().contains("start_sheet") ? 2f / 3 : 1,
        .5f,
        false,
        15728880,
        overlay);
    consumers.submit(queue);
  }

  public record Unbaked(Identifier texture) implements SpecialModelRenderer.Unbaked {
    public static final MapCodec<Unbaked> CODEC =
        Identifier.CODEC.fieldOf("texture").xmap(Unbaked::new, Unbaked::texture);

    public MapCodec<? extends SpecialModelRenderer.Unbaked> getCodec() {
      return CODEC;
    }

    public SpecialModelRenderer<?> bake(SpecialModelRenderer.BakeContext models) {
      return new PanelItemRenderer(texture);
    }
  }
}
