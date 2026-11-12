import java.nio.file.*;import java.util.*;import org.objectweb.asm.*;import org.objectweb.asm.tree.*;
public final class Revision246Patch implements Opcodes{
 static void clear(MethodNode m){m.instructions.clear();m.tryCatchBlocks.clear();m.localVariables=null;}
 public static void main(String[] a)throws Exception{Path common=Path.of(a[3]),out=Path.of(a[1]);String base="com/duckswords/input/";
  for(String helper:List.of("AdaptiveCps243","SmoothCps244","AttackBindings246")){
   byte[] bytes=Files.readAllBytes(common.resolve(base+helper+".class"));ClassNode c=new ClassNode();new ClassReader(bytes).accept(c,0);
   if(helper.equals("AttackBindings246"))for(MethodNode m:c.methods){
    if(m.name.equals("primaryKey")){clear(m);InsnList i=m.instructions;i.add(new MethodInsnNode(INVOKESTATIC,"net/minecraft/class_310","method_1551","()Lnet/minecraft/class_310;",false));i.add(new FieldInsnNode(GETFIELD,"net/minecraft/class_310","field_1690","Lnet/minecraft/class_315;"));i.add(new FieldInsnNode(GETFIELD,"net/minecraft/class_315","field_1886","Lnet/minecraft/class_304;"));i.add(new MethodInsnNode(INVOKEVIRTUAL,"net/minecraft/class_304","method_1428","()Ljava/lang/String;",false));i.add(new InsnNode(ARETURN));}
    if(m.name.equals("keyName")){clear(m);m.instructions.add(new VarInsnNode(ALOAD,0));m.instructions.add(new TypeInsnNode(CHECKCAST,"net/minecraft/class_3675$class_306"));m.instructions.add(new MethodInsnNode(INVOKEVIRTUAL,"net/minecraft/class_3675$class_306","method_1441","()Ljava/lang/String;",false));m.instructions.add(new InsnNode(ARETURN));}
   }
   ClassWriter w=new ClassWriter(ClassWriter.COMPUTE_MAXS);c.accept(w);Path p=out.resolve(base+helper+".class");Files.createDirectories(p.getParent());Files.write(p,w.toByteArray());
  }
  System.out.println("2.46 attack-bound held selection and bidirectional adaptive CPS interpolation: "+a[2]);
 }
}
