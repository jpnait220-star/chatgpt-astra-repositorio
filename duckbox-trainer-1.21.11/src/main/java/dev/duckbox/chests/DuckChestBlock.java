package dev.duckbox.chests;

import com.mojang.serialization.MapCodec;
import net.minecraft.block.*;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.block.enums.ChestType;
import net.minecraft.item.ItemPlacementContext;
import net.minecraft.util.math.BlockPos;

public final class DuckChestBlock extends ChestBlock {
  public final int baseRole;

  public DuckChestBlock(int role, Settings settings) {
    super(() -> MapChests.TYPE, net.minecraft.sound.SoundEvents.BLOCK_CHEST_OPEN, net.minecraft.sound.SoundEvents.BLOCK_CHEST_CLOSE, settings);
    baseRole = role;
  }

  public MapCodec<? extends ChestBlock> getCodec() {
    return createCodec(s -> new DuckChestBlock(baseRole, s));
  }

  public BlockState getPlacementState(ItemPlacementContext context) {
    return super.getPlacementState(context).with(CHEST_TYPE, ChestType.SINGLE);
  }

  public BlockEntity createBlockEntity(BlockPos pos, BlockState state) {
    return new DuckChestEntity(pos, state);
  }
}
