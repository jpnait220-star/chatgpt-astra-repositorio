import com.duckswords.modules.ElytraFeature;
public class Elytra248Test {public static void main(String[] args)throws Exception{
 ElytraFeature feature=new ElytraFeature();if(feature.getSettings().size()!=3)throw new AssertionError("expected remaining 3 options");
 if(feature.physics==null||feature.disableVisual==null||feature.leanMultiplier==null)throw new AssertionError("remaining options lost");
 if(feature.getSettings().stream().anyMatch(s->s.getName().toLowerCase().contains("bug")))throw new AssertionError("bugfix still visible");
 try{ElytraFeature.class.getDeclaredField("bugFix");throw new AssertionError("removed field still present");}catch(NoSuchFieldException expected){}
 System.out.println("PASS real Elytra constructor: Physics/visual/lean remain, Bug Fix field and menu entry absent: "+args[0]);
}}
