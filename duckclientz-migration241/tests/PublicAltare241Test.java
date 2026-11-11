import com.duckswords.connect.ServiceRoute241;import com.google.gson.*;
import java.nio.file.*;import java.lang.reflect.*;import java.util.*;
public final class PublicAltare241Test{
 static Method transport;
 static String call(String u,String b)throws Exception{try{return(String)transport.invoke(null,u,b);}catch(InvocationTargetException e){if(e.getCause()instanceof Exception x)throw x;throw e;}}
 public static void main(String[] args)throws Exception{
  String envelope=Files.readString(Path.of(args[0]));var doc=ServiceRoute241.verify(envelope,ServiceRoute241.KEY);
  if(!doc.enabled()||!doc.endpoint().equals("https://duckconnect.go.altare.global"))throw new AssertionError("Invalid activation");
  var resolver=new ServiceRoute241.Resolver(ServiceRoute241.KEY,null,()->envelope,System::nanoTime);
  Field f=ServiceRoute241.class.getDeclaredField("resolver");f.setAccessible(true);f.set(null,resolver);
  transport=Class.forName("com.duckswords.connect.TransportProbe241").getMethod("request",String.class,String.class);
  String id=UUID.randomUUID().toString(),old="https://duck-connect.vercel.app";
  String health=call(old+"/health",null);if(!JsonParser.parseString(health).getAsJsonObject().get("status").getAsString().equals("online"))throw new AssertionError("Health failed");
  try{
   String ack=call(old+"/profile","{\"uuid\":\""+id+"\",\"cosmetics\":[\"duckMask\"]}");
   if(!JsonParser.parseString(ack).getAsJsonObject().get("ok").getAsBoolean())throw new AssertionError("Publish failed");
   JsonObject response=JsonParser.parseString(call(old+"/profiles?ids="+id,null)).getAsJsonObject();
   if(!response.getAsJsonArray(id).get(0).getAsString().equals("duckMask"))throw new AssertionError("Lookup failed");
   System.out.println("PASS real client HTTPS transport against public Altare: signed activation, health, cosmetic publication and lookup.");
  }finally{call(old+"/profile","{\"uuid\":\""+id+"\",\"cosmetics\":[]}");}
 }
}
