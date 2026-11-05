import java.nio.file.*;
import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;

public class PatchMouse {
  public static void main(String[] args) throws Exception {
    var node = new ClassNode();
    new ClassReader(Files.readAllBytes(Path.of(args[0]))).accept(node, 0);
    int changed = 0;
    for (var method : node.methods)
      if (method.name.startsWith("duck$") && method.desc.endsWith("V")) {
        var pass = new LabelNode();
        var code = new InsnList();
        code.add(
            new MethodInsnNode(
                Opcodes.INVOKESTATIC,
                "com/duckunified/duckbox/HitDelayScope",
                "allow",
                "()Z",
                false));
        code.add(new JumpInsnNode(Opcodes.IFNE, pass));
        code.add(new InsnNode(Opcodes.RETURN));
        code.add(pass);
        code.add(new FrameNode(Opcodes.F_SAME, 0, null, 0, null));
        method.instructions.insert(code);
        changed++;
      }
    if (changed != 3)
      throw new AssertionError("Expected three local hit-delay callbacks, got " + changed);
    var writer = new ClassWriter(ClassWriter.COMPUTE_MAXS);
    node.accept(writer);
    Files.write(Path.of(args[1]), writer.toByteArray());
  }
}
