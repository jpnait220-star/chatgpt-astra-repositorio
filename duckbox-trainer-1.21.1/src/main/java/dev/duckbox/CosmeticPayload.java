package dev.duckbox;

import java.util.UUID;
import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.*;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.*;

public record CosmeticPayload(UUID owner, UUID bot, int mask) implements CustomPayload {
  public static final Id<CosmeticPayload> ID = new Id<>(Identifier.of("duckbox", "cosmetics"));
  public static final PacketCodec<RegistryByteBuf, CosmeticPayload> CODEC =
      PacketCodec.tuple(
          Uuids.PACKET_CODEC,
          CosmeticPayload::owner,
          Uuids.PACKET_CODEC,
          CosmeticPayload::bot,
          PacketCodecs.VAR_INT,
          CosmeticPayload::mask,
          CosmeticPayload::new);

  public Id<? extends CustomPayload> getId() {
    return ID;
  }
}
