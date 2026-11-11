import com.duckswords.modules.CpsDisplay;import com.duckswords.input.*;import com.duckswords.util.Keys;import com.duckswords.client.ClientData;import net.minecraft.*;import java.lang.reflect.*;import java.util.*;
public final class Cps243IntegrationTest {
 static int checks;static Method observer;static Object mouse;
 static void check(boolean ok){checks++;if(!ok)throw new AssertionError("Check "+checks);}
 static void event(int b,int action)throws Exception{Keys.held[b]=action!=0;if(observer.getParameterTypes()[1]==int.class)observer.invoke(mouse,0L,b,action,0,null);else observer.invoke(mouse,0L,new class_11910(b),action,null);if(action==1){if(b==0)CpsDisplay.addLeft();if(b==1)CpsDisplay.addRight();}}
 static String display(){return CpsDisplay.formatMiddle230("{middle}/{middle}|{cps}|{right}");}
 static void value(int n){String actual=display();checks++;if(!actual.equals(n+"/"+n+"|{cps}|{right}"))throw new AssertionError("Check "+checks+" expected "+n+" actual "+actual);}
 static void reset()throws Exception{AdaptiveCps243.reset();for(String name:List.of("LEFT","RIGHT","MIDDLE")){Field f=CpsDisplay.class.getDeclaredField(name);f.setAccessible(true);((Deque<?>)f.get(null)).clear();}Arrays.fill(Keys.held,false);Cps243Clock.now=0;ClientData.focus=true;AutoClickerRuntime.fake=false;class_310 mc=class_310.method_1551();mc.field_1755=null;mc.field_1724=new class_746();mc.field_1687=new class_638();}
 public static void main(String[] args)throws Exception{
  Class<?> clazz=Class.forName("Mouse243");mouse=clazz.getConstructor().newInstance();observer=Arrays.stream(clazz.getMethods()).filter(m->m.getName().equals("duck$middleCps230")).findFirst().orElseThrow();reset();
  for(int i=0;i<10;i++)CpsDisplay.addMiddle();value(10);event(1,1);value(1);check(CpsDisplay.currentMiddleCps()==10);event(1,0);value(1);
  Cps243Clock.now=500_000_000L;CpsDisplay.addMiddle();value(1);Cps243Clock.now=1_001_000_000L;value(1); // old middle clicks expired; newer middle survives
  Cps243Clock.now=2_000_000_000L;CpsDisplay.addMiddle();event(1,1);value(1);Cps243Clock.now=4_000_000_000L;CpsDisplay.addMiddle();value(0);check(CpsDisplay.currentMiddleCps()==1); // held does not spam CPS
  event(1,0);value(0);event(2,1);value(2);event(2,0);value(2);
  reset();for(int i=0;i<6;i++)CpsDisplay.addMiddle();event(0,1);event(0,0);value(1);check(CpsDisplay.currentLeftCps()==1);event(1,1);value(1);event(0,1);value(2);event(0,0);value(1);event(1,0);
  reset();for(int i=0;i<5;i++)CpsDisplay.addMiddle();event(1,1);value(1);Keys.held[1]=false;value(1);Cps243Clock.now=1_001_000_000L;CpsDisplay.addMiddle();value(1); // release recovery exits override
  reset();CpsDisplay.addMiddle();event(1,1);value(1);class_310.method_1551().field_1755=new class_437();value(1);class_310.method_1551().field_1755=null;CpsDisplay.addMiddle();value(2); // screen clears held override
  event(1,0);AutoClickerRuntime.fake=true;event(0,1);value(2);AutoClickerRuntime.fake=false;event(0,0);
  event(1,1);ClientData.focus=false;value(2);ClientData.focus=true;value(2);
  event(1,0);event(0,1);class_310.method_1551().field_1724=null;value(2);class_310.method_1551().field_1724=new class_746();value(2);
  reset();event(2,1);value(1);event(2,0);value(1);check(CpsDisplay.currentMiddleCps()==1);Cps243Clock.now=1_001_000_000L;value(0);
  System.out.println("PASS "+checks+" exact CPS/formatter and actual version-specific input observer checks: "+args[0]);
 }
}
