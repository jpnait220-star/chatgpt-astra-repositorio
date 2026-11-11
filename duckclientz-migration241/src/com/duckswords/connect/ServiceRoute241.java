package com.duckswords.connect;

import com.google.gson.*;
import net.fabricmc.loader.api.FabricLoader;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.*;
import java.security.spec.X509EncodedKeySpec;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.function.LongSupplier;

/** Signed service discovery on existing I/O workers only. Never invoked by rendering. */
public final class ServiceRoute241 {
    public static final String KEY="MCowBQYDK2VwAyEAsGruKukaAwPgI5PChxvclKUNfyoDFx0efRpHZF8355o=";
    public static final String CONFIG="https://raw.githubusercontent.com/jpnait220-star/chatgpt-astra-repositorio/asasa/downloads/DuckClientZ-service.json";
    private static final String OLD="https://duck-connect.vercel.app";
    private static volatile Resolver resolver;
    private static final Set<String> PATHS=Set.of("/health","/profile","/profiles","/community","/chat","/announcements","/announcement-challenge","/announce");
    private ServiceRoute241(){}
    public static String translate(String url)throws IOException {
        if(!url.equals(OLD)&&!url.startsWith(OLD+"/"))return url;
        String suffix=url.substring(OLD.length());
        String path=suffix.split("\\?",2)[0];
        if(!PATHS.contains(path)||suffix.indexOf('#')>=0||suffix.indexOf('\r')>=0||suffix.indexOf('\n')>=0)throw new IOException("Rota Duck invalida");
        Resolver current=resolver;
        if(current==null)synchronized(ServiceRoute241.class){
            current=resolver;
            if(current==null){
                Path file=FabricLoader.getInstance().getConfigDir().resolve("duckclientz").resolve("shared").resolve("service-route.json");
                resolver=current=new Resolver(KEY,file,()->fetch(CONFIG),System::nanoTime);
            }
        }
        return current.root()+suffix;
    }
    public record Document(long revision,boolean enabled,String endpoint){}
    @FunctionalInterface public interface Source {String read()throws Exception;}
    public static Document verify(String envelope,String publicKey)throws Exception {
        if(envelope==null||envelope.length()>65536)throw new SecurityException("Route envelope too large");
        JsonObject outer=JsonParser.parseString(envelope).getAsJsonObject();
        byte[] body=Base64.getDecoder().decode(outer.get("payload").getAsString());
        byte[] sig=Base64.getDecoder().decode(outer.get("signature").getAsString());
        if(body.length>32768||sig.length!=64)throw new SecurityException("Invalid route size");
        PublicKey key=KeyFactory.getInstance("Ed25519").generatePublic(new X509EncodedKeySpec(Base64.getDecoder().decode(publicKey)));
        Signature verifier=Signature.getInstance("Ed25519");verifier.initVerify(key);verifier.update(body);
        if(!verifier.verify(sig))throw new SecurityException("Invalid route signature");
        JsonObject root=JsonParser.parseString(new String(body,StandardCharsets.UTF_8)).getAsJsonObject();
        if(root.get("protocol").getAsInt()!=1||!"duck-service-route".equals(root.get("type").getAsString()))throw new SecurityException("Invalid route protocol");
        long revision=root.get("revision").getAsLong();if(revision<1)throw new SecurityException("Invalid revision");
        JsonPrimitive enabled=root.getAsJsonPrimitive("enabled");if(!enabled.isBoolean())throw new SecurityException("Invalid enabled field");
        String endpoint=root.get("endpoint").getAsString();
        if(!enabled.getAsBoolean()){
            if(!endpoint.isEmpty())throw new SecurityException("Disabled route must be empty");
            return new Document(revision,false,"");
        }
        return new Document(revision,true,validateEndpoint(endpoint));
    }
    public static String validateEndpoint(String value){
        if(value==null||value.length()>512)throw new SecurityException("Invalid endpoint");
        URI uri=URI.create(value);String host=uri.getHost();String path=uri.getRawPath();
        if(!"https".equals(uri.getScheme())||host==null||uri.getRawUserInfo()!=null||uri.getRawQuery()!=null||uri.getRawFragment()!=null||!(path==null||path.isEmpty()||path.equals("/")))throw new SecurityException("HTTPS service root required");
        host=host.toLowerCase(Locale.ROOT);
        if(!host.matches("[a-z0-9](?:[a-z0-9.-]{0,251}[a-z0-9])?")||!host.contains(".")||host.matches("[0-9.]+")||host.endsWith(".local")||host.endsWith(".localhost")||host.endsWith(".internal")||uri.getPort()==0||uri.getPort()>65535)throw new SecurityException("Public service hostname required");
        return value.endsWith("/")?value.substring(0,value.length()-1):value;
    }
    private static String fetch(String url)throws IOException {
        HttpURLConnection c=(HttpURLConnection)URI.create(url).toURL().openConnection();
        c.setConnectTimeout(2500);c.setReadTimeout(3500);c.setInstanceFollowRedirects(false);c.setUseCaches(false);
        c.setRequestProperty("User-Agent","DuckClientZ-Service/241");c.setRequestProperty("Accept","application/json");
        try{
            if(c.getResponseCode()!=200)throw new IOException("Service configuration unavailable");
            try(InputStream in=c.getInputStream()){
                byte[] bytes=in.readNBytes(65537);if(bytes.length>65536)throw new IOException("Service configuration too large");
                return new String(bytes,StandardCharsets.UTF_8);
            }
        }finally{c.disconnect();}
    }
    public static final class Resolver {
        private final String key;private final Path file;private final Source source;private final LongSupplier clock;
        private Document current;private boolean loaded,scheduled;private long next;private int failures;
        public Resolver(String key,Path file,Source source,LongSupplier clock){this.key=key;this.file=file;this.source=source;this.clock=clock;}
        public synchronized String root()throws IOException {
            if(!loaded){loaded=true;try{if(file!=null&&Files.size(file)<=65536)current=verify(Files.readString(file),key);}catch(Exception ignored){}}
            long now=clock.getAsLong();
            if(!scheduled||now-next>=0){
                scheduled=true;
                // Reserve the next attempt before any I/O; callers are existing worker threads.
                next=now+TimeUnit.SECONDS.toNanos(60);
                try{
                    String envelope=source.read();Document incoming=verify(envelope,key);
                    if(current!=null&&(incoming.revision()<current.revision()||(incoming.revision()==current.revision()&&!incoming.equals(current))))throw new SecurityException("Route rollback/conflict");
                    current=incoming;failures=0;
                    next=now+TimeUnit.SECONDS.toNanos(current.enabled()?600:60);
                    if(file!=null)try{save(file,envelope);}catch(IOException ignored){}
                }catch(Exception error){
                    failures=Math.min(failures+1,5);next=now+TimeUnit.SECONDS.toNanos(Math.min(900,60L<<(failures-1)));
                }
            }
            if(current==null||!current.enabled())throw new IOException("Servico Duck aguardando configuracao");
            return current.endpoint();
        }
        private static void save(Path file,String text)throws IOException {
            Files.createDirectories(file.getParent());Path temp=Files.createTempFile(file.getParent(),"route-",".tmp");
            try{
                Files.writeString(temp,text,StandardCharsets.UTF_8);
                try{Files.move(temp,file,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}
                catch(AtomicMoveNotSupportedException e){Files.move(temp,file,StandardCopyOption.REPLACE_EXISTING);}
            }finally{Files.deleteIfExists(temp);}
        }
    }
}
