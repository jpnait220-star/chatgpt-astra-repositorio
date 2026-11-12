import java.nio.file.*;import java.util.*;import java.util.zip.*;import org.objectweb.asm.*;import org.objectweb.asm.tree.*;import org.objectweb.asm.util.*;
public final class ExtractTarget247 implements Opcodes {
 static ClassNode read(ZipFile z,String n)throws Exception{ClassNode c=new ClassNode();new ClassReader(z.getInputStream(z.getEntry(n+".class"))).accept(c,0);return c;}
 static void save(ClassNode c,Path out)throws Exception{ClassWriter w=new ClassWriter(ClassWriter.COMPUTE_MAXS);c.accept(w);Path p=out.resolve(c.name+".class");Files.createDirectories(p.getParent());Files.write(p,w.toByteArray());}
 public static void main(String[] args)throws Exception{Path out=Path.of(args[1]);try(ZipFile z=new ZipFile(args[0])){
  String overlay="com/duckswords/render/TargetOverlay247",geometry="com/duckswords/render/TargetTopGeometry242";
  for(String name:List.of(overlay,geometry,"com/duckswords/render/TargetRawLine247","com/duckswords/render/BlockShadow247","com/duckswords/render/TargetTop242"))new ClassReader(z.getInputStream(z.getEntry(name+".class"))).accept(new CheckClassAdapter(new ClassWriter(0),false),0);
  ClassNode raw=read(z,"com/duckswords/render/TargetRawLine247");MethodNode line=raw.methods.stream().filter(m->m.name.equals("drawLine")).findFirst().orElseThrow();int depth=0;for(AbstractInsnNode n:line.instructions)if(n instanceof MethodInsnNode m&&m.owner.equals("com/duckswords/render/WebLineLayers")&&m.name.equals("special"))depth++;if(depth!=1)throw new AssertionError("overlay no-depth line missing");
  if(args[0].contains("1.21.11")){int normals=0;for(AbstractInsnNode n:line.instructions)if(n instanceof MethodInsnNode m&&m.name.equals("method_60831"))normals++;if(normals!=2)throw new AssertionError("per-edge directions missing");}
  if(raw.methods.stream().anyMatch(m->m.name.equals("cameraPos"))){raw.methods.removeIf(m->!m.name.equals("cameraPos"));save(raw,out);}
  ClassNode normal=read(z,geometry);for(MethodNode m:normal.methods)for(AbstractInsnNode n:m.instructions)if(n instanceof MethodInsnNode call&&call.owner.equals("com/duckswords/render/WebLineLayers"))throw new AssertionError("normal depth bypass");
  save(read(z,"com/duckswords/render/TargetTop242"),out);save(read(z,"com/duckswords/render/BlockShadow247"),out);
  ClassNode c=read(z,overlay);for(MethodNode m:c.methods){
   if(m.name.equals("raw")){m.instructions.clear();m.tryCatchBlocks.clear();m.localVariables=null;InsnList i=m.instructions;for(int n:new int[]{1,3,5,7,9,11})i.add(new VarInsnNode(DLOAD,n));i.add(new VarInsnNode(ILOAD,13));i.add(new VarInsnNode(FLOAD,14));i.add(new MethodInsnNode(INVOKESTATIC,"Capture247","line","(DDDDDDIF)V",false));i.add(new InsnNode(RETURN));}
   if(m.name.equals("fallback")){m.instructions.clear();m.tryCatchBlocks.clear();m.localVariables=null;m.instructions.add(new MethodInsnNode(INVOKESTATIC,"Capture247","fallback","()V",false));m.instructions.add(new InsnNode(RETURN));}
  }save(c,out);
 }System.out.println("PASS final class structure, overlay native material and normal depth separation: "+args[0]);}
}
