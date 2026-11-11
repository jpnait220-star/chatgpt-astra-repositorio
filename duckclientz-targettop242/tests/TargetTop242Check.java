import java.nio.file.*;import java.util.*;import java.util.zip.*;import org.objectweb.asm.*;import org.objectweb.asm.tree.*;import org.objectweb.asm.util.*;
public final class TargetTop242Check implements Opcodes{
 public static void main(String[] args)throws Exception{
  try(ZipFile z=new ZipFile(args[0])){
   for(String n:List.of("com/duckswords/modules/TargetHighlight","com/duckswords/render/TargetTop242","com/duckswords/render/TargetTopGeometry242"))new ClassReader(z.getInputStream(z.getEntry(n+".class"))).accept(new CheckClassAdapter(new ClassWriter(0),false),0);
   ClassNode m=new ClassNode();new ClassReader(z.getInputStream(z.getEntry("com/duckswords/modules/TargetHighlight.class"))).accept(m,0);
   if(m.fields.stream().filter(f->f.name.equals("renderTop")||f.name.equals("onlyElytra")).count()!=2)throw new AssertionError("Missing new options");
   MethodNode ctor=m.methods.stream().filter(x->x.name.equals("<init>")).findFirst().orElseThrow();int initialized=0;
   for(AbstractInsnNode n:ctor.instructions)if(n instanceof FieldInsnNode f&&f.getOpcode()==PUTFIELD&&Set.of("renderTop","onlyElytra").contains(f.name))initialized++;
   if(initialized!=2)throw new AssertionError("Settings not initialized");
   ClassNode geometry=new ClassNode();new ClassReader(z.getInputStream(z.getEntry("com/duckswords/render/TargetTopGeometry242.class"))).accept(geometry,0);
   MethodNode box=geometry.methods.stream().filter(x->x.name.equals("drawBox")).findFirst().orElseThrow();int special=0;
   for(AbstractInsnNode n:box.instructions)if(n instanceof MethodInsnNode call&&call.owner.equals("com/duckswords/render/WebLineLayers")){if(call.name.equals("special"))special++;else if(call.name.equals("layer"))throw new AssertionError("Conditional web material left in top renderer");}
   if(special!=1)throw new AssertionError("Missing cached no-depth material");
   String mix=args[1].equals("1.21.11")?"com/duckswords/mixin/MixinWebPipeline218.class":"com/duckswords/mixin/MixinWebLines218.class";
   ClassNode pipeline=new ClassNode();new ClassReader(z.getInputStream(z.getEntry(mix))).accept(pipeline,0);boolean noDepth=false,noDepthWrite=false;
   for(MethodNode method:pipeline.methods)for(AbstractInsnNode n:method.instructions){
    if(n instanceof FieldInsnNode f&&((f.name.equals("NO_DEPTH_TEST"))||f.name.equals("field_21346")))noDepth=true;
    if(n instanceof FieldInsnNode f&&f.name.equals("field_21350"))noDepthWrite=true;
    if(n instanceof MethodInsnNode call&&call.name.equals("withDepthWrite")){AbstractInsnNode previous=n.getPrevious();while(previous.getOpcode()<0)previous=previous.getPrevious();if(previous.getOpcode()==ICONST_0)noDepthWrite=true;}
   }
   if(!noDepth||!noDepthWrite)throw new AssertionError("Material depth policy missing "+noDepth+"/"+noDepthWrite);
   Path tiny=Path.of(args[2]);boolean living=false,nativeGlide=false;
   for(String line:Files.readAllLines(tiny)){String[] p=line.split("\t");if(p[0].equals("c"))living=p[p.length-1].equals("net/minecraft/class_1309");if(living&&p.length>=5&&p[1].equals("m")&&p[2].equals("()Z")&&p[p.length-1].equals("method_6128"))nativeGlide=true;}
   if(!nativeGlide)throw new AssertionError("Native glide API not present");
   System.out.println("PASS native glide mapping, default option registration, structural bytecode and cached NO_DEPTH/COLOR_ONLY material: "+args[1]);
  }
 }
}
