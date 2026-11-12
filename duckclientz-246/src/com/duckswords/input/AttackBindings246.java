package com.duckswords.input;
import java.lang.reflect.Method;

/** Optional Multi Key Bindings integration; native and optional checks are cached between HUD frames. */
public final class AttackBindings246 {
 private static boolean cached,discovered;private static long checked;private static int mask;
 private static Method extras,key;
 private AttackBindings246(){}
 public static String primaryKey(){throw new IllegalStateException("native attack binding adapter");}
 public static String keyName(Object value){throw new IllegalStateException("native input key adapter");}
 public static boolean matches(int button){
  if(button<0||button>1)return false;
  long now=System.nanoTime();if(!cached||now-checked<0||now-checked>=250_000_000L)refresh(now);
  return (mask&(1<<button))!=0;
 }
 public static void input(){cached=false;}
 private static int bit(String name){return "key.mouse.left".equals(name)?1:"key.mouse.right".equals(name)?2:0;}
 private static void refresh(long now){
  checked=now;cached=true;mask=0;
  try{mask=bit(primaryKey());}catch(RuntimeException ignored){}
  if(!discovered){discovered=true;try{
   extras=Class.forName("us.kenny.MultiKeyBindingManager",false,AttackBindings246.class.getClassLoader()).getMethod("getKeyBindings",String.class);
   key=Class.forName("us.kenny.core.MultiKeyBinding",false,AttackBindings246.class.getClassLoader()).getMethod("getKey");
  }catch(ReflectiveOperationException|LinkageError ignored){extras=key=null;}}
  if(extras==null||key==null)return;
  try{Object value=extras.invoke(null,"key.attack");if(value instanceof Iterable<?> bindings)for(Object binding:bindings){if(binding!=null)mask|=bit(keyName(key.invoke(binding)));}}
  catch(ReflectiveOperationException|RuntimeException|LinkageError ignored){}
 }
}
