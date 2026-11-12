package com.duckswords.input;
public final class SmoothCps244Test{
 static int checks;static void check(boolean ok){checks++;if(!ok)throw new AssertionError("Check "+checks);}
 public static void main(String[] a){
  long t=0;check(SmoothCps244.at(20,0,t)==20);t+=10_000_000L;check(SmoothCps244.at(0,0,t)==20);
  int previous=20;boolean intermediate=false;
  for(int n=1;n<=21;n++){int value=SmoothCps244.at(0,0,t+n*20_000_000L);check(value<=previous&&value>=0);intermediate|=value>0&&value<20;previous=value;}
  check(intermediate);check(previous==0);check(SmoothCps244.at(15,0,t+500_000_000L)==15);
  long start=4_000_000_000L;check(SmoothCps244.at(18,1,start)==18);check(SmoothCps244.at(2,1,start+10_000_000L)==18);int half=SmoothCps244.at(2,1,start+185_000_000L);check(half>2&&half<18);check(SmoothCps244.at(2,1,start+360_000_000L)==2);
  check(SmoothCps244.at(22,1,start+370_000_000L)==22);check(SmoothCps244.at(0,1,start+3_000_000_000L)==0);
  check(SmoothCps244.at(9,2,0)==9);check(SmoothCps244.at(0,2,10_000_000L)==9);check(SmoothCps244.at(0,2,185_000_000L)==5);
  check(SmoothCps244.at(100,3,0)==100);check(SmoothCps244.at(-8,-1,0)==0);
  for(long base:new long[]{-5_000_000_000L,Long.MAX_VALUE-100_000_000L}){check(SmoothCps244.at(16,2,base)==16);check(SmoothCps244.at(0,2,base+10_000_000L)==16);check(SmoothCps244.at(0,2,base+185_000_000L)==8);check(SmoothCps244.at(0,2,base+360_000_000L)==0);}
  System.out.println("PASS "+checks+" HUD smoothing checks: gradual fall, immediate increase, independent channels, pause, negative/wrapped monotonic clock");
 }
}
