import com.duckswords.input.*;import net.minecraft.*;
public final class VanillaBindings246Test {public static void main(String[] a){
 class_310.method_1551().field_1690.field_1886.binding="key.mouse.right";AttackBindings246.input();if(!AttackBindings246.matches(1)||AttackBindings246.matches(0))throw new AssertionError();
 AdaptiveCps243.mouse(1,1,0);if(AdaptiveCps243.current(2,3,20,0)!=3)throw new AssertionError();AdaptiveCps243.mouse(1,0,1);if(AdaptiveCps243.current(2,3,20,1)!=20)throw new AssertionError();
 class_310.method_1551().field_1690.field_1886.binding="key.keyboard.r";AttackBindings246.input();if(AttackBindings246.matches(1)||AttackBindings246.matches(0))throw new AssertionError();
 System.out.println("PASS optional Multi Key Bindings absent: native attack binding and release work without dependency.");
}}
