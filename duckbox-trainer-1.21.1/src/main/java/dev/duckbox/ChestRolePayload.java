package dev.duckbox;

import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.*;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.BlockPos;

public record ChestRolePayload(Identifier dimension, BlockPos pos, int role)
    implements CustomPayload {
  public static final Id<ChestRolePayload> ID = new Id<>(Identifier.of("duckbox", "chest_role"));
  public static final PacketCodec<RegistryByteBuf, ChestRolePayload> CODEC =
      PacketCodec.tuple(
          Identifier.PACKET_CODEC,
          ChestRolePayload::dimension,
          BlockPos.PACKET_CODEC,
          ChestRolePayload::pos,
          PacketCodecs.VAR_INT,
          ChestRolePayload::role,
          ChestRolePayload::new);

  public Id<? extends CustomPayload> getId() {
    return ID;
  }
}
