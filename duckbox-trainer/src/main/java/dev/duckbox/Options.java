package dev.duckbox;

public final class Options {
  public enum Difficulty {
    LOW(16, 7, 5, 7, 0.09, 0.10),
    MEDIUM(10, 14, 8, 5, 0.30, 0.28),
    HIGH(6, 23, 11, 3, 0.60, 0.45),
    EXPERT(4, 34, 14, 2, 0.85, 0.65);
    public final int reaction, aimSpeed, cps, swapDelay;
    public final double rockets, strafe;

    Difficulty(int r, int a, int c, int s, double k, double st) {
      reaction = r;
      aimSpeed = a;
      cps = c;
      swapDelay = s;
      rockets = k;
      strafe = st;
    }
  }

  public Difficulty difficulty = Difficulty.MEDIUM;
  public boolean giro = true,
      gap = true,
      retotem = true,
      teia = true,
      wtap = true,
      strafe = true,
      webRocket = true,
      tank = false;
  public int size = 25, webCooldown = 200;
  public boolean initialized = false, built = false;
  public int x, y, z;
  public String dimension = "minecraft:overworld";

  public boolean toggle(String key) {
    return switch (key) {
      case "giro" -> giro = !giro;
      case "gap" -> gap = !gap;
      case "retotem" -> retotem = !retotem;
      case "teia" -> teia = !teia;
      case "wtap" -> wtap = !wtap;
      case "strafe" -> strafe = !strafe;
      case "foguete_teia" -> webRocket = !webRocket;
      case "tank" -> tank = !tank;
      default -> throw new IllegalArgumentException(key);
    };
  }
}
