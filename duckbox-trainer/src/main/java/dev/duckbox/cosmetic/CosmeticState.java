package dev.duckbox.cosmetic;

import dev.duckbox.CosmeticPayload;
import java.util.UUID;

public final class CosmeticState {
  private static volatile CosmeticPayload state;

  public static void set(CosmeticPayload p) {
    state = p;
  }

  public static void clear() {
    state = null;
  }

  public static boolean isBot(UUID id) {
    var p = state;
    return p != null && p.bot().equals(id) && !id.equals(new UUID(0, 0));
  }

  public static boolean enabled(UUID id, int bit) {
    var p = state;
    return p != null && (p.owner().equals(id) || p.bot().equals(id)) && (p.mask() & bit) != 0;
  }
}
