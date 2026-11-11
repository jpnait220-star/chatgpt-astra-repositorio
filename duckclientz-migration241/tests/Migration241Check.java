import org.objectweb.asm.*;import org.objectweb.asm.tree.*;import org.objectweb.asm.util.*;
import java.util.*;import java.util.zip.*;import java.nio.file.*;
public final class Migration241Check implements Opcodes{
 public static void main(String[] args)throws Exception{
  try(ZipFile z=new ZipFile(args[0])){
   int checked=0;
   for(String n:Collections.list(z.entries()).stream().map(ZipEntry::getName).filter(n->n.startsWith("com/duckswords/connect/ServiceRoute241")&&n.endsWith(".class")).toList()){
    new ClassReader(z.getInputStream(z.getEntry(n))).accept(new CheckClassAdapter(new ClassWriter(0),false),0);checked++;
   }
   String name="com/duckswords/social/CosmeticSharing.class";ClassNode c=new ClassNode();new ClassReader(z.getInputStream(z.getEntry(name))).accept(c,0);
   new ClassReader(z.getInputStream(z.getEntry(name))).accept(new CheckClassAdapter(new ClassWriter(0),false),0);
   MethodNode request=c.methods.stream().filter(m->m.name.equals("request")&&m.desc.equals("(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;")).findFirst().orElseThrow();
   if(!(request.instructions.get(1)instanceof MethodInsnNode call)||!call.owner.equals("com/duckswords/connect/ServiceRoute241")||!call.name.equals("translate"))throw new AssertionError("Missing entry routing hook");
   // Export the exact patched transport method to isolate it from Minecraft.
   ClassNode probe=new ClassNode();probe.version=V17;probe.access=ACC_PUBLIC|ACC_FINAL;probe.name="com/duckswords/connect/TransportProbe241";probe.superName="java/lang/Object";probe.methods.add(request);
   ClassWriter w=new ClassWriter(ClassWriter.COMPUTE_MAXS);probe.accept(w);Path p=Path.of(args[1],probe.name+".class");Files.createDirectories(p.getParent());Files.write(p,w.toByteArray());
   for(String target:List.of("com/duckswords/update/ClientUpdater229.class","com/duckswords/modules/CosmeticsOnline.class"))new ClassReader(z.getInputStream(z.getEntry(target))).accept(new CheckClassAdapter(new ClassWriter(0),false),0);
   System.out.println("PASS structural bytecode and exact transport hook: "+checked+" added classes and 3 patched classes");
  }
 }
}
