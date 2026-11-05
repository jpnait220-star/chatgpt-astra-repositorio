package com.duckunified.duckbox;

/** Optional trainer integration; no dependency on Minecraft or Fabric at link time. */
public final class HitDelayScope {
  private static java.lang.reflect.Method hook;
  private static boolean checked;

  public static boolean allow() {
    if (!checked) {
      checked = true;
      try {
        hook =
            Class.forName("dev.duckbox.ClientTrainingState")
                .getMethod("allowExternalMouseHitDelay");
      } catch (ReflectiveOperationException ignored) {
      }
    }
    if (hook == null) return true;
    try {
      return Boolean.TRUE.equals(hook.invoke(null));
    } catch (ReflectiveOperationException ignored) {
      return false;
    }
  }
}
