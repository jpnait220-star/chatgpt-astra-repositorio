package dev.duckbox.cosmetic;
import net.minecraft.client.model.*;
import net.minecraft.client.util.math.MatrixStack;
import java.lang.reflect.*;
import org.joml.Vector3f;
/** Preserve the original pre-1.15 skin UVs by flipping each cube's Y/Z geometry. */
public final class LegacyChestModel {
 public static CompatChestModel create(){
  var root=CompatChestModel.getSingleTexturedModelData().createModel();
  root.forEachCuboid(new MatrixStack(),(entry,path,index,cube)->{
   try {
    Field side=java.util.Arrays.stream(cube.getClass().getDeclaredFields()).filter(f->f.getType().isArray()).findFirst().orElseThrow();side.setAccessible(true);
    for(Object quad:(Object[])side.get(cube)) {
     Field vs=java.util.Arrays.stream(quad.getClass().getDeclaredFields()).filter(f->f.getType().isArray()).findFirst().orElseThrow();vs.setAccessible(true);
     for(Object vertex:(Object[])vs.get(quad)) {
      Field pos=java.util.Arrays.stream(vertex.getClass().getDeclaredFields()).filter(f->f.getType()==Vector3f.class).findFirst().orElseThrow();pos.setAccessible(true);
      Vector3f v=(Vector3f)pos.get(vertex);v.set(v.x,cube.minY+cube.maxY-v.y,cube.minZ+cube.maxZ-v.z);
     }
     Field normal=java.util.Arrays.stream(quad.getClass().getDeclaredFields()).filter(f->f.getType()==Vector3f.class).findFirst().orElseThrow();normal.setAccessible(true);
     Vector3f n=(Vector3f)normal.get(quad);n.set(n.x,-n.y,-n.z);
    }
   }catch(ReflectiveOperationException e){throw new IllegalStateException("Chest geometry unavailable",e);}
  });
  return new CompatChestModel(root);
 }
}
