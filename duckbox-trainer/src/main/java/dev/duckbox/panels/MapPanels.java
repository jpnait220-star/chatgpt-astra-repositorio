package dev.duckbox.panels;

import java.util.*;
import net.minecraft.block.*;
import net.minecraft.block.entity.*;
import net.minecraft.item.*;
import net.minecraft.registry.*;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.Identifier;

public final class MapPanels {
  public static final List<String> NAMES =
      List.of(
          "kit_1",
          "kit_2",
          "kit_3",
          "kit_4",
          "cps",
          "gap",
          "giro_elytra_foguete",
          "giro_seta_elytra",
          "nao_correr_retotem",
          "regras",
          "resistencia",
          "retotem",
          "start_1_top_left",
          "start_2_top_center",
          "start_3_top_right",
          "start_4_bottom_left",
          "start_5_bottom_center",
          "start_6_bottom_right",
          "start_sheet");
  public static final Map<String, MapPanelBlock> BLOCKS = new LinkedHashMap<>();
  public static BlockEntityType<MapPanelEntity> TYPE;

  public static void init() {
    if (TYPE != null) return;
    dev.duckbox.chests.MapChests.init();
    for (String name : NAMES) {
      var id = Identifier.of("duckbox", "painel_" + name);
      var key = RegistryKey.of(RegistryKeys.BLOCK, id);
      var block =
          new MapPanelBlock(name, AbstractBlock.Settings.create().registryKey(key).strength(2));
      Registry.register(Registries.BLOCK, id, block);
      BLOCKS.put(name, block);
      var item =
          new BlockItem(
              block,
              new Item.Settings()
                  .registryKey(RegistryKey.of(RegistryKeys.ITEM, id))
                  .useBlockPrefixedTranslationKey());
      Registry.register(Registries.ITEM, id, item);
      item.appendBlocks(Item.BLOCK_ITEMS, item);
    }
    TYPE =
        Registry.register(
            Registries.BLOCK_ENTITY_TYPE, Identifier.of("duckbox", "map_panel"), createType());
  }

  private static BlockEntityType<MapPanelEntity> createType() {
    return dev.duckbox.NativeBlockEntities.create(Set.copyOf(BLOCKS.values()), MapPanelEntity::new);
  }

  public static void give(ServerPlayerEntity p, String name) {
    var block = BLOCKS.get(name);
    if (block == null)
      throw new IllegalArgumentException(
          "Bloco desconhecido. Use /box blocos ou a lista sugerida.");
    p.getInventory().offerOrDrop(new ItemStack(block));
  }
}
