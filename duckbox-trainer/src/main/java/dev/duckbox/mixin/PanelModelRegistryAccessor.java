package dev.duckbox.mixin;
import com.mojang.serialization.MapCodec;
import net.minecraft.client.render.item.model.special.*;
import net.minecraft.util.Identifier;
import net.minecraft.util.dynamic.Codecs;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;
@Mixin(SpecialModelTypes.class)
public interface PanelModelRegistryAccessor{
  @Accessor(value="field_55453",remap=false)
  static Codecs.IdMapper<Identifier,MapCodec<? extends SpecialModelRenderer.Unbaked>> duckbox$types(){throw new AssertionError();}
}
