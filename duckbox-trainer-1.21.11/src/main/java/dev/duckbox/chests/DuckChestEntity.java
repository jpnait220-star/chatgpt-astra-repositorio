package dev.duckbox.chests;

import net.minecraft.block.BlockState;
import net.minecraft.block.entity.ChestBlockEntity;
import net.minecraft.util.math.BlockPos;

public final class DuckChestEntity extends ChestBlockEntity {
  @Override protected void readData(net.minecraft.storage.ReadView view){
    super.readData(dev.duckbox.LegacyStockMigration.inventoryView(view));
  }
  public DuckChestEntity(BlockPos pos, BlockState state) {
    super(MapChests.TYPE, pos, state);
  }
}
