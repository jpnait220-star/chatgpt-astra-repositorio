import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import jdk.internal.org.objectweb.asm.*;
import jdk.internal.org.objectweb.asm.tree.*;
/** Conservative beta.2.40 candidate patch. No game classes are loaded at build time. */
public final class Patch240 {
 static final String SETTINGS="com/duckswords/setting/KeybindSetting.class";
 static final String HIT="com/duckswords/modules/HitParticles.class";
 static final String CRIT="com/duckswords/modules/CritEffects.class";
 static final String COSMETICS="com/duckswords/cosmetic/CosmeticManager.class";
 static byte[] modify(byte[] data,String name){
  ClassNode node=new ClassNode();new ClassReader(data).accept(node,0);
  if(name.equals(SETTINGS)){
   MethodNode m=node.methods.stream().filter(x->x.name.equals("isPressed")&&x.desc.equals("(Z)Z")).findFirst().orElseThrow();
   InsnList i=new InsnList();i.add(new VarInsnNode(Opcodes.ALOAD,0));
   i.add(new FieldInsnNode(Opcodes.GETFIELD,"com/duckswords/setting/KeybindSetting","mods","I"));
   i.add(new InsnNode(Opcodes.ICONST_1));i.add(new InsnNode(Opcodes.ISUB));
   i.add(new IntInsnNode(Opcodes.BIPUSH,31));i.add(new InsnNode(Opcodes.IUSHR));
   i.add(new VarInsnNode(Opcodes.ILOAD,1));i.add(new InsnNode(Opcodes.IOR));
   i.add(new VarInsnNode(Opcodes.ISTORE,1));m.instructions.insert(i);
   m.maxStack=Math.max(2,m.maxStack);
  } else if(name.equals(HIT)||name.equals(CRIT)){
   MethodNode m=node.methods.stream().filter(x->x.name.equals("emit")&&x.desc.endsWith(")V")).findFirst().orElseThrow();
   int found=0;for(AbstractInsnNode i=m.instructions.getFirst();i!=null;i=i.getNext())
    if(i instanceof MethodInsnNode call&&call.owner.equals("com/duckswords/setting/NumberSetting")&&call.name.equals("getInt")&&call.desc.equals("()I")){
     m.instructions.insert(i,new MethodInsnNode(Opcodes.INVOKESTATIC,"com/duckswords/perf/VisualBudget240",name.equals(HIT)?"hit":"critical","(I)I",false));found++;
    }
   if(found!=1)throw new IllegalStateException("Unexpected particles method "+name+" "+found);
  } else if(name.equals(COSMETICS)){
   MethodNode m=node.methods.stream().filter(x->x.name.equals("spawn")&&x.desc.endsWith(")V")).findFirst().orElseThrow();
   int found=0;for(AbstractInsnNode i=m.instructions.getFirst();i!=null;i=i.getNext())
    if(i instanceof MethodInsnNode call&&call.owner.equals("com/duckswords/cosmetic/CosmeticManager")&&call.name.equals("isSafeForView")&&call.desc.endsWith(")Z")){
     m.instructions.insert(i,new MethodInsnNode(Opcodes.INVOKESTATIC,"com/duckswords/perf/VisualBudget240","visible","(Z)Z",false));found++;
    }
   if(found!=1)throw new IllegalStateException("Unexpected cosmetic guard "+found);
  } else throw new IllegalArgumentException(name);
  ClassWriter w=new ClassWriter(ClassWriter.COMPUTE_MAXS);node.accept(w);
  byte[] result=w.toByteArray();new ClassReader(result).accept(new ClassVisitor(Opcodes.ASM8){},ClassReader.SKIP_CODE);
  return result;
 }
 public static void main(String[] argv)throws Exception {
  if(argv.length!=2)throw new IllegalArgumentException("Patch240 base.jar patch-dir");
  Path dst=Path.of(argv[1]);Files.createDirectories(dst);
  try(ZipFile zip=new ZipFile(argv[0])){
   for(String name:List.of(SETTINGS,HIT,CRIT,COSMETICS)){
    ZipEntry ent=zip.getEntry(name);if(ent==null)throw new IllegalStateException("Missing "+name);
    Path file=dst.resolve(name);Files.createDirectories(file.getParent());
    Files.write(file,modify(zip.getInputStream(ent).readAllBytes(),name));
    System.out.println("PATCH "+name);
   }
  }
 }
}