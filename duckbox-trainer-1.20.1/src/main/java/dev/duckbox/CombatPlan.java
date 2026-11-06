package dev.duckbox;

public final class CombatPlan {
  public static boolean mayReposition(
      boolean enabled,
      boolean gliding,
      boolean healing,
      boolean tank,
      int tick,
      int next,
      double distanceSquared,
      double heightDifference) {
    return enabled
        && gliding
        && !healing
        && !tank
        && tick >= next
        && distanceSquared >= 2.25
        && distanceSquared <= 20.25
        && Math.abs(heightDifference) <= 3;
  }

  public static double meleeIntentRange(double reach) {
    return (reach + 0.7) * (reach + 0.7);
  }

  private CombatPlan() {}
}
