package dev.duckbox;

/** Fractional server-tick schedule:15 attempts every20 eligible ticks; no catch-up bursts. */
public final class CpsCadence {
  private final int rate;
  private int credit;

  public CpsCadence(int rate) {
    if (rate < 1 || rate > 20) throw new IllegalArgumentException("CPS must be1..20");
    this.rate = rate;
  }

  public boolean next() {
    credit += rate;
    if (credit < 20) return false;
    credit -= 20;
    return true;
  }
}
