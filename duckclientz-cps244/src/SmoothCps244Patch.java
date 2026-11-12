import java.nio.file.*;import java.util.*;import java.util.zip.*;import org.objectweb.asm.*;import org.objectweb.asm.tree.*;
public final class SmoothCps244Patch implements Opcodes{
 static final String CPS="com/duckswords/modules/CpsDisplay",SMOOTH="com/duckswords/input/SmoothCps244";
 public static void main(String[] a)throws Exception{Path out=Path.of(a[1]);try(ZipFile z=new ZipFile(a[0])){
  ClassNode c=new ClassNode();new ClassReader(z.getInputStream(z.getEntry(CPS+".class"))).accept(c,0);int left=0,right=0,middle=0;
  for(MethodNode m:c.methods)for(AbstractInsnNode n:m.instructions.toArray())if(n instanceof MethodInsnNode call){int slot=-1;
   if(m.name.equals("onHudRender")&&call.owner.equals(CPS)&&call.name.equals("count")&&call.desc.equals("(Ljava/util/Deque;)I")){
    AbstractInsnNode p=n.getPrevious();while(p!=null&&p.getOpcode()<0)p=p.getPrevious();
    if(p instanceof FieldInsnNode f&&f.owner.equals(CPS)){if(f.name.equals("LEFT")){slot=0;left++;}if(f.name.equals("RIGHT")){slot=1;right++;}}
   }
   if(m.name.equals("formatMiddle230")&&call.owner.equals(CPS)&&call.name.equals("currentAdaptiveMiddle243")){slot=2;middle++;}
   if(slot>=0){InsnList ins=new InsnList();ins.add(new InsnNode(ICONST_0+slot));ins.add(new MethodInsnNode(INVOKESTATIC,SMOOTH,"display","(II)I",false));m.instructions.insert(n,ins);}
  }
  if(left!=1||right!=1||middle!=1)throw new IllegalStateException("Unexpected HUD counter sites "+left+"/"+right+"/"+middle);
  ClassWriter w=new ClassWriter(ClassWriter.COMPUTE_MAXS);c.accept(w);Path dest=out.resolve(CPS+".class");Files.createDirectories(dest.getParent());Files.write(dest,w.toByteArray());
  dest=out.resolve(SMOOTH+".class");Files.createDirectories(dest.getParent());Files.copy(Path.of(a[3]).resolve(SMOOTH+".class"),dest,StandardCopyOption.REPLACE_EXISTING);
 }System.out.println("HUD-only falling CPS animation: left/right/adaptive middle hooked: "+a[2]);}
}
