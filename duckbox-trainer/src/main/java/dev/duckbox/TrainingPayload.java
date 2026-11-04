package dev.duckbox;

import java.util.UUID;
import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.packet.CustomPayload;
import net.minecraft.util.Identifier;
import net.minecraft.util.Uuids;

public record TrainingPayload(UUID owner, UUID bot, boolean enabled) implements CustomPayload {
  public static final CustomPayload.Id<TrainingPayload> ID =
      new CustomPayload.Id<>(Identifier.of("duckbox", "training"));
  public static final PacketCodec<RegistryByteBuf, TrainingPayload> CODEC =
      PacketCodec.tuple(
          Uuids.PACKET_CODEC,
          TrainingPayload::owner,
          Uuids.PACKET_CODEC,
          TrainingPayload::bot,
          net.minecraft.network.codec.PacketCodecs.BOOLEAN,
          TrainingPayload::enabled,
          TrainingPayload::new);

  @Override
  public CustomPayload.Id<? extends CustomPayload> getId() {
    return ID;
  }
}
