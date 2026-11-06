package dev.duckbox;

public final class Aim {
  public static float wrap(float degrees) {
    float a = degrees % 360;
    return a >= 180 ? a - 360 : a < -180 ? a + 360 : a;
  }

  public static float approach(float now, float target, float limit) {
    return now + Math.max(-limit, Math.min(limit, wrap(target - now)));
  }

  public static double fraction(double health, double max) {
    return max <= 0 ? 0 : health / max;
  }

  private Aim() {}
}
