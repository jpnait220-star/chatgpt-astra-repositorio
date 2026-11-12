package com.duckswords.input;
/** Both directions interpolate when the adaptive source changes; actual counters stay untouched. */
public final class SmoothCps244 {
 private static final long FALL=900_000_000L,CHANGE=600_000_000L,RESET=2_000_000_000L;
 private static final boolean[] ready=new boolean[3],transition=new boolean[3];
 private static final double[] from=new double[3];private static final int[] target=new int[3],source=new int[3];
 private static final long[] start=new long[3],sample=new long[3],duration=new long[3],until=new long[3];
 private SmoothCps244(){}
 public static int display(int actual,int slot){return at(actual,slot,slot==2?AdaptiveCps243.button():slot,System.nanoTime());}
 static int at(int actual,int slot,int mode,long now){
  actual=Math.max(0,actual);if(slot<0||slot>2)return actual;long gap=now-sample[slot];
  if(!ready[slot]||gap<0||gap>RESET){ready[slot]=true;from[slot]=target[slot]=actual;source[slot]=mode;start[slot]=sample[slot]=now;duration[slot]=FALL;transition[slot]=false;return actual;}
  double progress=Math.min(1,Math.max(0,(double)(now-start[slot])/Math.max(1,duration[slot])));
  double value=from[slot]+(target[slot]-from[slot])*progress;sample[slot]=now;
  boolean changed=source[slot]!=mode;
  if(changed){source[slot]=mode;until[slot]=now+CHANGE;transition[slot]=true;}
  if(transition[slot]&&now-until[slot]>=0)transition[slot]=false;
  if(!transition[slot]&&actual>=value){from[slot]=target[slot]=actual;start[slot]=now;return actual;}
  if(actual!=target[slot]||changed){from[slot]=value;target[slot]=actual;start[slot]=now;duration[slot]=transition[slot]?Math.max(1,until[slot]-now):FALL;}
  return Math.max(0,(int)Math.round(value));
 }
}
