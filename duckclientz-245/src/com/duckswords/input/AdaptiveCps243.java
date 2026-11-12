package com.duckswords.input;

/** Display selection only. Never creates clicks or changes input bindings. */
public final class AdaptiveCps243 {
    private static final long WINDOW = 120_000_000L;
    private static final boolean[] held = new boolean[3];
    private static int manual = -1, selected = 2;
    private static long until;
    private static boolean lingering;
    private AdaptiveCps243() {}
    public static void reset() {
        held[0] = held[1] = held[2] = false;
        manual = -1; selected = 2; lingering = false;
    }
    public static void mouse(int button, int action, long now) {
        if (button < 0 || button > 2 || (action != 0 && action != 1)) return;
        if (action == 1) {
            if (held[button]) return;
            held[button] = true;
            if (button != 2) { manual = button; lingering = false; }
            else if (!held[0] && !held[1]) { manual = -1; lingering = false; }
        } else {
            if (!held[button]) return;
            held[button] = false;
            if (button != 2) {
                if (held[0] || held[1]) { manual = held[0] ? 0 : 1; lingering = false; }
                else if (held[2]) { manual = -1; lingering = false; }
                else { manual = button; until = now + WINDOW; lingering = true; }
            }
        }
    }
    /** Recover lost releases without inventing a press. */
    public static void reconcile(boolean left, boolean right, boolean middle, long now) {
        if (held[0] && !left) mouse(0, 0, now);
        if (held[1] && !right) mouse(1, 0, now);
        if (held[2] && !middle) mouse(2, 0, now);
    }
    public static int button(){ return selected; }
    public static int current(int left, int right, int middle, long now) {
        if (held[0] || held[1]) selected = held[0] && held[1] ? manual : held[0] ? 0 : 1;
        else if (held[2]) selected = 2;
        else if (lingering && now - until <= 0) selected = manual;
        else { lingering = false; manual = -1; selected = 2; }
        return selected == 0 ? left : selected == 1 ? right : middle;
    }
}
