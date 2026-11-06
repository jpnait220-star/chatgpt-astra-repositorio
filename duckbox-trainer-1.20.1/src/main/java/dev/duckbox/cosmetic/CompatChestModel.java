package dev.duckbox.cosmetic;
import net.minecraft.client.model.*;
import net.minecraft.client.render.*;
import net.minecraft.client.render.block.entity.ChestBlockEntityRenderer;
import net.minecraft.client.util.math.MatrixStack;
public final class CompatChestModel {
 private final ModelPart root;
 public CompatChestModel(ModelPart root) { this.root=root; }
 public static TexturedModelData getSingleTexturedModelData(){return ChestBlockEntityRenderer.getSingleTexturedModelData();}
 public void setLockAndLidPitch(float open){root.getChild("lid").pitch=-(open*(float)Math.PI/2);root.getChild("lock").pitch=root.getChild("lid").pitch;}
 public void render(MatrixStack m,VertexConsumer v,int light,int overlay){root.render(m,v,light,overlay);}
}
