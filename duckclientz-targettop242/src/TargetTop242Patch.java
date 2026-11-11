import java.nio.file.*;import java.util.*;import java.util.zip.*;
import org.objectweb.asm.*;import org.objectweb.asm.tree.*;import org.objectweb.asm.commons.*;
public final class TargetTop242Patch implements Opcodes {
 static final String M="com/duckswords/modules/TargetHighlight",H="com/duckswords/render/TargetTop242",G="com/duckswords/render/TargetTopGeometry242",B="com/duckswords/setting/BooleanSetting",S="com/duckswords/setting/Setting",E="net/minecraft/class_1297",L="net/minecraft/class_1309";
 static ClassNode read(byte[] data){ClassNode c=new ClassNode();new ClassReader(data).accept(c,0);return c;}
 static void write(ClassNode c,Path out,boolean frames)throws Exception{
  ClassWriter w=new ClassWriter(frames?ClassWriter.COMPUTE_FRAMES|ClassWriter.COMPUTE_MAXS:ClassWriter.COMPUTE_MAXS){protected String getCommonSuperClass(String a,String b){return "java/lang/Object";}};
  c.accept(w);Path p=out.resolve(c.name+".class");Files.createDirectories(p.getParent());Files.write(p,w.toByteArray());
 }
 static void reset(MethodNode m){m.instructions.clear();m.tryCatchBlocks.clear();m.localVariables=null;}
 static void field(ClassNode c,String name,String label,String description,boolean initial){
  c.fields.add(new FieldNode(ACC_PUBLIC|ACC_FINAL,name,"L"+B+";",null,null));
  for(MethodNode ctor:c.methods)if(ctor.name.equals("<init>"))for(AbstractInsnNode n:ctor.instructions.toArray())if(n.getOpcode()==RETURN){
   InsnList i=new InsnList();i.add(new VarInsnNode(ALOAD,0));i.add(new VarInsnNode(ALOAD,0));i.add(new TypeInsnNode(NEW,B));i.add(new InsnNode(DUP));i.add(new LdcInsnNode(label));i.add(new LdcInsnNode(description));i.add(new InsnNode(initial?ICONST_1:ICONST_0));i.add(new MethodInsnNode(INVOKESPECIAL,B,"<init>","(Ljava/lang/String;Ljava/lang/String;Z)V",false));i.add(new MethodInsnNode(INVOKEVIRTUAL,M,"add","(L"+S+";)L"+S+";",false));i.add(new TypeInsnNode(CHECKCAST,B));i.add(new FieldInsnNode(PUTFIELD,M,name,"L"+B+";"));ctor.instructions.insertBefore(n,i);
  }
 }
 static void args(InsnList i){i.add(new VarInsnNode(ALOAD,0));i.add(new VarInsnNode(ALOAD,1));for(int x=2;x<=5;x++)i.add(new VarInsnNode(FLOAD,x));}
 static void option(InsnList i){i.add(new VarInsnNode(ALOAD,6));i.add(new FieldInsnNode(GETFIELD,M,"renderTop","L"+B+";"));i.add(new MethodInsnNode(INVOKEVIRTUAL,B,"getValue","()Ljava/lang/Boolean;",false));i.add(new MethodInsnNode(INVOKEVIRTUAL,"java/lang/Boolean","booleanValue","()Z",false));}
 static void wrapper(ClassNode helper,String name,String desc){
  String extended=desc.substring(0,desc.indexOf(')'))+"L"+M+";)V";MethodNode m=new MethodNode(ACC_PUBLIC|ACC_STATIC,name,extended,null,null);InsnList i=m.instructions;LabelNode done=new LabelNode();
  if(name.equals("drawBox")){
   LabelNode normal=new LabelNode();option(i);i.add(new JumpInsnNode(IFEQ,normal));args(i);i.add(new MethodInsnNode(INVOKESTATIC,G,"drawBox",desc,false));i.add(new InsnNode(RETURN));i.add(normal);args(i);i.add(new MethodInsnNode(INVOKESTATIC,"com/duckswords/util/RenderUtil",name,desc,false));i.add(new InsnNode(RETURN));
  }else{
   args(i);i.add(new MethodInsnNode(INVOKESTATIC,"com/duckswords/util/RenderUtil",name,desc,false));option(i);i.add(new JumpInsnNode(IFEQ,done));
   i.add(new VarInsnNode(ALOAD,6));i.add(new FieldInsnNode(GETFIELD,M,"mode","Lcom/duckswords/setting/ModeSetting;"));i.add(new LdcInsnNode("Filled"));i.add(new MethodInsnNode(INVOKEVIRTUAL,"com/duckswords/setting/ModeSetting","is","(Ljava/lang/String;)Z",false));i.add(new JumpInsnNode(IFEQ,done));
   i.add(new VarInsnNode(ALOAD,0));i.add(new VarInsnNode(ALOAD,1));for(int x=2;x<=4;x++)i.add(new VarInsnNode(FLOAD,x));i.add(new InsnNode(FCONST_1));i.add(new VarInsnNode(FLOAD,5));i.add(new LdcInsnNode(4f));i.add(new InsnNode(FMUL));i.add(new MethodInsnNode(INVOKESTATIC,"java/lang/Math","min","(FF)F",false));i.add(new MethodInsnNode(INVOKESTATIC,G,"drawBox",desc,false));i.add(done);i.add(new InsnNode(RETURN));
  }
  helper.methods.add(m);
 }
 public static void main(String[] a)throws Exception{
  Path out=Path.of(a[1]);boolean modern=a[2].equals("1.21.11");ClassNode helper=read(Files.readAllBytes(Path.of(a[3],H+".class")));
  try(ZipFile jar=new ZipFile(a[0])){
   ClassNode module=read(jar.getInputStream(jar.getEntry(M+".class")).readAllBytes());
   field(module,"renderTop","RenderTop","Desenha o contorno da hitbox por cima do modelo do jogador",true);
   field(module,"onlyElytra","Apenas elytra","Destaca somente alvos com a elytra ativada, planando",false);
   int filtering=0,rendering=0,boxes=0;Set<String> wrapped=new HashSet<>();
   for(MethodNode m:module.methods){
    if(!modern&&m.name.startsWith("lambda$")&&m.desc.equals("(L"+E+";)Z"))for(AbstractInsnNode n:m.instructions.toArray())if(n.getOpcode()==IRETURN){InsnList i=new InsnList();i.add(new VarInsnNode(ALOAD,0));i.add(new VarInsnNode(ALOAD,1));i.add(new MethodInsnNode(INVOKESTATIC,H,"allowed","(ZL"+M+";Ljava/lang/Object;)Z",false));m.instructions.insertBefore(n,i);filtering++;}
    for(AbstractInsnNode n:m.instructions.toArray())if(n instanceof MethodInsnNode call){
     if(modern&&m.name.equals("onTick")&&call.owner.equals(E)&&call.name.equals("method_5805")&&call.desc.equals("()Z")){
      m.instructions.insertBefore(n,new VarInsnNode(ALOAD,0));m.instructions.set(n,new MethodInsnNode(INVOKESTATIC,H,"candidate","(Ljava/lang/Object;L"+M+";)Z",false));filtering++;
     }
     if(m.name.equals("onWorldRender")&&call.owner.equals("com/duckswords/cleaner/CleanerRuntime")&&call.name.equals("visible")){
      m.instructions.insertBefore(n,new VarInsnNode(ALOAD,0));m.instructions.set(n,new MethodInsnNode(INVOKESTATIC,H,"render","(Ljava/lang/Object;L"+M+";)Z",false));rendering++;
     }
     if(m.name.equals("onWorldRender")&&call.owner.equals("com/duckswords/util/RenderUtil")&&Set.of("drawBox","drawFilledBox").contains(call.name)){
      if(wrapped.add(call.name))wrapper(helper,call.name,call.desc);m.instructions.insertBefore(n,new VarInsnNode(ALOAD,0));call.owner=H;call.desc=call.desc.substring(0,call.desc.indexOf(')'))+"L"+M+";)V";boxes++;
     }
    }
   }
   if(filtering<1||rendering!=1||boxes!=2)throw new IllegalStateException("Target hook mismatch "+filtering+"/"+rendering+"/"+boxes);
   for(MethodNode m:helper.methods)if(Set.of("alive","visible","gliding").contains(m.name)){
    reset(m);InsnList i=m.instructions;LabelNode no=new LabelNode();String type=m.name.equals("gliding")?L:E;
    i.add(new VarInsnNode(ALOAD,0));i.add(new TypeInsnNode(INSTANCEOF,type));i.add(new JumpInsnNode(IFEQ,no));i.add(new VarInsnNode(ALOAD,0));i.add(new TypeInsnNode(CHECKCAST,type));
    if(m.name.equals("visible"))i.add(new MethodInsnNode(INVOKESTATIC,"com/duckswords/cleaner/CleanerRuntime","visible","(L"+E+";)Z",false));
    else i.add(new MethodInsnNode(INVOKEVIRTUAL,type,m.name.equals("gliding")?"method_6128":"method_5805","()Z",false));
    i.add(new InsnNode(IRETURN));i.add(no);i.add(new InsnNode(ICONST_0));i.add(new InsnNode(IRETURN));
   }
   String original=modern?"com/duckswords/util/RenderUtil":"com/duckswords/perf/WorldGeometry";
   ClassNode geometry=new ClassNode();new ClassReader(jar.getInputStream(jar.getEntry(original+".class"))).accept(new ClassRemapper(geometry,new Remapper(){public String map(String n){return n.equals(original)?G:n;}}),0);
   int materials=0;
   for(MethodNode m:geometry.methods)if(m.name.equals("drawBox"))for(AbstractInsnNode n:m.instructions.toArray())if(n instanceof MethodInsnNode call&&call.owner.equals("com/duckswords/render/WebLineLayers")&&call.name.equals("layer")){
    m.instructions.insertBefore(n,new InsnNode(POP));call.name="special";call.desc="()Ljava/lang/Object;";materials++;
   }
   if(materials!=1)throw new IllegalStateException("Missing cached no-depth line material: "+materials);
   write(module,out,false);write(helper,out,true);write(geometry,out,false);
   System.out.println("PASS TargetHighlight options / elytra filter / dedicated no-depth outline: "+a[2]);
  }
 }
}
