import java.util.*;import java.util.zip.*;import org.objectweb.asm.*;import org.objectweb.asm.tree.*;import org.objectweb.asm.util.*;
public final class TargetDepth245Check implements Opcodes{
 static ClassNode read(ZipFile z,String n)throws Exception{ClassNode c=new ClassNode();new ClassReader(z.getInputStream(z.getEntry(n+".class"))).accept(c,0);return c;}
 static List<AbstractInsnNode> initializer(ClassNode c,String field){
  MethodNode init=c.methods.stream().filter(m->m.name.equals("<clinit>")).findFirst().orElseThrow();ArrayList<AbstractInsnNode> part=new ArrayList<>();
  for(AbstractInsnNode n:init.instructions){part.add(n);if(n instanceof FieldInsnNode f&&f.getOpcode()==PUTSTATIC&&f.owner.equals(c.name)){if(f.name.equals(field))return part;part.clear();}}
  throw new AssertionError("Missing field initializer "+field);
 }
 static void noNoDepth(List<AbstractInsnNode> part){for(AbstractInsnNode n:part)if(n instanceof FieldInsnNode f&&f.name.equals("NO_DEPTH_TEST"))throw new AssertionError("No-depth pipeline inherited");}
 public static void main(String[] a)throws Exception{boolean modern=a[1].equals("1.21.11");try(ZipFile z=new ZipFile(a[0]);ZipFile game=new ZipFile(a[2])){
  String geometry="com/duckswords/render/TargetTopGeometry242",helper="com/duckswords/render/TargetTop242";
  for(String name:List.of(geometry,helper,"com/duckswords/modules/TargetHighlight"))new ClassReader(z.getInputStream(z.getEntry(name+".class"))).accept(new CheckClassAdapter(new ClassWriter(0),false),0);
  ClassNode g=read(z,geometry);int nativeLines=0;
  for(MethodNode m:g.methods)for(AbstractInsnNode n:m.instructions){
   if(n instanceof MethodInsnNode call){if(call.owner.equals("com/duckswords/render/WebLineLayers")||call.name.equals("disableDepthTest"))throw new AssertionError("Target can bypass native depth");if(call.owner.equals("net/minecraft/class_1921")&&call.name.equals("method_23594"))nativeLines++;}
   if(n instanceof FieldInsnNode f&&f.owner.equals("net/minecraft/class_12249")&&f.name.equals("field_64042"))nativeLines++;
  }
  if(nativeLines<1)throw new AssertionError("Missing cached native lines");
  ClassNode h=read(z,helper);int dispatches=0;
  for(MethodNode m:h.methods)for(AbstractInsnNode n:m.instructions)if(n instanceof MethodInsnNode call){if(call.owner.equals("com/duckswords/util/RenderUtil")&&call.name.startsWith("draw"))throw new AssertionError("Normal path can inherit xray material");if(call.owner.equals(geometry))dispatches++;}
  if(dispatches!=4)throw new AssertionError("Box/Filled/Both dispatch mismatch "+dispatches);
  if(modern){
   ClassNode layer=read(game,"net/minecraft/class_12249");noNoDepth(initializer(layer,"field_64042"));
   ClassNode pipelines=read(game,"net/minecraft/class_10799");for(String f:List.of("field_56833","field_56859","field_60126","field_60127"))noNoDepth(initializer(pipelines,f));
   ClassNode builder=read(game,"com/mojang/blaze3d/pipeline/RenderPipeline$Builder");boolean lequal=false;for(MethodNode m:builder.methods)for(AbstractInsnNode n:m.instructions)if(n instanceof FieldInsnNode f&&f.name.equals("LEQUAL_DEPTH_TEST"))lequal=true;if(!lequal)throw new AssertionError("Native default LEQUAL missing");
  }else{
   ClassNode layer=read(game,"net/minecraft/class_1921");MethodNode getter=layer.methods.stream().filter(m->m.name.equals("method_23594")).findFirst().orElseThrow();String field=null;for(AbstractInsnNode n:getter.instructions)if(n instanceof FieldInsnNode f&&f.getOpcode()==GETSTATIC)field=f.name;
   if(field==null)throw new AssertionError("No cached lines field");for(AbstractInsnNode n:initializer(layer,field))if(n instanceof FieldInsnNode f&&f.desc.equals("Lnet/minecraft/class_4668$class_4672;")&&!f.name.equals("field_21348"))throw new AssertionError("Native lines override depth");
   ClassNode builder=read(game,"net/minecraft/class_1921$class_4688$class_4689");boolean lequal=false;for(MethodNode m:builder.methods)if(m.name.equals("<init>"))for(AbstractInsnNode n:m.instructions)if(n instanceof FieldInsnNode f&&f.owner.equals("net/minecraft/class_4668")&&f.name.equals("field_21348"))lequal=true;if(!lequal)throw new AssertionError("Native default LEQUAL missing");
   boolean glLequal=false;for(AbstractInsnNode n:initializer(read(game,"net/minecraft/class_4668"),"field_21348"))if(n instanceof IntInsnNode v&&v.operand==515)glLequal=true;if(!glLequal)throw new AssertionError("Native GL_LEQUAL state missing");
  }
  System.out.println("PASS TargetLight native LEQUAL occlusion; all Box/Filled/Both paths and RenderTop states cannot select no-depth materials: "+a[1]);
 }}
}
