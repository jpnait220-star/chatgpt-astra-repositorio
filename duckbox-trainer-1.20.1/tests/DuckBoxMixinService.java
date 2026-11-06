import java.io.*;
import java.net.*;
import java.util.*;
import org.objectweb.asm.*;
import org.objectweb.asm.tree.*;
import org.spongepowered.asm.launch.platform.container.*;
import org.spongepowered.asm.mixin.MixinEnvironment;
import org.spongepowered.asm.service.*;

/**
 * Isolated test service: supplies real remapped Minecraft/mod bytecode to the unmodified Mixin
 * transformer.
 */
public class DuckBoxMixinService extends MixinServiceAbstract
    implements IClassProvider, IClassBytecodeProvider, IGlobalPropertyService {
  public static java.lang.reflect.Method reader;
  private final Map<IPropertyKey, Object> properties = new HashMap<>();
  private final Map<String, IPropertyKey> keys = new HashMap<>();

  public String getName() {
    return "Duck startup regression";
  }

  public boolean isValid() {
    return true;
  }

  public MixinEnvironment.Phase getInitialPhase() {
    return MixinEnvironment.Phase.DEFAULT;
  }

  public IClassProvider getClassProvider() {
    return this;
  }

  public IClassBytecodeProvider getBytecodeProvider() {
    return this;
  }

  public ITransformerProvider getTransformerProvider() {
    return null;
  }

  public IClassTracker getClassTracker() {
    return null;
  }

  public IMixinAuditTrail getAuditTrail() {
    return null;
  }

  public Collection<String> getPlatformAgents() {
    return List.of();
  }

  public IContainerHandle getPrimaryContainer() {
    return new ContainerHandleVirtual("duck-test");
  }

  public InputStream getResourceAsStream(String name) {
    return getClass().getClassLoader().getResourceAsStream(name);
  }

  public URL[] getClassPath() {
    return new URL[0];
  }

  public Class<?> findClass(String n) throws ClassNotFoundException {
    return Class.forName(n, false, getClass().getClassLoader());
  }

  public Class<?> findClass(String n, boolean init) throws ClassNotFoundException {
    return Class.forName(n, init, getClass().getClassLoader());
  }

  public Class<?> findAgentClass(String n, boolean init) throws ClassNotFoundException {
    return findClass(n, init);
  }

  public ClassNode getClassNode(String name) throws IOException, ClassNotFoundException {
    return getClassNode(name, false);
  }

  public ClassNode getClassNode(String name, boolean transform)
      throws IOException, ClassNotFoundException {
    return getClassNode(name, transform, 0);
  }

  public ClassNode getClassNode(String name, boolean transform, int flags)
      throws IOException, ClassNotFoundException {
    name = name.replace('.', '/');
    try {
      ClassNode c = (ClassNode) reader.invoke(null, name);
      if (c != null) {
        ClassNode copy = new ClassNode();
        c.accept(copy);
        return copy;
      }
    } catch (Exception e) {
      throw new IOException(name, e);
    }
    try (InputStream stream = getResourceAsStream(name + ".class")) {
      if (stream == null) throw new ClassNotFoundException(name);
      ClassNode c = new ClassNode();
      new ClassReader(stream).accept(c, flags);
      return c;
    }
  }

  public IPropertyKey resolveKey(String name) {
    return keys.computeIfAbsent(name, n -> new IPropertyKey() {});
  }

  @SuppressWarnings("unchecked")
  public <T> T getProperty(IPropertyKey key) {
    return (T) properties.get(key);
  }

  public void setProperty(IPropertyKey key, Object value) {
    properties.put(key, value);
  }

  public <T> T getProperty(IPropertyKey key, T fallback) {
    T value = getProperty(key);
    return value == null ? fallback : value;
  }

  public String getPropertyString(IPropertyKey key, String fallback) {
    Object value = properties.get(key);
    return value == null ? fallback : value.toString();
  }
}
