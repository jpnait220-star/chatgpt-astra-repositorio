package dev.duckbox.chests;

import net.minecraft.block.BlockState;
import net.minecraft.block.entity.ChestBlockEntity;
import net.minecraft.util.math.BlockPos;

public final class DuckChestEntity extends ChestBlockEntity {
  public int profileRole = -1;
  @Override public void readNbt(net.minecraft.nbt.NbtCompound n){super.readNbt(n);profileRole=n.contains("duckbox_visual_role")?n.getInt("duckbox_visual_role"):-1;}
  @Override protected void writeNbt(net.minecraft.nbt.NbtCompound n){super.writeNbt(n);if(profileRole>=0)n.putInt("duckbox_visual_role",profileRole);}
  @Override public net.minecraft.nbt.NbtCompound toInitialChunkDataNbt(){var n=super.toInitialChunkDataNbt();if(profileRole>=0)n.putInt("duckbox_visual_role",profileRole);return n;}
  @Override public net.minecraft.network.packet.s2c.play.BlockEntityUpdateS2CPacket toUpdatePacket(){return net.minecraft.network.packet.s2c.play.BlockEntityUpdateS2CPacket.create(this);}
  public DuckChestEntity(BlockPos pos, BlockState state) {
    super(MapChests.TYPE, pos, state);
  }
}
