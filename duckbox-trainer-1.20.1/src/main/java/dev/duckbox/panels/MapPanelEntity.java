package dev.duckbox.panels;

import net.minecraft.block.BlockState;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.util.math.BlockPos;

public final class MapPanelEntity extends BlockEntity {
  public MapPanelEntity(BlockPos pos, BlockState state) {
    super(MapPanels.TYPE, pos, state);
  }
}
