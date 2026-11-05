package dev.duckbox.chests;

import dev.duckbox.*;
import java.util.*;
import net.minecraft.block.*;
import net.minecraft.block.entity.*;
import net.minecraft.block.enums.ChestType;
import net.minecraft.item.*;
import net.minecraft.registry.*;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.Identifier;

public final class MapChests {
  public static DuckChestBlock STOCK, PROFILE;
  public static BlockEntityType<DuckChestEntity> TYPE;

  public static void init() {
    if (TYPE != null) return;
    STOCK = block("cofre", 0);
    PROFILE = block("bau_profile", 1);
    TYPE =
        Registry.register(
            Registries.BLOCK_ENTITY_TYPE,
            Identifier.of("duckbox", "duck_chest"),
            NativeBlockEntities.create(Set.of(STOCK, PROFILE), DuckChestEntity::new));
  }

  private static DuckChestBlock block(String name, int role) {
    var id = Identifier.of("duckbox", name);
    var block =
        new DuckChestBlock(
            role,
            AbstractBlock.Settings.create()
                .registryKey(RegistryKey.of(RegistryKeys.BLOCK, id))
                .strength(2.5f));
    Registry.register(Registries.BLOCK, id, block);
    var item =
        new BlockItem(
            block,
            new Item.Settings()
                .registryKey(RegistryKey.of(RegistryKeys.ITEM, id))
                .useBlockPrefixedTranslationKey());
    Registry.register(Registries.ITEM, id, item);
    item.appendBlocks(Item.BLOCK_ITEMS, item);
    return block;
  }

  public static ChestBlockEntity upgrade(ServerWorld world, ChestBlockEntity old) {
    if (old instanceof DuckChestEntity) return old;
    int role = TrainerChests.profile(old);
    if (role < 0) return old;
    var pos = old.getPos();
    var saved = old.createNbtWithIdentifyingData(world.getRegistryManager());
    var state = (role == 0 ? STOCK : PROFILE).getDefaultState();
    if (old.getCachedState().contains(ChestBlock.FACING))
      state = state.with(ChestBlock.FACING, old.getCachedState().get(ChestBlock.FACING));
    if (old.getCachedState().contains(ChestBlock.WATERLOGGED))
      state = state.with(ChestBlock.WATERLOGGED, old.getCachedState().get(ChestBlock.WATERLOGGED));
    state = state.with(ChestBlock.CHEST_TYPE, ChestType.SINGLE);
    // Snapshot first and clear only the old inventory to avoid vanilla scattering duplicate stock.
    old.clear();
    world.setBlockState(pos, state, 3);
    if (world.getBlockEntity(pos) instanceof DuckChestEntity upgraded) {
      upgraded.read(saved, world.getRegistryManager());
      upgraded.markDirty();
      world.getChunkManager().markForUpdate(pos);
      return upgraded;
    }
    throw new IllegalStateException("Duck chest migration could not create native block entity");
  }
}
