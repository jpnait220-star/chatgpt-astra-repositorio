package dev.duckbox;

import java.util.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;

public final class SpawnControl {
  private record Return(int due, ServerWorld world) {}

  private static final Map<UUID, Return> pending = new HashMap<>();

  public static void later(ServerPlayerEntity p) {
    pending.put(p.getUuid(), new Return(p.getEntityWorld().getServer().getTicks() + 60, p.getEntityWorld()));
  }

  public static void move(ServerPlayerEntity p, ServerWorld world) {
    pending.remove(p.getUuid());
    p.stopUsingItem();
    p.stopGliding();
    p.setVelocity(net.minecraft.util.math.Vec3d.ZERO);
    var o = DuckBox.options;
    if (!o.spawnDimension.isEmpty()) {
      var id = net.minecraft.util.Identifier.tryParse(o.spawnDimension);
      if (id != null) {
        var configured =
            p.getEntityWorld().getServer()
                .getWorld(
                    net.minecraft.registry.RegistryKey.of(
                        net.minecraft.registry.RegistryKeys.WORLD, id));
        if (configured != null) world = configured;
      }
    }
    p.teleport(world, o.spawnX, o.spawnY, o.spawnZ, Set.of(), o.spawnYaw, o.spawnPitch, false);
    DuckBox.applyLobbyMode(p);
  }

  public static void set(ServerPlayerEntity p) {
    var o = DuckBox.options;
    o.spawnX = p.getX();
    o.spawnY = p.getY();
    o.spawnZ = p.getZ();
    o.spawnYaw = p.getYaw();
    o.spawnPitch = p.getPitch();
    o.spawnDimension = p.getEntityWorld().getRegistryKey().getValue().toString();
    DuckBox.save();
    DuckBox.setting(p, "Spawn definido nesta posicao.");
  }

  public static void command(ServerPlayerEntity p) {
    if (DuckBox.session != null && DuckBox.session.owner == p) DuckBox.stop("Treino encerrado.");
    else move(p, DuckBox.world() == null ? p.getEntityWorld() : DuckBox.world());
  }

  public static void tick(MinecraftServer server) {
    var ready = new ArrayList<UUID>();
    pending.forEach(
        (id, job) -> {
          if (server.getTicks() >= job.due()) ready.add(id);
        });
    for (var id : ready) {
      var job = pending.remove(id);
      var p = server.getPlayerManager().getPlayer(id);
      if (p != null
          && !p.isDisconnected()
          && p.getEntityWorld() == job.world()
          && (DuckBox.session == null || DuckBox.session.owner != p)) move(p, job.world());
    }
  }

  public static void clear() {
    pending.clear();
  }
}
