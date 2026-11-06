package dev.duckbox;
public final class LegacyNetworking {
 public static void send(net.minecraft.server.network.ServerPlayerEntity p,LegacyPayload data){var buf=net.fabricmc.fabric.api.networking.v1.PacketByteBufs.create();data.write(buf);net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking.send(p,data.id(),buf);}
}
