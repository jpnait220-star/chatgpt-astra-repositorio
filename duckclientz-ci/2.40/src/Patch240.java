import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;
import jdk.internal.org.objectweb.asm.*;
import jdk.internal.org.objectweb.asm.tree.*;

/** Targeted patches against the tested beta.2.39 baseline, never a full source rebuild. */
public final class Patch240 {
  static final String SETTINGS = "com/duckswords/setting/KeybindSetting.class";
  static final String HIT = "com/duckswords/modules/HitParticles.class";
  static final String CRIT = "com/duckswords/modules/CritEffects.class";
  static byte[] modify(byte[] bytes, String target) {
    ClassNode node = new ClassNode();
    new ClassReader(bytes).accept(node, 0);
    if (target.equals(SETTINGS)) {
      MethodNode method = node.methods.stream().filter(m -> m.name.equals("isPressed") && m.desc.equals("(Z)Z")).findFirst().orElseThrow();
      // allowExtra |= (mods==0); no extra branches or StackMap frame requirements.
      // For modifier bitmasks 0..15, (mods-1) >>> 31 is 1 iff mods==0.
      InsnList i = new InsnList();
      i.add(new VarInsnNode(Opcodes.ALOAD, 0));
      i.add(new FieldInsnNode(Opcodes.GETFIELD,"com/duckswords/setting/KeybindSetting","mods","I"));
      i.add(new InsnNode(Opcodes.ICONST_1));
      i.add(new InsnNode(Opcodes.ISUB));
      i.add(new IntInsnNode(Opcodes.BIPUSH,31));
      i.add(new InsnNode(Opcodes.IUSHR));
      i.add(new VarInsnNode(Opcodes.ILOAD,1));
      i.add(new InsnNode(Opcodes.IOR));
      i.add(new VarInsnNode(Opcodes.ISTORE,1));
      method.instructions.insert(i);
      method.maxStack=Math.max(method.maxStack,2);
    } else if (target.equals(HIT) || target.equals(CRIT)) {
      String helper=target.equals(HIT)?"hit":"critical";
      MethodNode method=node.methods.stream().filter(m -> m.name.equals("emit") && m.desc.endsWith(")V")).findFirst().orElseThrow();
      int changed=0;
      for(AbstractInsnNode insn=method.instructions.getFirst();insn!=null;insn=insn.getNext()){
        if(insn instanceof MethodInsnNode m && m.owner.equals("com/duckswords/setting/NumberSetting") && m.name.equals("getInt") && m.desc.equals("()I")){
          method.instructions.insert(insn,new MethodInsnNode(Opcodes.INVOKESTATIC,"com/duckswords/perf/VisualBudget240",helper,"(I)I",false));
          changed++;
        }
      }
      if(changed!=1)throw new IllegalStateException("Expected one count read: "+target+" got "+changed);
    } else throw new IllegalArgumentException(target);
    ClassWriter writer=new ClassWriter(0);node.accept(writer);
    byte[] result=writer.toByteArray();
    new ClassReader(result).accept(new ClassVisitor(Opcodes.ASM8){},ClassReader.SKIP_CODE);
    return result;
  }
  public static void main(String[] args)throws Exception{
    if(args.length!=2)throw new IllegalArgumentException("Patch240 <baseline.jar> <patch-dir>");
    Path dest=Path.of(args[1]);Files.createDirectories(dest);
    try(ZipFile zip=new ZipFile(args[0])){
      for(String cls:List.of(SETTINGS,HIT,CRIT)){
        ZipEntry e=zip.getEntry(cls);if(e==null)throw new IllegalStateException(cls+" missing");
        byte[] altered=modify(zip.getInputStream(e).readAllBytes(),cls);
        Path p=dest.resolve(cls);Files.createDirectories(p.getParent());Files.write(p,altered);
        System.out.println("PATCH "+cls);
      }
    }
  }
}