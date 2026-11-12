import java.nio.file.*;import java.util.*;import java.util.zip.*;import org.objectweb.asm.*;import org.objectweb.asm.tree.*;
public final class Revision245Patch implements Opcodes{
 static final String G="com/duckswords/render/TargetTopGeometry242",H="com/duckswords/render/TargetTop242";
 static ClassNode read(ZipFile z,String n)throws Exception{ClassNode c=new ClassNode();new ClassReader(z.getInputStream(z.getEntry(n+".class"))).accept(c,0);return c;}
 static void save(ClassNode c,Path out)throws Exception{ClassWriter w=new ClassWriter(ClassWriter.COMPUTE_MAXS);c.accept(w);Path p=out.resolve(c.name+".class");Files.createDirectories(p.getParent());Files.write(p,w.toByteArray());}
 public static void main(String[] a)throws Exception{Path out=Path.of(a[1]);try(ZipFile z=new ZipFile(a[0])){
  ClassNode c=read(z,G);int special=0,identity=0;
  for(MethodNode m:c.methods)for(AbstractInsnNode n:m.instructions.toArray())if(n instanceof MethodInsnNode call&&call.owner.equals("com/duckswords/render/WebLineLayers")){
   if(call.name.equals("special")){AbstractInsnNode previous=n.getPrevious();while(previous!=null&&previous.getOpcode()<0)previous=previous.getPrevious();if(previous==null||previous.getOpcode()!=POP)throw new IllegalStateException("Missing discarded native layer");m.instructions.remove(previous);m.instructions.remove(n);special++;}
   else if(call.name.equals("layer")){m.instructions.remove(n);identity++;}else throw new IllegalStateException("Unexpected material hook "+call.name);
  }
  if(special!=1||identity<1)throw new IllegalStateException("Occlusion hook mismatch "+special+"/"+identity);save(c,out);
  c=read(z,H);int routed=0;for(MethodNode m:c.methods)for(AbstractInsnNode n:m.instructions)if(n instanceof MethodInsnNode call&&call.owner.equals("com/duckswords/util/RenderUtil")&&Set.of("drawBox","drawFilledBox").contains(call.name)){call.owner=G;routed++;}
  if(routed!=2)throw new IllegalStateException("Missing normal geometry routing "+routed);save(c,out);
  c=read(z,"com/duckswords/modules/TargetHighlight");int descriptions=0;for(MethodNode m:c.methods)for(AbstractInsnNode n:m.instructions)if(n instanceof LdcInsnNode l&&"Desenha o contorno da hitbox por cima do modelo do jogador".equals(l.cst)){l.cst="Realca o contorno da hitbox respeitando a profundidade dos blocos";descriptions++;}if(descriptions!=1)throw new IllegalStateException("Missing RenderTop description");save(c,out);
  for(String helper:List.of("AdaptiveCps243","SmoothCps244")){Path p=out.resolve("com/duckswords/input/"+helper+".class");Files.createDirectories(p.getParent());Files.copy(Path.of(a[3]).resolve("com/duckswords/input/"+helper+".class"),p,StandardCopyOption.REPLACE_EXISTING);}
 }System.out.println("2.45: slow CPS decay, fast button release, and native depth-tested target geometry: "+a[2]);}
}
