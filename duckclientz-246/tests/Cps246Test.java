package com.duckswords.input;
public final class Cps246Test {
 static int checks;static void check(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
 static int at(int count,int source,long ms){return SmoothCps244.at(count,2,source,ms*1_000_000L);}
 public static void main(String[] args){
  check(at(20,2,0)==20,"initial middle");check(at(1,1,0)==20,"no source-change snap down");
  check(at(1,1,300)==11,"half decline");check(at(1,1,600)==1,"decline endpoint");
  check(at(20,2,600)==1,"no source-change snap up");check(at(20,2,900)==11,"half ascent");check(at(20,2,1200)==20,"ascent endpoint");
  check(at(0,1,1200)==20,"second decline starts at current display");check(at(0,1,1800)==0,"second decline completes");
  check(at(24,2,1800)==0,"return starts at zero");int v=at(16,2,2000);check(v==8,"retarget current middle during ascent");
  check(at(16,2,2200)==12,"remaining transition continues smoothly");check(at(16,2,2400)==16,"finishes on current middle");
  check(at(0,2,2400)==16,"ordinary stop begins at displayed CPS");check(at(0,2,2850)==8,"ordinary decay stays slow");check(at(0,2,3300)==0,"ordinary decay endpoint");
  check(at(12,2,3300)==12,"ordinary clicking responds immediately");
  long now=Long.MAX_VALUE-400_000_000L;check(SmoothCps244.at(20,2,2,now)==20,"reset after inactivity");
  check(SmoothCps244.at(0,2,1,now)==20,"transition before clock overflow");
  check(SmoothCps244.at(0,2,1,now+300_000_000L)==10,"before overflow midpoint");check(SmoothCps244.at(0,2,1,now+600_000_000L)==0,"clock overflow endpoint");
  System.out.println("PASS "+checks+" timing checks: bidirectional transitions, live retarget, normal decay, nanoTime overflow.");
 }
}
