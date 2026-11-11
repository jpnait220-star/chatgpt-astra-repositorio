package com.duckswords.connect;
import com.google.gson.*;import com.sun.net.httpserver.*;import javax.net.ssl.*;
import java.nio.file.*;import java.io.*;import java.lang.reflect.*;import java.net.*;import java.security.*;import java.util.*;import java.nio.charset.StandardCharsets;import java.util.concurrent.atomic.*;
public final class Transport241Test {
 static int checks;static Method request;static String key;static KeyPair pair;
 static void ok(boolean b,String m){checks++;if(!b)throw new AssertionError(m);}
 static String signed(String endpoint,boolean enabled)throws Exception{
  String payload="{\"protocol\":1,\"type\":\"duck-service-route\",\"revision\":1,\"enabled\":"+enabled+",\"endpoint\":\""+endpoint+"\"}";
  Signature s=Signature.getInstance("Ed25519");s.initSign(pair.getPrivate());s.update(payload.getBytes(StandardCharsets.UTF_8));
  return "{\"payload\":\""+Base64.getEncoder().encodeToString(payload.getBytes(StandardCharsets.UTF_8))+"\",\"signature\":\""+Base64.getEncoder().encodeToString(s.sign())+"\"}";
 }
 static String call(String url,String body)throws Exception{
  try{return (String)request.invoke(null,url,body);}catch(InvocationTargetException e){if(e.getCause()instanceof Exception x)throw x;throw e;}
 }
 static void resolver(String body)throws Exception{
  var resolver=new ServiceRoute241.Resolver(key,null,()->body,System::nanoTime);
  Field field=ServiceRoute241.class.getDeclaredField("resolver");field.setAccessible(true);field.set(null,resolver);
 }
 public static void main(String[] args)throws Exception{
  pair=KeyPairGenerator.getInstance("Ed25519").generateKeyPair();key=Base64.getEncoder().encodeToString(pair.getPublic().getEncoded());
  KeyStore store=KeyStore.getInstance("PKCS12");try(InputStream in=Files.newInputStream(Path.of(args[0]))){store.load(in,"testonly".toCharArray());}
  KeyManagerFactory keys=KeyManagerFactory.getInstance(KeyManagerFactory.getDefaultAlgorithm());keys.init(store,"testonly".toCharArray());
  SSLContext tls=SSLContext.getInstance("TLS");tls.init(keys.getKeyManagers(),null,null);
  HttpsServer server=HttpsServer.create(new InetSocketAddress("127.0.0.1",0),0);server.setHttpsConfigurator(new HttpsConfigurator(tls));AtomicInteger count=new AtomicInteger();
  server.createContext("/",exchange->{
   count.incrementAndGet();String path=exchange.getRequestURI().getPath();String result;
   if(path.equals("/profile")){
    String body=new String(exchange.getRequestBody().readAllBytes(),StandardCharsets.UTF_8);
    result=body.contains("duckMask")&&exchange.getRequestMethod().equals("POST")?"{\"ok\":true}":"{\"ok\":false}";
   }else if(path.equals("/community"))result="{\"token\":\"11111111-2222-4333-8444-555555555555\",\"online\":1,\"messages\":[]}";
   else if(path.equals("/profiles"))result="{\"11111111-2222-4333-8444-555555555555\":[\"duckMask\"]}";
   else if(path.equals("/too-large"))result="x".repeat(65537);
   else result="{\"status\":\"online\"}";
   byte[] bytes=result.getBytes(StandardCharsets.UTF_8);exchange.getResponseHeaders().set("Content-Type","application/json");exchange.sendResponseHeaders(200,bytes.length);exchange.getResponseBody().write(bytes);exchange.close();
  });server.start();
  try{
   String base="https://duck-migration.test:"+server.getAddress().getPort();
   request=Class.forName("com.duckswords.connect.TransportProbe241").getMethod("request",String.class,String.class);
   resolver(signed(base,true));
   ok(JsonParser.parseString(call("https://duck-connect.vercel.app/profile","{\"uuid\":\"11111111-2222-4333-8444-555555555555\",\"cosmetics\":[\"duckMask\"]}")).getAsJsonObject().get("ok").getAsBoolean(),"old profile call rerouted to verified HTTPS server");
   ok(JsonParser.parseString(call("https://duck-connect.vercel.app/profiles?ids=11111111-2222-4333-8444-555555555555",null)).getAsJsonObject().size()==1,"read route/query preserved");
   ok(JsonParser.parseString(call("https://duck-connect.vercel.app/community","{}")).getAsJsonObject().get("online").getAsInt()==1,"community rerouted to same origin");
   ok(count.get()==3,"no extra API requests generated");
   int before=count.get();resolver(signed("",false));boolean pending=false;
   try{call("https://duck-connect.vercel.app/chat","{}");}catch(IOException e){pending=true;}
   ok(pending&&count.get()==before,"pending route makes no API connection");
   resolver(signed(base,true));boolean hostnameRejected=false;
   try{call("https://localhost:"+server.getAddress().getPort()+"/health",null);}catch(SSLException e){hostnameRejected=true;}
   ok(hostnameRejected,"original certificate/hostname verification remains enforced");
   boolean largeRejected=false;try{call(base+"/too-large",null);}catch(IOException e){largeRejected=true;}
   ok(largeRejected,"original response size cap preserved");
   System.out.println("PASS: "+checks+" real HTTPS transport checks from exact patched request bytecode; trusted test CA isolated to this JVM.");
  }finally{server.stop(0);}
 }
}
