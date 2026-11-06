package dev.duckbox;

import java.util.*;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.block.entity.ChestBlockEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.BlockPos;

public final class ChestRoleSync {
  private static final Map<Identifier, Set<BlockPos>> known = new HashMap<>();
  private static final Map<UUID, Map<String, Integer>> sent = new HashMap<>();
  private static final Map<String, Integer> client = new HashMap<>();
  private static final Map<UUID, String> discovery = new HashMap<>();

  private static String key(Identifier dimension, BlockPos pos) {
    return dimension + "/" + pos.asLong();
  }

  public static void remember(ServerWorld world, ChestBlockEntity chest) {
    if (TrainerChests.profile(chest) >= 0)
      known
          .computeIfAbsent(world.getRegistryKey().getValue(), k -> new HashSet<>())
          .add(chest.getPos().toImmutable());
  }

  public static void receive(ChestRolePayload payload) {
    String key = key(payload.dimension(), payload.pos());
    if (payload.role() < 0) client.remove(key);
    else if (payload.role() <= 4) client.put(key, payload.role());
  }

  public static int clientRole(ChestBlockEntity chest) {
    if (chest.getWorld() == null || !chest.getWorld().isClient()) return -1;
    return client.getOrDefault(
        key(chest.getWorld().getRegistryKey().getValue(), chest.getPos()), -1);
  }

  public static void forget(UUID id) {
    sent.remove(id);
    discovery.remove(id);
  }

  public static void clearClient() {
    client.clear();
  }

  public static void clear() {
    known.clear();
    sent.clear();
    discovery.clear();
  }

  public static void tick(MinecraftServer server) {
    if (server.getTicks() % 10 != 0) return;
    for (var p : server.getPlayerManager().getPlayerList()) {
      if (p instanceof TrainingBot
          || !DuckBox.canSendTraining(p)
          || !ServerPlayNetworking.canSend(p, ChestRolePayload.ID)) continue;
      var world = p.getServerWorld();
      var dimension = world.getRegistryKey().getValue();
      String location = dimension + "/" + p.getChunkPos().toLong();
      if (!location.equals(discovery.get(p.getUuid())) || server.getTicks() % 200 == 0) {
        int cx = p.getChunkPos().x, cz = p.getChunkPos().z;
        int radius = Math.min(8, server.getPlayerManager().getViewDistance());
        for (int x = cx - radius; x <= cx + radius; x++)
          for (int z = cz - radius; z <= cz + radius; z++) {
            var loaded = world.getChunkManager().getWorldChunk(x, z);
            if (loaded != null)
              for (var blockEntity : loaded.getBlockEntities().values())
                if (blockEntity instanceof ChestBlockEntity chest) remember(world, chest);
          }
        discovery.put(p.getUuid(), location);
      }
      var memo = sent.computeIfAbsent(p.getUuid(), k -> new HashMap<>());
      for (var pos : new java.util.ArrayList<>(known.getOrDefault(dimension, Set.of()))) {
        if (p.squaredDistanceTo(net.minecraft.util.math.Vec3d.ofCenter(pos)) > 65536) continue;
        var chunk = world.getChunkManager().getWorldChunk(pos.getX() >> 4, pos.getZ() >> 4);
        if (chunk == null) continue;
        int role = -1;
        if (chunk.getBlockEntity(pos) instanceof ChestBlockEntity chest) {
          var upgraded = dev.duckbox.chests.MapChests.upgrade(world, chest);
          role = TrainerChests.profile(upgraded);
        }
        String key = key(dimension, pos);
        if (!Objects.equals(memo.get(key), role)) {
          ServerPlayNetworking.send(p, new ChestRolePayload(dimension, pos, role));
          memo.put(key, role);
        }
      }
    }
  }
}
