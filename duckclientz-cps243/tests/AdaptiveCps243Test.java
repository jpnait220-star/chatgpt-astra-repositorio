import com.duckswords.input.*;
public final class AdaptiveCps243Test{
 static int checks;
 static void check(boolean ok){checks++;if(!ok)throw new AssertionError("Check "+checks);}
 public static void main(String[] a){
  AdaptiveCps243.reset();check(AdaptiveCps243.current(3,7,15,0)==15);
  AdaptiveCps243.mouse(1,1,0);check(AdaptiveCps243.current(3,7,15,0)==7);check(AdaptiveCps243.current(3,0,15,5_000_000_000L)==0);
  AdaptiveCps243.mouse(1,0,5_000_000_000L);check(AdaptiveCps243.current(3,7,15,5_500_000_000L)==7);check(AdaptiveCps243.current(3,7,15,6_000_000_000L)==7);check(AdaptiveCps243.current(3,7,15,6_000_000_001L)==15);
  AdaptiveCps243.mouse(0,1,7_000_000_000L);check(AdaptiveCps243.current(3,7,15,7_000_000_000L)==3);
  AdaptiveCps243.mouse(1,1,7_000_000_001L);check(AdaptiveCps243.current(3,7,15,7_000_000_001L)==7);
  AdaptiveCps243.mouse(2,1,7_000_000_002L);check(AdaptiveCps243.current(3,7,15,7_000_000_002L)==7);
  AdaptiveCps243.mouse(1,0,7_000_000_003L);check(AdaptiveCps243.current(3,7,15,7_000_000_003L)==3);
  AdaptiveCps243.mouse(0,0,7_000_000_004L);check(AdaptiveCps243.current(3,7,15,7_000_000_004L)==15);
  AdaptiveCps243.mouse(2,0,7_000_000_005L);check(AdaptiveCps243.current(3,7,15,7_000_000_005L)==15);
  AdaptiveCps243.mouse(1,1,0);AdaptiveCps243.reconcile(false,false,false,10);check(AdaptiveCps243.current(3,7,15,500_000_000L)==7);check(AdaptiveCps243.current(3,7,15,1_000_000_011L)==15);
  AdaptiveCps243.mouse(1,1,0);AdaptiveCps243.reset();check(AdaptiveCps243.current(3,7,15,0)==15);
  AdaptiveCps243.reconcile(true,true,true,0);check(AdaptiveCps243.current(3,7,15,0)==15);
  for(int[] pair:new int[][]{{3,1},{-1,1},{0,2},{0,-1}})AdaptiveCps243.mouse(pair[0],pair[1],0);check(AdaptiveCps243.current(3,7,15,0)==15);
  for(long start:new long[]{-9_000_000_000L,Long.MAX_VALUE-500_000_000L}){
   AdaptiveCps243.reset();AdaptiveCps243.mouse(0,1,start);AdaptiveCps243.mouse(0,0,start);
   check(AdaptiveCps243.current(3,7,15,start+500_000_000L)==3);check(AdaptiveCps243.current(3,7,15,start+1_000_000_001L)==15);
  }
  System.out.println("PASS "+checks+" selection cases: active/held L-R, no summed or invented clicks, middle resume, grace, invalid input, lost release, negative/wrapped clock");
 }
}
