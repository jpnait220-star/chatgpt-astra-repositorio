package dev.duckbox;

import java.util.*;
import java.util.function.BiFunction;
import net.minecraft.block.*;
import net.minecraft.block.entity.*;
import net.minecraft.util.math.BlockPos;

/** One-time adapter for the private native MC1.21.4 block entity type constructor. */
public final class NativeBlockEntities {
  @SuppressWarnings("unchecked")
  public static <T extends BlockEntity> BlockEntityType<T> create(
      Set<Block> blocks, BiFunction<BlockPos, BlockState, T> factoryFunction) {
    try {
      var constructor =
          Arrays.stream(BlockEntityType.class.getDeclaredConstructors())
              .filter(c -> c.getParameterCount() >= 2 && c.getParameterTypes()[1] == Set.class)
              .findFirst()
              .orElseThrow();
      var factoryType = constructor.getParameterTypes()[0];
      Object factory =
          java.lang.reflect.Proxy.newProxyInstance(
              factoryType.getClassLoader(),
              new Class<?>[] {factoryType},
              (proxy, method, args) -> {
                if (method.getDeclaringClass() == Object.class)
                  return switch (method.getName()) {
                    case "hashCode" -> System.identityHashCode(proxy);
                    case "equals" -> proxy == args[0];
                    default -> "DuckBox native block entity factory";
                  };
                return factoryFunction.apply((BlockPos) args[0], (BlockState) args[1]);
              });
      constructor.setAccessible(true);
      return (BlockEntityType<T>) constructor.newInstance(factory, blocks, null);
    } catch (ReflectiveOperationException error) {
      throw new IllegalStateException(
          "Minecraft1.21.4 block entity constructor unavailable", error);
    }
  }
}
