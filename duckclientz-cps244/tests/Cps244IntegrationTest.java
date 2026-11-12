import com.duckswords.modules.CpsDisplay;import com.duckswords.input.*;import com.duckswords.util.Keys;import java.lang.reflect.*;import java.util.*;import net.minecraft.*;
public final class Cps244IntegrationTest{
 static int checks;static Method observer;static Object mouse;
 static void check(boolean ok){checks++;if(!ok)throw new AssertionError("Check "+checks);}
 static int shown(){return Integer.parseInt(CpsDisplay.formatMiddle230("{middle}"));}
 static void event(int b,int action)throws Exception{Keys.held[b]=action!=0;if(observer.getParameterTypes()[1]==int.class)observer.invoke(mouse,0L,b,action,0,null);else observer.invoke(mouse,0L,new class_11910(b),action,null);if(action==1){if(b==0)CpsDisplay.addLeft();if(b==1)CpsDisplay.addRight();}}
 public static void main(String[] a)throws Exception{
  Class<?> c=Class.forName("Mouse243");mouse=c.getConstructor().newInstance();observer=Arrays.stream(c.getMethods()).filter(m->m.getName().equals("duck$middleCps230")).findFirst().orElseThrow();
  for(int i=0;i<20;i++)CpsDisplay.addMiddle();check(shown()==20);
  Cps243Clock.now=1_001_000_000L;check(CpsDisplay.currentMiddleCps()==0);check(shown()==20);
  Cps243Clock.now+=175_000_000L;check(shown()==10);check(CpsDisplay.currentMiddleCps()==0);
  Cps243Clock.now+=175_000_000L;check(shown()==0);
  Cps243Clock.now=2_000_000_000L;for(int i=0;i<15;i++)CpsDisplay.addMiddle();check(shown()==15);
  event(1,1);check(CpsDisplay.currentRightCps()==1);check(shown()==15);check(CpsDisplay.currentMiddleCps()==15);
  Cps243Clock.now+=175_000_000L;int half=shown();check(half>1&&half<15);check(CpsDisplay.currentRightCps()==1);check(CpsDisplay.currentMiddleCps()==15);
  Cps243Clock.now+=175_000_000L;check(shown()==1);check(CpsDisplay.currentRightCps()==1);check(CpsDisplay.currentMiddleCps()==15);
  event(1,0);event(2,1);check(shown()==16); // return to middle: increase stays immediate
  System.out.println("PASS "+checks+" exact formatter/observer checks: visual fall on idle and button switch; real CPS preserved: "+a[0]);
 }
}
