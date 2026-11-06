package dev.duckbox.cosmetic;
import java.util.*;
import net.minecraft.client.render.*;
import net.minecraft.client.render.command.OrderedRenderCommandQueue;
import net.minecraft.client.util.math.MatrixStack;
/** Snapshot posed vertices at submission, so later players cannot change queued geometry. */
public final class QueuedVertices implements VertexConsumerProvider {
 private final Map<RenderLayer,Buffer> buffers=new LinkedHashMap<>();
 public VertexConsumer getBuffer(RenderLayer layer){return buffers.computeIfAbsent(layer,k->new Buffer());}
 public void submit(OrderedRenderCommandQueue queue){
  buffers.forEach((layer,buffer)->queue.submitCustom(new MatrixStack(),layer,(entry,out)->{
   for(var v:buffer.vertices)out.vertex(v.x,v.y,v.z).color(v.color).texture(v.u,v.v).overlay(v.overlay).light(v.light).normal(v.nx,v.ny,v.nz);
  }));
 }
 private record V(float x,float y,float z,int color,float u,float v,int overlay,int light,float nx,float ny,float nz){}
 private static final class Buffer implements VertexConsumer {
  final List<V> vertices=new ArrayList<>();float x,y,z,u,v;int color,overlay,light;
  public VertexConsumer vertex(float a,float b,float c){x=a;y=b;z=c;return this;}
  public VertexConsumer color(int r,int g,int b,int a){color=(a<<24)|(r<<16)|(g<<8)|b;return this;}
  public VertexConsumer color(int c){color=c;return this;}
  public VertexConsumer texture(float a,float b){u=a;v=b;return this;}
  public VertexConsumer overlay(int a,int b){overlay=a|(b<<16);return this;}
  public VertexConsumer light(int a,int b){light=a|(b<<16);return this;}
  public VertexConsumer normal(float a,float b,float c){vertices.add(new V(x,y,z,color,u,v,overlay,light,a,b,c));return this;}
  public VertexConsumer lineWidth(float width){return this;}
 }
}
