package dev.duckbox.panels;
import net.minecraft.client.render.block.entity.*;
import net.minecraft.client.render.block.entity.state.BlockEntityRenderState;
import net.minecraft.client.render.command.*;
import net.minecraft.client.render.state.CameraRenderState;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.math.*;
public final class PanelBlockRenderer implements BlockEntityRenderer<MapPanelEntity,BlockEntityRenderState> {
 public BlockEntityRenderState createRenderState(){return new BlockEntityRenderState();}
 public void render(BlockEntityRenderState panel,MatrixStack m,OrderedRenderCommandQueue q,CameraRenderState camera){
  if(!(panel.blockState.getBlock() instanceof MapPanelBlock block))return;
  m.push();m.translate(.5,.5,.5);m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(180-panel.blockState.get(MapPanelBlock.FACING).getPositiveHorizontalDegrees()));m.translate(-.5,-.5,-.5);
  var vertices=new dev.duckbox.cosmetic.QueuedVertices();PanelGraphics.draw(m,vertices,block.textureId,block.texture.equals("start_sheet")?2f/3:1,-.001f,true,15728880,0);vertices.submit(q);m.pop();
 }
}
