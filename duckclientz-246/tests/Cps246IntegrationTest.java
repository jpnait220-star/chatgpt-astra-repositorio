import com.duckswords.modules.CpsDisplay;import com.duckswords.input.*;import com.duckswords.util.Keys;import net.minecraft.*;import us.kenny.MultiKeyBindingManager;import us.kenny.core.MultiKeyBinding;import java.lang.reflect.*;import java.util.*;
public final class Cps246IntegrationTest {
 static int checks;static Object mouse;static Method observer;
 static void check(boolean b,String message){checks++;if(!b)throw new AssertionError(message+" #"+checks);}
 static int shown(){return Integer.parseInt(CpsDisplay.formatMiddle230("{middle}"));}
 static void event(int button,int action)throws Exception{Keys.held[button]=action==1;if(observer.getParameterTypes()[1]==int.class)observer.invoke(mouse,0L,button,action,0,null);else observer.invoke(mouse,0L,new class_11910(button),action,null);if(action==1){if(button==0)CpsDisplay.addLeft();if(button==1)CpsDisplay.addRight();}}
 public static void main(String[] a)throws Exception{
  Class<?> c=Class.forName("Mouse243");mouse=c.getConstructor().newInstance();observer=Arrays.stream(c.getMethods()).filter(m->m.getName().equals("duck$middleCps230")).findFirst().orElseThrow();
  boolean multi=a.length<2||!a[1].equals("vanilla");
  if(multi)MultiKeyBindingManager.attack.add(new MultiKeyBinding("key.mouse.right"));else class_310.method_1551().field_1690.field_1886.binding="key.mouse.right";
  AttackBindings246.input();
  for(int i=0;i<20;i++)CpsDisplay.addMiddle();check(shown()==20,"middle starts at actual CPS");
  event(1,1);check(shown()==20,"holding attack-right must start a smooth decline");check(CpsDisplay.currentMiddleCps()==20,"middle counter continues independently");
  Cps243Clock.now=300_000_000L;int down=shown();check(down>1&&down<20,"intermediate descending value");
  Cps243Clock.now=600_000_000L;check(shown()==1,"arrives at actual right CPS");
  Cps243Clock.now=1_001_000_000L;for(int i=0;i<16;i++)CpsDisplay.addMiddle();shown();
  Cps243Clock.now=1_901_000_000L;check(shown()==0,"held right settles at zero instead of continuing middle CPS");check(CpsDisplay.currentMiddleCps()==16,"middle still counts while attack-right is held");
  event(1,0);check(shown()==0,"release must begin smooth ascent rather than jump");check(AdaptiveCps243.button()==2,"release selects middle immediately; no lingering wrong source");
  Cps243Clock.now=2_001_000_000L;for(int i=0;i<18;i++)CpsDisplay.addMiddle();int up=shown();check(up>0&&up<18,"intermediate ascent despite live middle CPS change");
  Cps243Clock.now=2_201_000_000L;up=shown();check(up>0&&up<18,"continues ascending toward middle");
  Cps243Clock.now=2_501_000_000L;check(shown()==18,"arrives at current middle CPS, not stale pre-hold CPS");
  if(multi)MultiKeyBindingManager.attack.clear();class_310.method_1551().field_1690.field_1886.binding="key.mouse.middle";AttackBindings246.input();
  event(1,1);check(shown()==18,"right bound only to Use cannot take over middle");check(AdaptiveCps243.button()==2,"non-attack right ignored");event(1,0);
  class_310.method_1551().field_1690.field_1886.binding="key.mouse.left";AttackBindings246.input();event(0,1);shown();check(AdaptiveCps243.button()==0,"attack-left is recognized");event(0,0);shown();check(AdaptiveCps243.button()==2,"left release restores middle source");
  check(CpsDisplay.currentRightCps()==1,"HUD did not invent right clicks");
  System.out.println("PASS "+checks+" exact observer/counter/formatter checks: attack-bound override, smooth down/up, middle continues, ignored Use button: "+a[0]+" "+(multi?"multi-key":"vanilla"));
 }
}
