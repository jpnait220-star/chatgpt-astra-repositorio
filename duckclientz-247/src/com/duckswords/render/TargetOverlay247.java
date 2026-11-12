package com.duckswords.render;
import java.util.*;import net.minecraft.class_238;import net.minecraft.class_243;import net.minecraft.class_310;import net.minecraft.class_2338;import net.minecraft.class_2680;import net.minecraft.class_3726;
/** Entity-independent overlay, clipped against the block shapes before its no-depth draw. */
public final class TargetOverlay247 {
 private static final int[][] EDGES={{0,1},{0,2},{0,4},{1,3},{1,5},{2,3},{2,6},{4,5},{4,6},{3,7},{5,7},{6,7}};
 private TargetOverlay247(){}
 private static class_243 camera(Object context){throw new IllegalStateException("native camera adapter");}
 private static void raw(Object context,double x,double y,double z,double xx,double yy,double zz,int color,float width){throw new IllegalStateException("native line adapter");}
 private static void fallback(Object context,class_238 box,float r,float g,float b,float a){throw new IllegalStateException("native depth fallback");}
 public static void drawBox(Object context,class_238 box,float r,float g,float b,float alpha){
  if(context==null||box==null||alpha<=0)return;
  class_310 client=class_310.method_1551();if(client.field_1687==null)return;
  class_243 eye=camera(context);if(eye==null)return;double[] camera={eye.field_1352,eye.field_1351,eye.field_1350};
  int minX=(int)Math.floor(Math.min(camera[0],box.field_1323))-1,minY=(int)Math.floor(Math.min(camera[1],box.field_1322))-1,minZ=(int)Math.floor(Math.min(camera[2],box.field_1321))-1;
  int maxX=(int)Math.floor(Math.max(camera[0],box.field_1320))+1,maxY=(int)Math.floor(Math.max(camera[1],box.field_1325))+1,maxZ=(int)Math.floor(Math.max(camera[2],box.field_1324))+1;
  long cells=((long)maxX-minX+1)*((long)maxY-minY+1)*((long)maxZ-minZ+1);
  if(cells<0||cells>8192){fallback(context,box,r,g,b,alpha);return;}
  List<double[]> blocks=new ArrayList<>();
  for(int x=minX;x<=maxX;x++)for(int y=minY;y<=maxY;y++)for(int z=minZ;z<=maxZ;z++){
   class_2338 pos=new class_2338(x,y,z);class_2680 state=client.field_1687.method_8320(pos);if(state.method_26215())continue;
   for(class_238 shape:state.method_26202(client.field_1687,pos,class_3726.method_16194()).method_1090()){
    blocks.add(new double[]{x+shape.field_1323,y+shape.field_1322,z+shape.field_1321,x+shape.field_1320,y+shape.field_1325,z+shape.field_1324});
    if(blocks.size()>4096){fallback(context,box,r,g,b,alpha);return;}
   }
  }
  double[][] points=new double[8][];for(int i=0;i<8;i++)points[i]=new double[]{(i&1)==0?box.field_1323:box.field_1320,(i&2)==0?box.field_1322:box.field_1325,(i&4)==0?box.field_1321:box.field_1324};
  int color=channel(alpha)<<24|channel(r)<<16|channel(g)<<8|channel(b);
  for(int[] edge:EDGES){double[] a=points[edge[0]],end=points[edge[1]],visible=BlockShadow247.visible(camera,a,end,blocks);
   for(int i=0;i<visible.length;i+=2){double t=visible[i],u=visible[i+1];if(u-t<1e-7)continue;
    raw(context,a[0]+(end[0]-a[0])*t,a[1]+(end[1]-a[1])*t,a[2]+(end[2]-a[2])*t,a[0]+(end[0]-a[0])*u,a[1]+(end[1]-a[1])*u,a[2]+(end[2]-a[2])*u,color,1f);
   }
  }
 }
 private static int channel(float value){return (int)(Math.max(0,Math.min(1,value))*255);}
}
