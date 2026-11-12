import java.util.*;import java.util.zip.*;import org.objectweb.asm.*;import org.objectweb.asm.tree.*;import org.objectweb.asm.util.*;
public class Removal248Check {
 static ClassNode read(ZipFile z,String n)throws Exception{ClassNode c=new ClassNode();new ClassReader(z.getInputStream(z.getEntry(n+".class"))).accept(c,0);return c;}
 static List<String> modules(ClassNode c){List<String> result=new ArrayList<>();for(MethodNode m:c.methods)if(m.name.equals("init"))for(AbstractInsnNode n:m.instructions)if(n instanceof TypeInsnNode t&&t.getOpcode()==Opcodes.NEW&&t.desc.startsWith("com/duckswords/"))result.add(t.desc);return result;}
 public static void main(String[] args)throws Exception{try(ZipFile before=new ZipFile(args[0]);ZipFile after=new ZipFile(args[1])){
  List<String> expected=modules(read(before,"com/duckswords/module/ModuleManager"));if(!expected.remove("com/duckswords/modules/FireworkKey"))throw new AssertionError("original module absent");
  if(!expected.equals(modules(read(after,"com/duckswords/module/ModuleManager"))))throw new AssertionError("other module registration changed");
  if(!expected.contains("com/duckswords/modules/ElytraFeature"))throw new AssertionError("visual Elytra removed");
  List<String> changed=new ArrayList<>(List.of("com/duckswords/module/ModuleManager","com/duckswords/input/AutoClickerRuntime","com/duckswords/modules/ElytraFeature"));if(!args[2].equals("1.21.1"))changed.add("com/duckswords/mixin/MixinLivingEntity");
  for(String name:changed)new ClassReader(after.getInputStream(after.getEntry(name+".class"))).accept(new CheckClassAdapter(new ClassWriter(0),false),0);
  ClassNode elytra=read(after,"com/duckswords/modules/ElytraFeature");if(elytra.fields.stream().anyMatch(f->f.name.equals("bugFix")))throw new AssertionError("bugfix field remains");
  System.out.println("PASS full registration order preserved except Firework; visual Elytra retained; changed class structure: "+args[2]+" ("+expected.size()+" modules)");
 }}
}
