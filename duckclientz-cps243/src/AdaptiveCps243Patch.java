import java.nio.file.*;import java.util.*;import java.util.zip.*;import org.objectweb.asm.*;import org.objectweb.asm.tree.*;
public final class AdaptiveCps243Patch implements Opcodes {
 static final String CPS="com/duckswords/modules/CpsDisplay",SELECT="com/duckswords/input/AdaptiveCps243";
 static ClassNode read(ZipFile z,String name)throws Exception{ClassNode c=new ClassNode();new ClassReader(z.getInputStream(z.getEntry(name+".class"))).accept(c,0);return c;}
 static MethodNode method(ClassNode c,String name){return c.methods.stream().filter(m->m.name.equals(name)).findFirst().orElseThrow();}
 static void call(InsnList i,String owner,String name,String desc){i.add(new MethodInsnNode(INVOKESTATIC,owner,name,desc,false));}
 static void mc(InsnList i){call(i,"net/minecraft/class_310","method_1551","()Lnet/minecraft/class_310;");}
 static void save(ClassNode c,Path out)throws Exception{ClassWriter w=new ClassWriter(ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS){protected String getCommonSuperClass(String a,String b){return "java/lang/Object";}};c.accept(w);Path p=out.resolve(c.name+".class");Files.createDirectories(p.getParent());Files.write(p,w.toByteArray());}
 public static void main(String[] a)throws Exception{
  Path out=Path.of(a[1]);boolean modern=a[2].equals("1.21.11");try(ZipFile z=new ZipFile(a[0])){
   ClassNode c=read(z,CPS);if(c.methods.stream().anyMatch(m->m.name.endsWith("243")))throw new IllegalStateException("Already patched");
   MethodNode context=new MethodNode(ACC_PRIVATE|ACC_STATIC,"adaptiveContext243","()Z",null,null);InsnList i=context.instructions;LabelNode no=new LabelNode();
   call(i,"com/duckswords/client/ClientData","focused","()Z");i.add(new JumpInsnNode(IFEQ,no));
   for(String[] f:new String[][]{{"field_1755","Lnet/minecraft/class_437;"},{"field_1724","Lnet/minecraft/class_746;"},{"field_1687","Lnet/minecraft/class_638;"}}){mc(i);i.add(new FieldInsnNode(GETFIELD,"net/minecraft/class_310",f[0],f[1]));i.add(new JumpInsnNode(f[0].equals("field_1755")?IFNONNULL:IFNULL,no));}
   i.add(new InsnNode(ICONST_1));i.add(new InsnNode(IRETURN));i.add(no);i.add(new InsnNode(ICONST_0));i.add(new InsnNode(IRETURN));c.methods.add(context);
   MethodNode mouse=new MethodNode(ACC_PUBLIC|ACC_STATIC,"adaptiveMouse243","(II)V",null,null);i=mouse.instructions;LabelNode valid=new LabelNode(),done=new LabelNode();
   call(i,CPS,context.name,context.desc);i.add(new JumpInsnNode(IFNE,valid));call(i,SELECT,"reset","()V");i.add(new InsnNode(RETURN));i.add(valid);
   call(i,"com/duckswords/input/AutoClickerRuntime","synthetic","()Z");i.add(new JumpInsnNode(IFNE,done));i.add(new VarInsnNode(ILOAD,0));i.add(new VarInsnNode(ILOAD,1));call(i,"java/lang/System","nanoTime","()J");call(i,SELECT,"mouse","(IIJ)V");i.add(done);i.add(new InsnNode(RETURN));c.methods.add(mouse);
   MethodNode current=new MethodNode(ACC_PRIVATE|ACC_STATIC,"currentAdaptiveMiddle243","()I",null,null);i=current.instructions;LabelNode live=new LabelNode(),value=new LabelNode();
   call(i,CPS,context.name,context.desc);i.add(new JumpInsnNode(IFNE,live));call(i,SELECT,"reset","()V");i.add(new JumpInsnNode(GOTO,value));i.add(live);
   for(int button=0;button<3;button++){i.add(new InsnNode(ICONST_0+button));call(i,"com/duckswords/util/Keys","isMouseDown","(I)Z");}
   call(i,"java/lang/System","nanoTime","()J");call(i,SELECT,"reconcile","(ZZZJ)V");i.add(value);
   for(String n:List.of("currentLeftCps","currentRightCps","currentMiddleCps"))call(i,CPS,n,"()I");call(i,"java/lang/System","nanoTime","()J");call(i,SELECT,"current","(IIIJ)I");i.add(new InsnNode(IRETURN));c.methods.add(current);
   int changed=0;for(AbstractInsnNode n:method(c,"formatMiddle230").instructions)if(n instanceof MethodInsnNode m&&m.owner.equals(CPS)&&m.name.equals("currentMiddleCps")){m.name=current.name;changed++;}if(changed!=1)throw new IllegalStateException("Formatter hooks "+changed);
   for(AbstractInsnNode n:method(c,"<init>").instructions)if(n instanceof LdcInsnNode l&&l.cst instanceof String s&&s.startsWith("Use {cps}"))l.cst="Use {cps}, {right}; {middle} acompanha o botao usado, inclusive esquerdo/direito ao clicar ou segurar";save(c,out);
   c=read(z,"com/duckswords/mixin/MixinCpsMiddle230");MethodNode observer=method(c,"duck$middleCps230");i=new InsnList();
   if(modern){i.add(new VarInsnNode(ALOAD,3));i.add(new MethodInsnNode(INVOKEVIRTUAL,"net/minecraft/class_11910","comp_4801","()I",false));}else i.add(new VarInsnNode(ILOAD,3));
   i.add(new VarInsnNode(ILOAD,4));call(i,CPS,mouse.name,mouse.desc);observer.instructions.insert(i);save(c,out);
   Path target=out.resolve(SELECT+".class");Files.createDirectories(target.getParent());Files.copy(Path.of(a[3]).resolve(SELECT+".class"),target,StandardCopyOption.REPLACE_EXISTING);
  }System.out.println("Adaptive middle CPS hooks: formatter, physical press/release, context/focus, synthetic exclusion: "+a[2]);
 }
}
