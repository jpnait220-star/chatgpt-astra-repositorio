package com.duckswords.perf;
/** Allocation-free burst limit for optional combat particle effects. */
public final class VisualBudget240 {
 private static long hitWindow,critWindow;
 private static int hitUsed,critUsed;
 private VisualBudget240(){}
 private static int admit(int requested,boolean crit){
  if(requested<=0)return 0;
  long now=System.nanoTime(),window=crit?critWindow:hitWindow;
  if(window==0||now-window<0||now-window>=50_000_000L){
   if(crit){critWindow=now;critUsed=0;}else{hitWindow=now;hitUsed=0;}
  }
  int used=crit?critUsed:hitUsed, limit=crit?32:48;
  int accepted=Math.min(requested,Math.max(0,limit-used));
  if(crit)critUsed+=accepted;else hitUsed+=accepted;
  return accepted;
 }
 public static int hit(int count){return admit(count,false);}
 public static int critical(int count){return admit(count,true);}
}