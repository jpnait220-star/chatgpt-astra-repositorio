import java.nio.file.*;import java.util.*;import java.util.zip.*;import org.objectweb.asm.*;import org.objectweb.asm.tree.*;
public final class Revision248Patch implements Opcodes {
 static ClassNode read(ZipFile z,String n)throws Exception{ClassNode c=new ClassNode();new ClassReader(z.getInputStream(z.getEntry(n+".class"))).accept(c,0);return c;}
 static void save(ClassNode c,Path out)throws Exception{ClassWriter w=new ClassWriter(ClassWriter.COMPUTE_MAXS);c.accept(w);Path p=out.resolve(c.name+".class");Files.createDirectories(p.getParent());Files.write(p,w.toByteArray());}
 static AbstractInsnNode prev(AbstractInsnNode n){do{n=n.getPrevious();}while(n!=null&&n.getOpcode()<0);return n;}
 static AbstractInsnNode next(AbstractInsnNode n){do{n=n.getNext();}while(n!=null&&n.getOpcode()<0);return n;}
 static void remove(MethodNode m,AbstractInsnNode first,AbstractInsnNode last){for(AbstractInsnNode n=first;;){AbstractInsnNode after=n.getNext();m.instructions.remove(n);if(n==last)break;n=after;}}
 public static void main(String[] a)throws Exception{Path out=Path.of(a[1]);try(ZipFile z=new ZipFile(a[0])){
  ClassNode c=read(z,"com/duckswords/module/ModuleManager");int registrations=0;
  for(MethodNode m:c.methods)if(m.name.equals("init"))for(AbstractInsnNode n:m.instructions.toArray())if(n instanceof TypeInsnNode t&&t.getOpcode()==NEW&&t.desc.equals("com/duckswords/modules/FireworkKey")){
   AbstractInsnNode start=prev(prev(n));if(start.getOpcode()!=ALOAD||prev(n).getOpcode()!=GETFIELD)throw new AssertionError("registration prefix");
   AbstractInsnNode end=n;while(end!=null&&!(end instanceof MethodInsnNode call&&call.name.equals("add")))end=next(end);
   if(end==null||next(end).getOpcode()!=POP)throw new AssertionError("registration suffix");remove(m,start,next(end));registrations++;
  }if(registrations!=1)throw new AssertionError("registration count "+registrations);save(c,out);
  c=read(z,"com/duckswords/input/AutoClickerRuntime");int frame=0;for(MethodNode m:c.methods)for(AbstractInsnNode n:m.instructions.toArray())if(n instanceof MethodInsnNode call&&call.owner.equals("com/duckswords/input/FireworkTiming")){if(!call.name.equals("frame")||!call.desc.equals("()V"))throw new AssertionError("unknown firework hook");m.instructions.remove(n);frame++;}if(frame!=1)throw new AssertionError("frame count "+frame);save(c,out);
  c=read(z,"com/duckswords/modules/ElytraFeature");if(!c.fields.removeIf(f->f.name.equals("bugFix")))throw new AssertionError("missing bugFix field");int initializers=0;
  for(MethodNode m:c.methods)if(m.name.equals("<init>"))for(AbstractInsnNode n:m.instructions.toArray()){
   if(n instanceof FieldInsnNode f&&f.getOpcode()==PUTFIELD&&f.name.equals("bugFix")){
    AbstractInsnNode create=n;while(create!=null&&!(create instanceof TypeInsnNode t&&t.getOpcode()==NEW&&t.desc.equals("com/duckswords/setting/BooleanSetting")))create=prev(create);
    if(create==null||prev(create).getOpcode()!=ALOAD||prev(prev(create)).getOpcode()!=ALOAD)throw new AssertionError("bugfix initializer");remove(m,prev(prev(create)),n);initializers++;
   }
  }
  if(initializers!=1)throw new AssertionError("initializer count "+initializers);
  for(MethodNode m:c.methods)for(AbstractInsnNode n:m.instructions)if(n instanceof LdcInsnNode l&&l.cst instanceof String s&&s.contains("Physics")&&s.contains("corre"))l.cst="Opções de Elytra Physics e indicador visual";
  save(c,out);
  if(!a[2].equals("1.21.1")){c=read(z,"com/duckswords/mixin/MixinLivingEntity");int before=c.methods.size();c.methods.removeIf(m->{for(AbstractInsnNode n:m.instructions)if(n instanceof FieldInsnNode f&&f.owner.equals("com/duckswords/modules/ElytraFeature")&&f.name.equals("bugFix"))return true;return false;});if(before-c.methods.size()!=1)throw new AssertionError("gliding hook count");save(c,out);}
 }System.out.println("PASS remove Firework registration/frame hook and Elytra Bug Fix setting/flight hook: "+a[2]);}
}
