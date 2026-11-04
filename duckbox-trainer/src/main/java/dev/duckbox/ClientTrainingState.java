package dev.duckbox;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.entity.*;

/** Synced permission only; the client never controls the bot's AI or inventory. */
public final class ClientTrainingState {
  private static volatile TrainingPayload state;
  private static final Map<UUID, Long> rockets = new ConcurrentHashMap<>();

  public static void set(TrainingPayload p) {
    state = p;
    rockets.clear();
  }

  public static void clear() {
    state = null;
    rockets.clear();
  }

  private static boolean participant(Entity e) {
    TrainingPayload p = state;
    return p != null
        && p.enabled()
        && (p.owner().equals(e.getUuid()) || p.bot().equals(e.getUuid()));
  }

  public static void boost(LivingEntity e) {
    if (participant(e)) rockets.put(e.getUuid(), e.getWorld().getTime() + 3);
  }

  public static boolean ignore(Entity e) {
    return participant(e)
        && e instanceof LivingEntity l
        && l.isGliding()
        && rockets.getOrDefault(e.getUuid(), -1L) >= e.getWorld().getTime();
  }
}
