package dev.duckbox;

import com.mojang.authlib.GameProfile;
import java.util.*;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.registry.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.*;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.Vec3d;

public final class LobbyBot {
  private static TrainingBot npc;

  public static UUID id() {
    return npc == null ? new UUID(0, 0) : npc.getUuid();
  }

  public static void place(ServerPlayerEntity p) {
    var o = DuckBox.options;
    o.lobbyBotEnabled = true;
    o.lobbyBotX = p.getX();
    o.lobbyBotY = p.getY();
    o.lobbyBotZ = p.getZ();
    o.lobbyBotDimension = p.getServerWorld().getRegistryKey().getValue().toString();
    DuckBox.save();
    if (npc != null && p.getServer().getPlayerManager().getPlayer(npc.getUuid()) == npc) {
      npc.teleport(
          p.getServerWorld(),
          o.lobbyBotX,
          o.lobbyBotY,
          o.lobbyBotZ,
          Set.of(),
          npc.getYaw(),
          npc.getPitch(),
          false);
      npc.onTeleportationDone();
      npc.getInventory().clear();
      DuckBox.syncCosmetics();
    } else {
      npc = null;
      ensure(p.getServer());
    }
    DuckBox.setting(p, "DuckBot do lobby colocado aqui.");
  }

  public static void clear(MinecraftServer server) {
    if (npc != null && server.getPlayerManager().getPlayer(npc.getUuid()) == npc)
      server.getPlayerManager().remove(npc);
    npc = null;
  }

  private static void ensure(MinecraftServer server) {
    if (npc != null || !DuckBox.options.lobbyBotEnabled) return;
    var o = DuckBox.options;
    var dim = Identifier.tryParse(o.lobbyBotDimension);
    if (dim == null) return;
    ServerWorld world = server.getWorld(RegistryKey.of(RegistryKeys.WORLD, dim));
    if (world == null) return;
    var uuid =
        UUID.nameUUIDFromBytes(
            ("DuckBox:Lobby:" + server.getSaveProperties().getLevelName())
                .getBytes(java.nio.charset.StandardCharsets.UTF_8));
    npc = new TrainingBot(server, world, new GameProfile(uuid, "DuckBot"));
    server
        .getPlayerManager()
        .onPlayerConnect(
            new TrainingBot.LocalConnection(),
            npc,
            ConnectedClientData.createDefault(npc.getGameProfile(), false));
    npc.getInventory().clear();
    npc.setInvulnerable(true);
    npc.setNoGravity(true);
    npc.teleport(world, o.lobbyBotX, o.lobbyBotY, o.lobbyBotZ, Set.of(), 0, 0, false);
    npc.onTeleportationDone();
    npc.setLoaded(true);
    DuckBox.syncCosmetics();
  }

  public static void tick(MinecraftServer server) {
    ensure(server);
    if (npc == null) return;
    var o = DuckBox.options;
    npc.setVelocity(Vec3d.ZERO);
    npc.setPosition(o.lobbyBotX, o.lobbyBotY, o.lobbyBotZ);
    npc.forwardSpeed = 0;
    npc.sidewaysSpeed = 0;
    npc.setSprinting(false);
    npc.setSneaking(false);
    ServerPlayerEntity closest = null;
    double best = 256;
    for (var p : server.getPlayerManager().getPlayerList()) {
      if (p instanceof TrainingBot
          || p.isDisconnected()
          || p.getServerWorld() != npc.getServerWorld()) continue;
      double dist = p.squaredDistanceTo(npc);
      if (dist < best) {
        best = dist;
        closest = p;
      }
    }
    if (closest != null) {
      var d = closest.getEyePos().subtract(npc.getEyePos());
      float yaw = (float) Math.toDegrees(Math.atan2(-d.x, d.z));
      float pitch = (float) -Math.toDegrees(Math.atan2(d.y, Math.sqrt(d.x * d.x + d.z * d.z)));
      npc.setYaw(Aim.approach(npc.getYaw(), yaw, 10));
      npc.setPitch(Aim.approach(npc.getPitch(), pitch, 8));
      npc.setHeadYaw(npc.getYaw());
      npc.setBodyYaw(npc.getYaw());
    }
    if (server.getTicks() % 100 == 0) DuckBox.syncCosmetics();
  }

  public static void sync(ServerPlayerEntity p, int mask) {
    if (DuckBox.canSendTraining(p) && ServerPlayNetworking.canSend(p, LobbyBotPayload.ID))
      ServerPlayNetworking.send(p, new LobbyBotPayload(id(), mask));
  }
}
