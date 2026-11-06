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
      if(registry!=Registries.BLOCK_ENTITY_TYPE)intrusive.set(registry, new IdentityHashMap<>());

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
