import java.util.*;
import net.minecraft.block.Block;
import net.minecraft.registry.*;

/** Reproduce Fabric's pre-freeze registration phase on the plain native test classpath. */
public final class NativeModBootstrap {
  public static void prepare() throws Exception {
    for (var registry : List.of(Registries.BLOCK, Registries.ITEM, Registries.BLOCK_ENTITY_TYPE)) {
      var frozen = SimpleRegistry.class.getDeclaredField("field_36463");
      frozen.setAccessible(true);
      frozen.setBoolean(registry, false);
      var intrusive = SimpleRegistry.class.getDeclaredField("field_40584");
      intrusive.setAccessible(true);
      intrusive.set(registry, new IdentityHashMap<>());
      var tags = SimpleRegistry.class.getDeclaredField("field_53687");
      tags.setAccessible(true);
      var emptyFactory =
          java.util.Arrays.stream(tags.getType().getDeclaredMethods())
              .filter(
                  m ->
                      java.lang.reflect.Modifier.isStatic(m.getModifiers())
                          && m.getParameterCount() == 0
                          && m.getReturnType() == tags.getType())
              .findFirst()
              .orElseThrow();
      emptyFactory.setAccessible(true);
      tags.set(registry, emptyFactory.invoke(null));
    }
    dev.duckbox.panels.MapPanels.init();
    var blocks = new ArrayList<Block>(dev.duckbox.panels.MapPanels.BLOCKS.values());
    blocks.add(dev.duckbox.chests.MapChests.STOCK);
    blocks.add(dev.duckbox.chests.MapChests.PROFILE);
    for (var block : blocks)
      for (var state : block.getStateManager().getStates()) {
        if (Block.STATE_IDS.getRawId(state) < 0) Block.STATE_IDS.add(state);
        state.initShapeCache();
      }
    Registries.BLOCK.freeze();
    Registries.ITEM.freeze();
    Registries.BLOCK_ENTITY_TYPE.freeze();
  }
}
