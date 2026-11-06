import java.lang.reflect.*;
import java.util.*;
import java.util.zip.*;
import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;
import org.spongepowered.asm.launch.MixinBootstrap;
import org.spongepowered.asm.mixin.*;
import org.spongepowered.asm.mixin.transformer.IMixinTransformer;

public class MixinTest {
  static ZipFile game, mod, mouse;

  public static ClassNode read(String name) throws Exception {
    var archives = new java.util.ArrayList<ZipFile>(List.of(game, mod));
    if (mouse != null) archives.add(mouse);
    for (var zip : archives) {
      var entry = zip.getEntry(name + ".class");
      if (entry != null) {
        ClassNode c = new ClassNode();
        new ClassReader(zip.getInputStream(entry).readAllBytes()).accept(c, 0);
        return c;
      }
    }
    return null;
  }

  public static void main(String[] args) throws Exception {
    game = new ZipFile(args[0]);
    mod = new ZipFile(args[1]);
    if (args.length > 3) mouse = new ZipFile(args[3]);
    DuckBoxMixinService.reader = MixinTest.class.getMethod("read", String.class);
    MixinBootstrap.init();
    MixinEnvironment.getDefaultEnvironment()
        .setSide(args.length > 2 ? MixinEnvironment.Side.CLIENT : MixinEnvironment.Side.SERVER);
    Mixins.addConfiguration("duckbox.mixins.json");
    if (mouse != null) Mixins.addConfiguration("internal/duckunified-hitdelay.mixins.json");
    var type = Class.forName("org.spongepowered.asm.mixin.transformer.MixinTransformer");
    var ctor = type.getDeclaredConstructor();
    ctor.setAccessible(true);
    var transformer = (IMixinTransformer) ctor.newInstance();
    for (String target :
        (args.length > 2
            ? new String[] {
              "net/minecraft/class_1007",
              "net/minecraft/class_640",
              "net/minecraft/class_310",
              "net/minecraft/class_10502$class_10503",
              "net/minecraft/class_10517"
            }
            : new String[] {
              "net/minecraft/class_1297",
              "net/minecraft/class_1309",
              "net/minecraft/class_1657",
              "net/minecraft/class_1671",
              "net/minecraft/class_3222",
              "net/minecraft/class_3244",
              "net/minecraft/class_2586",
              "net/minecraft/class_1747"
            })) {
      ClassNode old = read(target);
      ClassWriter w = new ClassWriter(0);
      old.accept(w);
      byte[] result =
          transformer.transformClassBytes(
              target.replace('/', '.'), target.replace('/', '.'), w.toByteArray());
      ClassNode changed = new ClassNode();
      new ClassReader(result).accept(changed, 0);
      if (changed.methods.size() <= old.methods.size())
        throw new AssertionError("missing hook " + target);
      if (target.endsWith("class_1671")
          && changed.methods.stream()
              .noneMatch(
                  m ->
                      m.name.equals("duckbox$getShooter")
                          && (m.access & Opcodes.ACC_ABSTRACT) == 0))
        throw new AssertionError("missing shooter accessor");
      if (target.endsWith("class_1657")) {
        var attack = changed.methods.stream().filter(m -> m.name.equals("method_75197")).findFirst().orElseThrow();
        int nativeSprint = 0, scopedCrit = 0, descent = 0;
        for (var instruction : attack.instructions) if (instruction instanceof MethodInsnNode call) {
          if (call.name.equals("method_5624")) nativeSprint++;
          if (call.name.contains("critSprint")) scopedCrit++;
          if (call.name.contains("critDescent")) descent++;
        }
        if (nativeSprint != 0 || scopedCrit != 1 || descent != 1)
          throw new AssertionError("Sprint critical hook must preserve native knockback and change only critical check");
      }
      if (target.endsWith("class_1657") && System.getProperty("duckbox.woven") != null) {
        try (var archive = new java.util.zip.ZipOutputStream(new java.io.FileOutputStream(System.getProperty("duckbox.woven")))) {
          archive.putNextEntry(new java.util.zip.ZipEntry(target + ".class")); archive.write(result); archive.closeEntry();
        }
      }
      System.out.println(
          "PASS real Mixin APPLY "
              + target
              + ": "
              + old.methods.size()
              + " -> "
              + changed.methods.size()
              + " methods");
    }
  }
}
