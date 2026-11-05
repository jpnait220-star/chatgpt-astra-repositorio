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
              "net/minecraft/class_1007", "net/minecraft/class_640", "net/minecraft/class_310"
            }
            : new String[] {
              "net/minecraft/class_1297",
              "net/minecraft/class_1671",
              "net/minecraft/class_3222",
              "net/minecraft/class_3244"
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
