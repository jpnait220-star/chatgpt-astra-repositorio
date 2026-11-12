package com.duckswords.input;

/** Select only a physically held mouse button assigned to Attack; middle keeps its own counter. */
public final class AdaptiveCps243 {
 private static final boolean[] held=new boolean[3];private static int latest=0,selected=2;
 private AdaptiveCps243(){}
 public static void reset(){held[0]=held[1]=held[2]=false;selected=2;latest=0;}
 public static void mouse(int button,int action,long now){
  if(button<0||button>2||(action!=0&&action!=1))return;
  AttackBindings246.input();
  if(action==1){if(button<2&&!AttackBindings246.matches(button))return;held[button]=true;if(button<2)latest=button;}
  else held[button]=false;
 }
 public static void reconcile(boolean left,boolean right,boolean middle,long now){
  boolean l=left&&AttackBindings246.matches(0),r=right&&AttackBindings246.matches(1);
  if(l&&!held[0])latest=0;if(r&&!held[1])latest=1;
  held[0]=l;held[1]=r;held[2]=middle;
 }
 public static int button(){return selected;}
 public static int current(int left,int right,int middle,long now){
  selected=held[0]&&held[1]?latest:held[0]?0:held[1]?1:2;
  return selected==0?left:selected==1?right:middle;
 }
}
