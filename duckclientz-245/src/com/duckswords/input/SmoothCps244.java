package com.duckswords.input;

/** Slow natural decay, fast source changes. HUD only; never modifies click counters. */
public final class SmoothCps244 {
 private static final long SLOW=900_000_000L,FAST=80_000_000L,RESET_AFTER=2_000_000_000L;
 private static final boolean[] ready=new boolean[3];
 private static final double[] from=new double[3];
 private static final int[] target=new int[3],source=new int[3];
 private static final long[] start=new long[3],sample=new long[3],duration=new long[3],fastUntil=new long[3];
 private static final boolean[] fast=new boolean[3];
 private SmoothCps244(){}
 public static int display(int actual,int slot){return at(actual,slot,slot==2?AdaptiveCps243.button():slot,System.nanoTime());}
 static int at(int actual,int slot,int mode,long now){
  actual=Math.max(0,actual);if(slot<0||slot>=3)return actual;
  long gap=now-sample[slot];
  if(!ready[slot]||gap<0||gap>RESET_AFTER){ready[slot]=true;from[slot]=target[slot]=actual;source[slot]=mode;start[slot]=sample[slot]=now;duration[slot]=SLOW;fast[slot]=false;return actual;}
  double progress=Math.min(1,Math.max(0,(double)(now-start[slot])/Math.max(1,duration[slot])));
  double value=from[slot]+(target[slot]-from[slot])*progress;sample[slot]=now;
  boolean changed=source[slot]!=mode;
  if(changed){source[slot]=mode;fastUntil[slot]=now+FAST;fast[slot]=true;}
  if(fast[slot]&&now-fastUntil[slot]>=0)fast[slot]=false;
  if(actual>=value){from[slot]=target[slot]=actual;start[slot]=now;return actual;}
  if(actual!=target[slot]||changed){from[slot]=value;target[slot]=actual;start[slot]=now;duration[slot]=fast[slot]?Math.max(1,fastUntil[slot]-now):SLOW;}
  return Math.max(actual,(int)Math.round(value));
 }
}
