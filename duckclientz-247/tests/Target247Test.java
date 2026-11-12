import com.duckswords.modules.TargetHighlight;import com.duckswords.setting.*;import com.duckswords.render.*;import net.minecraft.*;import java.lang.reflect.*;import java.util.*;
public final class Target247Test {
 static int checks;static Object context;static class_310 client=class_310.method_1551();static class_238 box=new class_238(0,0,4,1,1,5);static TargetHighlight target=new TargetHighlight();
 static void ok(boolean v,String why){checks++;if(!v)throw new AssertionError(why);}
 static void draw(String method)throws Exception{Method m=Arrays.stream(TargetTop242.class.getMethods()).filter(x->x.getName().equals(method)).findFirst().orElseThrow();m.invoke(null,context,box,.2f,.4f,.8f,.5f,target);}
 static void reset(){Capture247.reset();TargetTopGeometry242.reset();client.field_1687.states.clear();}
 static void block(int x,int y,int z,class_238 shape){class_2680 state=new class_2680();state.boxes.add(shape);client.field_1687.states.put(new class_2338(x,y,z),state);}
 public static void main(String[] args)throws Exception {
  Class<?> type=Class.forName(args[0].equals("1.21.11")?"net.fabricmc.fabric.api.client.rendering.v1.world.WorldRenderContext":"net.fabricmc.fabric.api.client.rendering.v1.WorldRenderContext");
  context=Proxy.newProxyInstance(type.getClassLoader(),new Class[]{type},(o,m,a)->m.getName().equals("camera")?new class_4184():new class_11658());
  target.renderTop=new BooleanSetting("RenderTop","",true);target.onlyElytra=new BooleanSetting("Apenas elytra","",false);target.mode=new ModeSetting("Modo","","Box",new String[]{"Box","Filled","Both"});
  reset();draw("drawBox");ok(Capture247.lines.size()==12,"RenderTop draws all 12 edges over model in open space");ok(TargetTopGeometry242.boxes==0,"no duplicate normal box pass");
  reset();block(0,-1,4,new class_238(0,0,0,1,1,1));draw("drawBox");ok(Capture247.lines.size()==12,"ground touching feet does not erase bottom outline");
  reset();block(0,0,2,new class_238(0,0,0,1,1,1));draw("drawBox");ok(Capture247.lines.isEmpty(),"opaque wall hides all back-of-player edges");
  reset();block(0,0,6,new class_238(0,0,0,1,1,1));draw("drawBox");ok(Capture247.lines.size()==12,"block behind player leaves all edges visible");
  reset();block(0,0,2,new class_238(0,0,0,.2,1,1));box=new class_238(-1,.1,4,2,.9,5);draw("drawBox");ok(!Capture247.lines.isEmpty(),"partly obstructed target retains visible edge pieces");
  for(double[] line:Capture247.lines)for(double t:new double[]{.01,.5,.99}){double[] c={.5,.5,0},p={line[0]+(line[3]-line[0])*t,line[1]+(line[4]-line[1])*t,line[2]+(line[5]-line[2])*t};ok(!BlockShadow247Test.ray(c,p,new double[]{0,0,2,.2,1,3}),"emitted overlay piece may not cross wall shadow");}
  reset();target.renderTop.setValue(false);draw("drawBox");ok(Capture247.lines.isEmpty()&&TargetTopGeometry242.boxes==1,"RenderTop off uses unchanged native depth box");
  reset();target.renderTop.setValue(true);target.mode.setValue("Filled");draw("drawFilledBox");ok(Capture247.lines.size()==12&&TargetTopGeometry242.fills==1,"Filled keeps native fill and gains overlay outline");
  reset();target.mode.setValue("Both");draw("drawBox");draw("drawFilledBox");ok(Capture247.lines.size()==12&&TargetTopGeometry242.fills==1,"Both has one overlay contour and native fill");
  reset();box=new class_238(300,300,300,301,301,301);draw("drawBox");ok(Capture247.fallbacks==1&&Capture247.lines.isEmpty(),"outlier workload safely falls back to depth-tested path");
  class_1309 player=new class_1309();target.onlyElytra.setValue(true);ok(!TargetTop242.candidate(player,target),"elytra filter still excludes standing");player.flying=true;ok(TargetTop242.candidate(player,target),"elytra filter accepts gliding");player.visible=false;ok(!TargetTop242.render(player,target),"existing visibility filter retained");
  System.out.println("PASS "+checks+" final renderer checks: "+args[0]+" open model, wall/partial/behind, off/Filled/Both, fallback and elytra.");
 }
}
