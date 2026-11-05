package dev.duckbox;

import java.util.UUID;
import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.*;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.*;

public record LobbyBotPayload(UUID bot, int mask) implements CustomPayload {
  public static final Id<LobbyBotPayload> ID = new Id<>(Identifier.of("duckbox", "lobby_bot"));
  public static final PacketCodec<RegistryByteBuf, LobbyBotPayload> CODEC =
      PacketCodec.tuple(
          Uuids.PACKET_CODEC,
          LobbyBotPayload::bot,
          PacketCodecs.VAR_INT,
          LobbyBotPayload::mask,
          LobbyBotPayload::new);

  public Id<? extends CustomPayload> getId() {
    return ID;
  }
}
