import java.nio.file.*;import java.util.*;import java.util.zip.*;import org.objectweb.asm.*;import org.objectweb.asm.tree.*;import org.objectweb.asm.util.*;
public final class ExtractCps245 implements Opcodes{
 static ClassNode read(ZipFile z,String name)throws Exception{ClassNode c=new ClassNode();new ClassReader(z.getInputStream(z.getEntry(name+".class"))).accept(c,0);return c;}
 static void save(ClassNode c,Path out)throws Exception{ClassWriter w=new ClassWriter(ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS){protected String getCommonSuperClass(String a,String b){return "java/lang/Object";}};c.accept(w);Path p=out.resolve(c.name+".class");Files.createDirectories(p.getParent());Files.write(p,w.toByteArray());}
 public static void main(String[] a)throws Exception{Path out=Path.of(a[1]);try(ZipFile z=new ZipFile(a[0])){
  for(String n:List.of("com/duckswords/modules/CpsDisplay","com/duckswords/mixin/MixinCpsMiddle230","com/duckswords/input/AdaptiveCps243","com/duckswords/input/SmoothCps244"))new ClassReader(z.getInputStream(z.getEntry(n+".class"))).accept(new CheckClassAdapter(new ClassWriter(0),false),0);
  ClassNode c=read(z,"com/duckswords/modules/CpsDisplay");c.superName="java/lang/Object";c.interfaces.clear();c.fields.removeIf(f->(f.access&ACC_STATIC)==0);c.methods.removeIf(m->(m.access&ACC_STATIC)==0);
  for(MethodNode m:c.methods)for(AbstractInsnNode n:m.instructions)if(n instanceof MethodInsnNode call&&call.owner.equals("java/lang/System")&&(call.name.equals("nanoTime")||call.name.equals("currentTimeMillis")))call.owner="Cps243Clock";save(c,out);
  c=read(z,"com/duckswords/mixin/MixinCpsMiddle230");c.name="Mouse243";c.superName="java/lang/Object";c.access=ACC_PUBLIC;c.visibleAnnotations=null;c.invisibleAnnotations=null;
  for(MethodNode m:c.methods){m.access=ACC_PUBLIC;m.visibleAnnotations=null;m.invisibleAnnotations=null;}
  MethodNode ctor=new MethodNode(ACC_PUBLIC,"<init>","()V",null,null);ctor.instructions.add(new VarInsnNode(ALOAD,0));ctor.instructions.add(new MethodInsnNode(INVOKESPECIAL,"java/lang/Object","<init>","()V",false));ctor.instructions.add(new InsnNode(RETURN));c.methods.add(ctor);save(c,out);
  c=read(z,"com/duckswords/input/AdaptiveCps243");save(c,out);
 c=read(z,"com/duckswords/input/SmoothCps244");for(MethodNode m:c.methods)for(AbstractInsnNode n:m.instructions)if(n instanceof MethodInsnNode call&&call.owner.equals("java/lang/System")&&call.name.equals("nanoTime"))call.owner="Cps243Clock";save(c,out);
 }System.out.println("Structural checks and exact static CPS/observer extraction PASS "+a[0]);}
}
