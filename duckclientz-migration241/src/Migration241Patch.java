import org.objectweb.asm.*;import org.objectweb.asm.tree.*;
import java.nio.file.*;import java.util.*;import java.util.zip.*;
public final class Migration241Patch implements Opcodes {
 static final String OLD="https://duck-connect.vercel.app/updates";
 static final String MANIFEST="https://raw.githubusercontent.com/jpnait220-star/chatgpt-astra-repositorio/asasa/downloads/DuckClientZ-update.json";
 public static void main(String[] args)throws Exception{
  try(ZipFile jar=new ZipFile(args[0])){
   for(String name:List.of("com/duckswords/social/CosmeticSharing","com/duckswords/update/ClientUpdater229","com/duckswords/modules/CosmeticsOnline")){
    ClassNode c=new ClassNode();new ClassReader(jar.getInputStream(jar.getEntry(name+".class")).readAllBytes()).accept(c,0);int changes=0;
    if(name.endsWith("ClientUpdater229"))for(FieldNode f:c.fields)if(OLD.equals(f.value)){f.value=MANIFEST;changes++;}
    for(MethodNode m:c.methods){
     if(name.endsWith("CosmeticSharing")&&m.name.equals("request")&&m.desc.equals("(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;")){
      InsnList hook=new InsnList();hook.add(new VarInsnNode(ALOAD,0));hook.add(new MethodInsnNode(INVOKESTATIC,"com/duckswords/connect/ServiceRoute241","translate","(Ljava/lang/String;)Ljava/lang/String;",false));hook.add(new VarInsnNode(ASTORE,0));m.instructions.insert(hook);changes++;
     }
     for(AbstractInsnNode n:m.instructions){
      if(n instanceof LdcInsnNode ldc){
       if(name.endsWith("ClientUpdater229")&&OLD.equals(ldc.cst)){ldc.cst=MANIFEST;changes++;}
       if(name.endsWith("CosmeticsOnline")&&m.name.equals("<init>")&&ldc.cst instanceof String s&&s.contains("duck-connect.vercel.app")){
        ldc.cst=s.equals("https://duck-connect.vercel.app")||s.equals("duck-connect.vercel.app")?"Duck Connect automatico":s.replace("Endereco fixo https://duck-connect.vercel.app.","Endereco atualizado automaticamente.");changes++;
       }
      }
     }
    }
    if(changes==0)throw new IllegalStateException("Patch target missing: "+name);
    ClassWriter writer=new ClassWriter(ClassWriter.COMPUTE_MAXS);c.accept(writer);
    Path file=Path.of(args[1],name+".class");Files.createDirectories(file.getParent());Files.write(file,writer.toByteArray());
    System.out.println(name+": "+changes+" migration changes");
   }
  }
 }
}
