package com.duckswords.input;

/** HUD only. Real one-second counters are never changed. */
public final class SmoothCps244 {
 private static final long DURATION=350_000_000L,RESET_AFTER=2_000_000_000L;
 private static final boolean[] ready=new boolean[3];
 private static final double[] from=new double[3];
 private static final int[] target=new int[3];
 private static final long[] start=new long[3],sample=new long[3];
 private SmoothCps244(){}
 public static int display(int actual,int slot){return at(actual,slot,System.nanoTime());}
 static int at(int actual,int slot,long now){
  actual=Math.max(0,actual);
  if(slot<0||slot>=3)return actual;
  long gap=now-sample[slot];
  if(!ready[slot]||gap<0||gap>RESET_AFTER){ready[slot]=true;from[slot]=target[slot]=actual;start[slot]=sample[slot]=now;return actual;}
  double progress=Math.min(1,Math.max(0,(double)(now-start[slot])/DURATION));
  double value=from[slot]+(target[slot]-from[slot])*progress;
  sample[slot]=now;
  if(actual>=value){from[slot]=target[slot]=actual;start[slot]=now;return actual;}
  if(actual!=target[slot]){from[slot]=value;target[slot]=actual;start[slot]=now;}
  return Math.max(actual,(int)Math.round(value));
 }
}
