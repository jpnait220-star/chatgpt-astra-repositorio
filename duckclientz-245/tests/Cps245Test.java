package com.duckswords.input;
public final class Cps245Test{
 static int checks;static void ok(boolean b){checks++;if(!b)throw new AssertionError("Check "+checks);}
 public static void main(String[] a){
  long now=0;ok(SmoothCps244.at(20,0,0,now)==20);now+=10_000_000L;ok(SmoothCps244.at(0,0,0,now)==20);
  ok(SmoothCps244.at(0,0,0,now+350_000_000L)>10);ok(SmoothCps244.at(0,0,0,now+450_000_000L)==10);ok(SmoothCps244.at(0,0,0,now+900_000_000L)==0);
  ok(SmoothCps244.at(15,0,0,now+910_000_000L)==15);
  long t=4_000_000_000L;ok(SmoothCps244.at(20,2,2,t)==20);ok(SmoothCps244.at(1,2,1,t+10_000_000L)==20);
  int half=SmoothCps244.at(1,2,1,t+50_000_000L);ok(half>1&&half<20);ok(SmoothCps244.at(1,2,1,t+90_000_000L)==1);
  ok(SmoothCps244.at(0,2,2,t+100_000_000L)==1);ok(SmoothCps244.at(0,2,2,t+180_000_000L)==0);
  AdaptiveCps243.reset();AdaptiveCps243.mouse(1,1,t);ok(AdaptiveCps243.current(2,7,15,t)==7);ok(AdaptiveCps243.button()==1);
  AdaptiveCps243.mouse(1,0,t);ok(AdaptiveCps243.current(2,7,15,t+119_000_000L)==7);ok(AdaptiveCps243.current(2,7,15,t+121_000_000L)==15);ok(AdaptiveCps243.button()==2);
  AdaptiveCps243.mouse(0,1,t+200_000_000L);AdaptiveCps243.mouse(2,1,t+210_000_000L);ok(AdaptiveCps243.current(4,7,15,t+210_000_000L)==4);
  AdaptiveCps243.mouse(0,0,t+220_000_000L);ok(AdaptiveCps243.current(4,7,15,t+220_000_000L)==15);
  AdaptiveCps243.reset();AdaptiveCps243.reconcile(true,true,true,t);ok(AdaptiveCps243.current(4,7,15,t)==15);
  // A changing target during a source switch must still finish by the original fast deadline.
  t=8_000_000_000L;ok(SmoothCps244.at(20,2,2,t)==20);SmoothCps244.at(1,2,1,t+10_000_000L);SmoothCps244.at(2,2,1,t+40_000_000L);ok(SmoothCps244.at(2,2,1,t+90_000_000L)==2);
  for(long base:new long[]{-3_000_000_000L,Long.MAX_VALUE-100_000_000L}){ok(SmoothCps244.at(20,1,1,base)==20);ok(SmoothCps244.at(0,1,1,base+10_000_000L)==20);ok(SmoothCps244.at(0,1,1,base+460_000_000L)==10);ok(SmoothCps244.at(0,1,1,base+910_000_000L)==0);}
  System.out.println("PASS "+checks+" timing checks: 900 ms natural fall vs 80 ms source switch, 120 ms manual release, unchanged button semantics");
 }
}
