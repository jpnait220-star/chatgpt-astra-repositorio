package com.duckswords.render;
import com.duckswords.modules.TargetHighlight;
/** Pure selection gates; rendering adapters are generated from each exact native version. */
public final class TargetTop242 {
 private TargetTop242(){}
 public static boolean allowed(boolean original,TargetHighlight module,Object entity){return original&&(!module.onlyElytra.getValue()||gliding(entity));}
 public static boolean candidate(Object entity,TargetHighlight module){return allowed(alive(entity),module,entity);}
 public static boolean render(Object entity,TargetHighlight module){return allowed(visible(entity),module,entity);}
 public static boolean alive(Object entity){throw new IllegalStateException("native entity alive adapter");}
 public static boolean visible(Object entity){throw new IllegalStateException("native cleaner visibility adapter");}
 public static boolean gliding(Object entity){throw new IllegalStateException("native gliding adapter");}
}
