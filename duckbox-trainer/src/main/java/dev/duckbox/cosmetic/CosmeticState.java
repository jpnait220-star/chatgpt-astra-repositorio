package dev.duckbox.cosmetic;

import dev.duckbox.CosmeticPayload;
import java.util.UUID;

public final class CosmeticState {
  private static volatile CosmeticPayload state;
  private static volatile dev.duckbox.LobbyBotPayload lobby;

  public static void setLobby(dev.duckbox.LobbyBotPayload p) {
    lobby = p;
  }

  public static void set(CosmeticPayload p) {
    state = p;
  }

  public static void clear() {
    state = null;
    lobby = null;
  }

  public static boolean isBot(UUID id) {
    var p = state;
    return !id.equals(new UUID(0, 0))
        && ((p != null && p.bot().equals(id)) || (lobby != null && lobby.bot().equals(id)));
  }

  public static boolean enabled(UUID id, int bit) {
    var p = state;
    return (p != null && (p.owner().equals(id) || p.bot().equals(id)) && (p.mask() & bit) != 0)
        || (lobby != null && lobby.bot().equals(id) && (lobby.mask() & bit) != 0);
  }
}
