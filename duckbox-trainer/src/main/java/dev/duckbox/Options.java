package dev.duckbox;

public final class Options {
  public enum Difficulty {
    LOW(10, 14, 15, 5, 0.30, 0.28),
    MEDIUM(8, 18, 15, 4, 0.40, 0.36),
    HIGH(6, 23, 15, 3, 0.60, 0.45),
    EXPERT(4, 34, 15, 2, 0.85, 0.65);
    public final int reaction, aimSpeed, cps, swapDelay;
    public final double rockets, strafe;

    public int refillDelayTicks() {
      return switch (this) {
        case LOW -> 8;
        case MEDIUM -> 5;
        case HIGH -> 3;
        case EXPERT -> 2;
      };
    }

    Difficulty(int r, int a, int c, int s, double k, double st) {
      reaction = r;
      aimSpeed = a;
      cps = c;
      swapDelay = s;
      rockets = k;
      strafe = st;
    }
  }

  public enum Rules {
    NORMAL_SPAM,
    INSTA_KILL;

    @Override
    public String toString() {
      return this == NORMAL_SPAM ? "Spam" : "Insta Kill";
    }

    public static Rules parse(String name) {
      return name.equalsIgnoreCase("SPAM")
          ? NORMAL_SPAM
          : valueOf(name.toUpperCase(java.util.Locale.ROOT));
    }
  }

  public enum SpinLevel {
    BAIXO(110, 32, 0.25),
    MEDIO(65, 22, 0.50),
    ALTO(35, 12, 0.80),
    EXTREMO(18, 8, 1.0);
    public final int interval, rocketDelay;
    public final double chance;

    SpinLevel(int interval, int rocketDelay, double chance) {
      this.interval = interval;
      this.rocketDelay = rocketDelay;
      this.chance = chance;
    }
  }

  public Rules rules = Rules.NORMAL_SPAM;
  public SpinLevel spin = SpinLevel.MEDIO;
  public boolean blood = true, money = true, glasses = true, frog = true;
  public Difficulty difficulty = Difficulty.MEDIUM;
  public boolean giro = true,
      gap = true,
      retotem = true,
      teia = true,
      wtap = true,
      strafe = true,
      webRocket = true,
      tank = false;
  public int revision = 2, size = 13, webCooldown = 200;
  public int cps = 15;

  public static boolean allowedCps(int cps) {
    return cps == 10 || cps == 13 || cps == 15;
  }

  public static int nextCps(int cps) {
    return cps == 10 ? 13 : cps == 13 ? 15 : 10;
  }

  public boolean initialized = false, built = false;
  public static final int ARENA_X = -5, ARENA_Y = 78, ARENA_Z = 111;
  public int x = ARENA_X, y = ARENA_Y, z = ARENA_Z;
  public boolean autoBuildOnJoin = false, customMap = false;

  public static int allowedSize(int value) {
    return value <= 9 ? 9 : value <= 13 ? 13 : 17;
  }

  public static int nextSize(int value) {
    return value < 13 ? 13 : value < 17 ? 17 : 9;
  }

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
