package dev.duckbox.panels;
import net.fabricmc.fabric.api.client.rendering.v1.BuiltinItemRendererRegistry;
import net.minecraft.item.ItemStack;
import net.minecraft.client.render.*;
import net.minecraft.client.render.model.json.ModelTransformationMode;
import net.minecraft.client.util.math.MatrixStack;
import dev.duckbox.chests.*;
import dev.duckbox.cosmetic.*;
public final class PanelItemRenderer {
 public static void register(){
  for(var entry:MapPanels.BLOCKS.entrySet()){
   var texture=entry.getValue().textureId;
   BuiltinItemRendererRegistry.INSTANCE.register(entry.getValue(),(stack,mode,m,v,l,o)->
     PanelGraphics.draw(m,v,texture,texture.getPath().contains("start_sheet")?2f/3:1,.5f,false,15728880,o));
  }
  var stock=LegacyChestModel.create();var profile=new CompatChestModel(CompatChestModel.getSingleTexturedModelData().createModel());
  for(var block:java.util.List.of(MapChests.STOCK,MapChests.PROFILE)) {
   boolean isStock=block==MapChests.STOCK;
   BuiltinItemRendererRegistry.INSTANCE.register(block,(stack,mode,m,v,l,o)->{
    var model=isStock?stock:profile;model.setLockAndLidPitch(0);
    model.render(m,v.getBuffer(RenderLayer.getEntityCutout(new net.minecraft.util.Identifier("duckbox","textures/entity/chest/"+(isStock?"stock":"profile")+".png"))),l,o);
   });
  }
 }
}
