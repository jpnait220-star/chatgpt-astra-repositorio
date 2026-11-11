import com.duckswords.modules.TargetHighlight;import com.duckswords.setting.*;import com.duckswords.render.*;import com.duckswords.util.RenderUtil;import net.minecraft.*;import java.lang.reflect.*;
public final class TargetTop242Test{
 static int checks;static void ok(boolean b,String m){checks++;if(!b)throw new AssertionError(m);}
 static void draw(String name,TargetHighlight m,float a)throws Exception{
  Method f=java.util.Arrays.stream(TargetTop242.class.getDeclaredMethods()).filter(x->x.getName().equals(name)&&x.getParameterCount()==7).findFirst().orElseThrow();f.invoke(null,null,new class_238(),.2f,.4f,.8f,a,m);
 }
 static void reset(){RenderUtil.reset();TargetTopGeometry242.reset();}
 public static void main(String[] args)throws Exception{
  TargetHighlight m=new TargetHighlight();m.renderTop=new BooleanSetting("RenderTop","",true);m.onlyElytra=new BooleanSetting("Apenas elytra","",false);m.mode=new ModeSetting("Modo","","Box",new String[]{"Box","Filled","Both"});
  class_1309 target=new class_1309();
  ok(TargetTop242.allowed(true,m,target),"normal eligible target preserved with onlyElytra off");
  ok(!TargetTop242.allowed(false,m,target),"original selection rejection preserved");
  m.onlyElytra.setValue(true);ok(!TargetTop242.candidate(target,m),"elytra-only excludes standing target before nearest-target limit");
  target.flying=true;ok(TargetTop242.candidate(target,m),"elytra-only includes actively gliding target");
  ok(!TargetTop242.candidate(new class_1297(),m),"nonliving entity cannot pass elytra-only");
  target.alive=false;ok(!TargetTop242.candidate(target,m),"dead gliding target excluded");target.alive=true;
  target.visible=false;ok(!TargetTop242.render(target,m),"cleaner visibility preserved");target.visible=true;
  ok(TargetTop242.render(target,m),"visible gliding target renders");
  target.flying=false;ok(!TargetTop242.render(target,m),"landing immediately hides old fading elytra-only target");
  m.onlyElytra.setValue(false);ok(TargetTop242.render(target,m),"disabling elytra-only restores original rendering eligibility");
  reset();draw("drawBox",m,.5f);ok(TargetTopGeometry242.boxes==1&&RenderUtil.boxes==0,"RenderTop selects only dedicated foreground outline");
  m.renderTop.setValue(false);reset();draw("drawBox",m,.5f);ok(TargetTopGeometry242.boxes==0&&RenderUtil.boxes==1,"RenderTop off uses original box renderer");
  m.renderTop.setValue(true);m.mode.setValue("Both");reset();draw("drawBox",m,.5f);draw("drawFilledBox",m,.125f);
  ok(TargetTopGeometry242.boxes==1&&RenderUtil.fills==1,"Both mode keeps one foreground outline plus original fill");
  m.mode.setValue("Filled");reset();draw("drawFilledBox",m,.125f);ok(TargetTopGeometry242.boxes==1&&RenderUtil.fills==1,"Filled gains foreground outline without replacing volume");
  ok(Math.abs(TargetTopGeometry242.alpha-.5f)<.00001f,"filled-mode outline preserves original fade/color alpha");
  m.renderTop.setValue(false);reset();draw("drawFilledBox",m,.125f);ok(TargetTopGeometry242.boxes==0&&RenderUtil.fills==1,"Filled unchanged when RenderTop is off");
  System.out.println("PASS: "+checks+" TargetLight filtering/renderer-dispatch checks using fake game entities and consumers.");
 }
}
