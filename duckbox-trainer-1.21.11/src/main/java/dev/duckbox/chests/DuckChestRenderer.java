package dev.duckbox.chests;
import dev.duckbox.TrainerChests;
import dev.duckbox.cosmetic.LegacyChestModel;
import net.minecraft.block.ChestBlock;
import net.minecraft.client.render.*;
import net.minecraft.client.render.block.entity.*;
import net.minecraft.client.render.block.entity.model.ChestBlockModel;
import net.minecraft.client.render.block.entity.state.BlockEntityRenderState;
import net.minecraft.client.render.command.*;
import net.minecraft.client.render.state.CameraRenderState;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.*;
import net.minecraft.util.math.*;
public final class DuckChestRenderer implements BlockEntityRenderer<DuckChestEntity,DuckChestRenderer.State>{
 public static class State extends BlockEntityRenderState {public int role;public float open;}
 private final ChestBlockModel stock=LegacyChestModel.create(),profile=new ChestBlockModel(ChestBlockModel.getSingleTexturedModelData().createModel());
 public State createRenderState(){return new State();}
 public void updateRenderState(DuckChestEntity e,State s,float delta,Vec3d camera,ModelCommandRenderer.CrumblingOverlayCommand crumbling){
  BlockEntityRenderer.super.updateRenderState(e,s,delta,camera,crumbling);s.role=TrainerChests.profile(e);float open=e.getAnimationProgress(delta);s.open=1-(1-open)*(1-open)*(1-open);
 }
 public void render(State s,MatrixStack m,OrderedRenderCommandQueue q,CameraRenderState camera){
  m.push();m.translate(.5,.5,.5);m.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-s.blockState.get(ChestBlock.FACING).getPositiveHorizontalDegrees()));m.translate(-.5,-.5,-.5);
  q.submitModel(s.role==0?stock:profile,s.open,m,RenderLayers.entityCutout(Identifier.of("duckbox","textures/entity/chest/"+(s.role==0?"stock":"profile")+".png")),s.lightmapCoordinates,0,-1,null,0,null);m.pop();
 }
}
