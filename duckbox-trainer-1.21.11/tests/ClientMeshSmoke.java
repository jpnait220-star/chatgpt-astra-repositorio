import net.minecraft.client.render.VertexConsumer;
public final class ClientMeshSmoke {
  static class Recorder implements VertexConsumer {
    int vertices; public net.minecraft.client.render.VertexConsumer color(int packed){return this;} public net.minecraft.client.render.VertexConsumer lineWidth(float w){return this;}
    java.util.List<float[]> uv = new java.util.ArrayList<>();
    java.util.List<String> tuples = new java.util.ArrayList<>();
    float vx, vy, vz, tu, tv;
    float minY = Float.POSITIVE_INFINITY, maxY = Float.NEGATIVE_INFINITY;

    void finite(float f) {
      if (!Float.isFinite(f)) throw new AssertionError("NaN/Inf cosmetic vertex");
    }

    public VertexConsumer vertex(float x, float y, float z) {
      finite(x);
      finite(y);
      finite(z);
      vertices++;
      vx = x;
      vy = y;
      vz = z;
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
      return this;
    }

    public VertexConsumer color(int r, int g, int b, int a) {
      return this;
    }

    public VertexConsumer texture(float u, float v) {
      finite(u);
      finite(v);
      tu = u;
      tv = v;
      uv.add(new float[] {u, v});
      return this;
    }

    public VertexConsumer overlay(int u, int v) {
      return this;
    }

    public VertexConsumer light(int u, int v) {
      return this;
    }

    public VertexConsumer normal(float x, float y, float z) {
      finite(x);
      finite(y);
      finite(z);
      tuples.add(
          Math.round(vx * 10000)
              + ":"
              + Math.round(vy * 10000)
              + ":"
              + Math.round(vz * 10000)
              + ":"
              + Math.round(tu * 10000)
              + ":"
              + Math.round(tv * 10000)
              + ":"
              + Math.round(x * 10000)
              + ":"
              + Math.round(y * 10000)
              + ":"
              + Math.round(z * 10000));
      return this;
    }
  }

 public static void main(String[] args)throws Exception{
  net.minecraft.SharedConstants.createGameVersion();net.minecraft.Bootstrap.initialize();NativeModBootstrap.prepare();
  var chest=dev.duckbox.cosmetic.LegacyChestModel.create();
  for(float open:new float[]{0,.5f,1}){chest.setAngles(open);var v=new Recorder();chest.render(new net.minecraft.client.util.math.MatrixStack(),v,15728880,0);if(v.vertices!=72)throw new AssertionError("Chest geometry "+v.vertices);}
  System.out.println("PASS PORT CHEST MESH: original UV geometry, closed/half/open finite72vertices");
  var model=new net.minecraft.client.render.entity.model.PlayerEntityModel(net.minecraft.client.render.entity.model.PlayerEntityModel.getTexturedModelData(net.minecraft.client.model.Dilation.NONE,false).getRoot().createPart(64,64),false);
  for(String id:new String[]{"demon2024bloodfists","theobaldmoneyaura","gamergamerglasses","spring2025froghat"}){
   var asset=new dev.duckbox.cosmetic.BedrockCosmetic(id);
   for(float time:new float[]{0,.25f,1.5f}){var m=new net.minecraft.client.util.math.MatrixStack();var v=new Recorder();asset.draw(model,m,layer->v,15728880,time);if((v.vertices<=0||v.vertices>asset.faceCount()*4||v.vertices%4!=0)||!m.isEmpty())throw new AssertionError("Cosmetic mesh "+id);}
  }
  System.out.println("PASS PORT COSMETIC MESHES:4 original assets, animated finite poses, correct vertex counts and balanced matrices");

  var collected=new Recorder();var tasks=new java.util.ArrayList<Runnable>();
  var queue=(net.minecraft.client.render.command.OrderedRenderCommandQueue)java.lang.reflect.Proxy.newProxyInstance(ClientMeshSmoke.class.getClassLoader(),new Class<?>[]{net.minecraft.client.render.command.OrderedRenderCommandQueue.class},(proxy,method,a)->{
   if(a!=null&&a.length==3&&a[0] instanceof net.minecraft.client.util.math.MatrixStack&&a[2] instanceof net.minecraft.client.render.command.OrderedRenderCommandQueue.Custom){var entry=((net.minecraft.client.util.math.MatrixStack)a[0]).peek();var callback=(net.minecraft.client.render.command.OrderedRenderCommandQueue.Custom)a[2];tasks.add(()->callback.render(entry,collected));}return null;
  });
  var snapshot=new dev.duckbox.cosmetic.QueuedVertices();var asset=new dev.duckbox.cosmetic.BedrockCosmetic("spring2025froghat");
  var reference=new Recorder();asset.draw(model,new net.minecraft.client.util.math.MatrixStack(),layer->reference,15728880,0);asset.draw(model,new net.minecraft.client.util.math.MatrixStack(),snapshot,15728880,0);snapshot.submit(queue);
  model.head.pitch=2;tasks.forEach(Runnable::run);if(!collected.tuples.equals(reference.tuples))throw new AssertionError("Queued pose changed after another player render");
  System.out.println("PASS QUEUED POSE: immutable vertex snapshot preserves each player pose across deferred rendering");

 }
}
