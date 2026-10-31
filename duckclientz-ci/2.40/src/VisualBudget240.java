package com.duckswords.perf;
/** Allocation-free throttling of optional cosmetic effects only. */
public final class VisualBudget240 {
 private static long combatWindow,ambientWindow;
 private static int hitUsed,critUsed,ambientUsed;
 private VisualBudget240(){}
 private static int combat(int count,boolean critical){
  if(count<=0)return 0;
  long now=System.nanoTime();
  if(combatWindow==0||now-combatWindow<0||now-combatWindow>=50_000_000L){
   combatWindow=now;hitUsed=0;critUsed=0;
  }
  int used=critical?critUsed:hitUsed,cap=critical?28:40;
  int amount=Math.min(count,Math.max(0,cap-used));
  if(critical)critUsed+=amount;else hitUsed+=amount;
  return amount;
 }
 public static int hit(int count){return combat(count,false);}
 public static int critical(int count){return combat(count,true);}
 public static boolean visible(boolean safe){return safe&&ambient();}
 public static boolean ambient(){
  long now=System.nanoTime();
  if(ambientWindow==0||now-ambientWindow<0||now-ambientWindow>=50_000_000L){ambientWindow=now;ambientUsed=0;}
  if(ambientUsed>=24)return false;
  ambientUsed++;return true;
 }
}