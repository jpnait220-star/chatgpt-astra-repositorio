package dev.duckbox;

import java.nio.file.*;
import java.io.*;

public final class WorldBranding {
  public static boolean apply(Path root) throws IOException {
    try (var source = WorldBranding.class.getResourceAsStream("/assets/duckbox/world_icon.png")) {
      if (source == null) return false;
      Path icon = root.resolve("icon.png"), backup = root.resolve("icon-before-duckbox.png");
      if (Files.exists(icon) && !Files.exists(backup)) Files.copy(icon, backup);
      Path temp = root.resolve("icon.duckbox.tmp");
      Files.copy(source, temp, StandardCopyOption.REPLACE_EXISTING);
      Files.move(temp, icon, StandardCopyOption.REPLACE_EXISTING);
      return true;
    }
  }
}
