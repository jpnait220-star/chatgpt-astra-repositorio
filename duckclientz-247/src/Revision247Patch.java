import java.nio.file.*;import java.util.*;import java.util.zip.*;import org.objectweb.asm.*;import org.objectweb.asm.tree.*;import org.objectweb.asm.commons.*;
public final class Revision247Patch implements Opcodes {
 static final String G="com/duckswords/render/TargetTopGeometry242",RAW="com/duckswords/render/TargetRawLine247",OVER="com/duckswords/render/TargetOverlay247";
 static ClassNode read(ZipFile z,String n)throws Exception{ClassNode c=new ClassNode();new ClassReader(z.getInputStream(z.getEntry(n+".class"))).accept(c,0);return c;}
 static void save(ClassNode c,Path out)throws Exception{ClassWriter w=new ClassWriter(ClassWriter.COMPUTE_MAXS);c.accept(w);Path p=out.resolve(c.name+".class");Files.createDirectories(p.getParent());Files.write(p,w.toByteArray());}
 static MethodNode method(ClassNode c,String n){return c.methods.stream().filter(m->m.name.equals(n)).findFirst().orElseThrow();}
 static void clear(MethodNode m){m.instructions.clear();m.tryCatchBlocks.clear();m.localVariables=null;}
 public static void main(String[] args)throws Exception{Path out=Path.of(args[1]),common=Path.of(args[3]);try(ZipFile z=new ZipFile(args[0])){
  ClassNode geom=read(z,G),raw=new ClassNode();geom.accept(new ClassRemapper(raw,new Remapper(){public String map(String n){return n.equals(G)?RAW:n;}}));
  MethodNode line=method(raw,"drawLine");String context=Type.getArgumentTypes(line.desc)[0].getInternalName();int layers=0;
  for(AbstractInsnNode n:line.instructions.toArray()){
   boolean nativeLayer=n instanceof MethodInsnNode m&&m.owner.equals("net/minecraft/class_1921")&&m.name.equals("method_23594")||n instanceof FieldInsnNode f&&f.owner.equals("net/minecraft/class_12249")&&f.name.equals("field_64042");
   if(nativeLayer){line.instructions.set(n,new MethodInsnNode(INVOKESTATIC,"com/duckswords/render/WebLineLayers","special","()Ljava/lang/Object;",false));AbstractInsnNode after=null; // insert a checked native layer cast after the replacement
    for(AbstractInsnNode q:line.instructions.toArray())if(q instanceof MethodInsnNode m&&m.owner.equals("com/duckswords/render/WebLineLayers")&&m.name.equals("special"))after=q;
    line.instructions.insert(after,new TypeInsnNode(CHECKCAST,"net/minecraft/class_1921"));layers++;
   }
  }
  if(layers!=1)throw new AssertionError("line layer "+layers);
  boolean modern=args[2].equals("1.21.11");if(modern)method(raw,"cameraPos").access=ACC_PUBLIC|ACC_STATIC;
  if(modern){int normals=0;for(AbstractInsnNode n:line.instructions.toArray())if(n instanceof MethodInsnNode m&&m.name.equals("method_22914")){
   for(int k=0;k<3;k++){AbstractInsnNode previous=n.getPrevious();if(previous.getOpcode()!=FCONST_0&&previous.getOpcode()!=FCONST_1)throw new AssertionError("unexpected normal input");line.instructions.remove(previous);}
   InsnList direction=new InsnList();direction.add(new VarInsnNode(ALOAD,16));direction.add(new MethodInsnNode(INVOKEVIRTUAL,"net/minecraft/class_4587","method_23760","()Lnet/minecraft/class_4587$class_4665;",false));
   for(int k=0;k<3;k++){direction.add(new VarInsnNode(DLOAD,7+k*2));direction.add(new VarInsnNode(DLOAD,1+k*2));direction.add(new InsnNode(DSUB));direction.add(new InsnNode(D2F));}
   line.instructions.insertBefore(n,direction);line.instructions.set(n,new MethodInsnNode(INVOKEINTERFACE,"net/minecraft/class_4588","method_60831","(Lnet/minecraft/class_4587$class_4665;FFF)Lnet/minecraft/class_4588;",true));normals++;
  }if(normals!=2)throw new AssertionError("line directions "+normals);}
  save(raw,out);
  ClassNode overlay=new ClassNode();new ClassReader(Files.readAllBytes(common.resolve(OVER+".class"))).accept(overlay,0);
  MethodNode camera=method(overlay,"camera");clear(camera);InsnList i=camera.instructions;i.add(new VarInsnNode(ALOAD,0));i.add(new TypeInsnNode(CHECKCAST,context));
  if(modern)i.add(new MethodInsnNode(INVOKESTATIC,RAW,"cameraPos","(L"+context+";)Lnet/minecraft/class_243;",false));
  else {i.add(new MethodInsnNode(INVOKEINTERFACE,context,"camera","()Lnet/minecraft/class_4184;",true));i.add(new MethodInsnNode(INVOKEVIRTUAL,"net/minecraft/class_4184","method_19326","()Lnet/minecraft/class_243;",false));}i.add(new InsnNode(ARETURN));
  MethodNode bridge=method(overlay,"raw");clear(bridge);i=bridge.instructions;i.add(new VarInsnNode(ALOAD,0));i.add(new TypeInsnNode(CHECKCAST,context));for(int slot:new int[]{1,3,5,7,9,11})i.add(new VarInsnNode(DLOAD,slot));i.add(new VarInsnNode(ILOAD,13));i.add(new VarInsnNode(FLOAD,14));i.add(new MethodInsnNode(INVOKESTATIC,RAW,"drawLine",line.desc,false));i.add(new InsnNode(RETURN));
  bridge=method(overlay,"fallback");clear(bridge);i=bridge.instructions;i.add(new VarInsnNode(ALOAD,0));i.add(new TypeInsnNode(CHECKCAST,context));i.add(new VarInsnNode(ALOAD,1));for(int slot=2;slot<=5;slot++)i.add(new VarInsnNode(FLOAD,slot));i.add(new MethodInsnNode(INVOKESTATIC,G,"drawBox",method(geom,"drawBox").desc,false));i.add(new InsnNode(RETURN));save(overlay,out);
  Path shadow=out.resolve("com/duckswords/render/BlockShadow247.class");Files.createDirectories(shadow.getParent());Files.copy(common.resolve("com/duckswords/render/BlockShadow247.class"),shadow,StandardCopyOption.REPLACE_EXISTING);
  ClassNode helper=read(z,"com/duckswords/render/TargetTop242");int routes=0;
  for(MethodNode m:helper.methods){boolean first=true;for(AbstractInsnNode n:m.instructions)if(n instanceof MethodInsnNode call&&call.owner.equals(G)&&call.name.equals("drawBox")){
   if(m.name.equals("drawFilledBox")||m.name.equals("drawBox")&&first){call.owner=OVER;call.desc=call.desc.replace("L"+context+";","Ljava/lang/Object;");routes++;}first=false;
  }}if(routes!=2)throw new AssertionError("overlay routes "+routes);save(helper,out);
  ClassNode module=read(z,"com/duckswords/modules/TargetHighlight");int descriptions=0;for(MethodNode m:module.methods)for(AbstractInsnNode n:m.instructions)if(n instanceof LdcInsnNode l&&"Realca o contorno da hitbox respeitando a profundidade dos blocos".equals(l.cst)){l.cst="Mostra as linhas sobre o jogador, ocultando trechos atras dos blocos";descriptions++;}if(descriptions!=1)throw new AssertionError("description");save(module,out);
 }System.out.println("PASS RenderTop model overlay with exact block-shape line clipping: "+args[2]);}
}
