package dev.duckbox.chests;

import net.minecraft.block.BlockState;
import net.minecraft.block.entity.ChestBlockEntity;
import net.minecraft.util.math.BlockPos;

public final class DuckChestEntity extends ChestBlockEntity {
  public DuckChestEntity(BlockPos pos, BlockState state) {
    super(MapChests.TYPE, pos, state);
  }
}
