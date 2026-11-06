package dev.duckbox.panels;

import com.mojang.serialization.MapCodec;
import net.minecraft.block.*;
import net.minecraft.block.entity.BlockEntity;
import net.minecraft.item.ItemPlacementContext;
import net.minecraft.state.StateManager;
import net.minecraft.state.property.*;
import net.minecraft.util.*;
import net.minecraft.util.math.*;

public final class MapPanelBlock extends BlockWithEntity {
  public static final EnumProperty<Direction> FACING = Properties.HORIZONTAL_FACING;
  public final String texture;
  public final net.minecraft.util.Identifier textureId;

  public MapPanelBlock(String texture, Settings settings) {
    super(settings);
    this.texture = texture;
    this.textureId =
        new net.minecraft.util.Identifier("duckbox", "textures/map_panels/" + texture + ".png");
    setDefaultState(getDefaultState().with(FACING, Direction.NORTH));
  }


  protected void appendProperties(StateManager.Builder<Block, BlockState> b) {
    b.add(FACING);
  }

  public BlockState getPlacementState(ItemPlacementContext context) {
    return getDefaultState().with(FACING, context.getHorizontalPlayerFacing().getOpposite());
  }

  public BlockRenderType getRenderType(BlockState state) {
    return BlockRenderType.MODEL;
  }

  public BlockState rotate(BlockState state, BlockRotation rotation) {
    return state.with(FACING, rotation.rotate(state.get(FACING)));
  }

  public BlockState mirror(BlockState state, BlockMirror mirror) {
    return state.rotate(mirror.getRotation(state.get(FACING)));
  }

  public BlockEntity createBlockEntity(BlockPos pos, BlockState state) {
    return new MapPanelEntity(pos, state);
  }
}
