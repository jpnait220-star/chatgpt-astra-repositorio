package com.duckswords.connect;
import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.security.*;import java.util.*;import java.util.concurrent.atomic.*;import com.google.gson.*;
public final class ServiceRoute241Test {
 static int checks;static KeyPair pair;static String key;
 static void ok(boolean v,String m){checks++;if(!v)throw new AssertionError(m);}
 static String signed(long revision,boolean enabled,String endpoint)throws Exception{
  JsonObject root=new JsonObject();root.addProperty("protocol",1);root.addProperty("type","duck-service-route");root.addProperty("revision",revision);root.addProperty("enabled",enabled);root.addProperty("endpoint",endpoint);
  byte[] body=root.toString().getBytes(StandardCharsets.UTF_8);Signature s=Signature.getInstance("Ed25519");s.initSign(pair.getPrivate());s.update(body);
  JsonObject out=new JsonObject();out.addProperty("payload",Base64.getEncoder().encodeToString(body));out.addProperty("signature",Base64.getEncoder().encodeToString(s.sign()));return out.toString();
 }
 interface Work{void run()throws Exception;}
 static void fails(Work f,String m)throws Exception{boolean rejected=false;try{f.run();}catch(Exception e){rejected=true;}ok(rejected,m);}
 public static void main(String[] args)throws Exception{
  pair=KeyPairGenerator.getInstance("Ed25519").generateKeyPair();key=Base64.getEncoder().encodeToString(pair.getPublic().getEncoded());
  String good=signed(1,true,"https://duck.example/");
  ok(ServiceRoute241.verify(good,key).endpoint().equals("https://duck.example"),"valid signed root normalized");
  ok(!ServiceRoute241.verify(signed(2,false,""),key).enabled(),"explicit disabled state");
  JsonObject tampered=JsonParser.parseString(good).getAsJsonObject();tampered.addProperty("payload",Base64.getEncoder().encodeToString("{}".getBytes(StandardCharsets.UTF_8)));
  fails(()->ServiceRoute241.verify(tampered.toString(),key),"tamper rejected before payload interpretation");
  String other=Base64.getEncoder().encodeToString(KeyPairGenerator.getInstance("Ed25519").generateKeyPair().getPublic().getEncoded());
  fails(()->ServiceRoute241.verify(good,other),"foreign signing key rejected");
  fails(()->ServiceRoute241.verify("x".repeat(65537),key),"oversized envelope rejected");
  for(String url:List.of("http://duck.example","https://localhost","https://127.0.0.1","https://192.168.1.1","https://duck.local","https://duck.example/api","https://user:pass@duck.example","https://duck.example?token=x","https://duck.example#x","https://duck.example:0"))fails(()->ServiceRoute241.verify(signed(2,true,url),key),"reject unsafe root: "+url);
  fails(()->ServiceRoute241.verify(signed(2,false,"https://duck.example"),key),"disabled route must not contain hidden destination");
  Path dir=Files.createTempDirectory("duck-route-test-");Path file=dir.resolve("route.json");
  try{
   AtomicLong clock=new AtomicLong(-1000);AtomicInteger calls=new AtomicInteger();AtomicReference<String> remote=new AtomicReference<>(good);
   ServiceRoute241.Source source=()->{calls.incrementAndGet();String s=remote.get();if(s==null)throw new java.io.IOException("offline");return s;};
   var resolver=new ServiceRoute241.Resolver(key,file,source,clock::get);
   ok(resolver.root().equals("https://duck.example")&&calls.get()==1,"first read also works with negative nanoTime");
   for(int i=0;i<50;i++)resolver.root();ok(calls.get()==1,"request threads share cached config");
   ok(Files.exists(file),"verified cache persisted");
   remote.set(null);clock.addAndGet(601_000_000_000L);ok(resolver.root().equals("https://duck.example"),"last good endpoint survives bootstrap outage");
   int before=calls.get();resolver.root();ok(calls.get()==before,"failure backoff prevents request spam");
   var restarted=new ServiceRoute241.Resolver(key,file,()->{throw new java.io.IOException("offline");},clock::get);
   ok(restarted.root().equals("https://duck.example"),"verified cache works after restarting without GitHub");
   remote.set(signed(2,false,""));clock.addAndGet(61_000_000_000L);fails(resolver::root,"signed pending state stops API access");
   before=calls.get();fails(resolver::root,"pending state remains stopped");ok(calls.get()==before,"pending state does not refetch on every request");
   remote.set(signed(3,true,"https://new-duck.example"));clock.addAndGet(61_000_000_000L);ok(resolver.root().equals("https://new-duck.example"),"service domain changes without mod reinstall");
   remote.set(good);clock.addAndGet(601_000_000_000L);ok(resolver.root().equals("https://new-duck.example"),"signed rollback cannot replace newer cached config");
   remote.set(signed(3,true,"https://conflict.example"));clock.addAndGet(61_000_000_000L);ok(resolver.root().equals("https://new-duck.example"),"same revision conflicting payload rejected");
   Files.writeString(file,tampered.toString());var corrupt=new ServiceRoute241.Resolver(key,file,()->{throw new java.io.IOException("offline");},clock::get);fails(corrupt::root,"corrupt cached configuration fails closed");
  }finally{try(var files=Files.walk(dir)){for(Path p:files.sorted(Comparator.reverseOrder()).toList())Files.delete(p);}}
  System.out.println("PASS: "+checks+" signed service-routing checks; no game/render loop or production requests used.");
 }
}
