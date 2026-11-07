package dev.duckzin.hidenick;

import java.lang.reflect.Proxy;
import java.nio.file.Files;
import java.util.*;
import me.neznamy.tab.api.TabPlayer;
import me.neznamy.tab.api.nametag.NameTagManager;

public final class PluginTests {
    static int checks;
    static void check(boolean value, String message) { checks++; if (!value) throw new AssertionError(message); }
    public static void main(String[] args) throws Exception {
        check(ColorCodes.lastColor("&cVIP &l").orElseThrow().equals("§c"), "prefix color ignores styles");
        check(ColorCodes.lastColor("&#Ff0000").orElseThrow().equals("§x§f§f§0§0§0§0"), "RGB normalization");
        check(ColorCodes.lastColor("§x§1§2§3§4§5§6").orElseThrow().equals("§x§1§2§3§4§5§6"), "native RGB preserved");
        var text=ColorCodes.label("&c");
        check(text.equals("§c§kXXXXXXXXX§r"), "exactly nine obfuscated characters");
        var policy=new ColorPolicy(Map.of("vip",new ColorPolicy.Rule("&6",null),"admin",new ColorPolicy.Rule("&c",null)),"&7",true);
        check(policy.resolve(List.of(new ColorPolicy.Group("vip",1,true),new ColorPolicy.Group("admin",10,false)),null).equals("§c"), "inherited highest weight");
        check(policy.resolve(List.of(new ColorPolicy.Group("vip",10,true),new ColorPolicy.Group("admin",10,false)),null).equals("§6"), "primary group tie break");
        check(policy.resolve(List.of(),"&4[Owner] &l").equals("§4"), "unconfigured rank uses LP prefix color");
        check(policy.resolve(List.of(),null).equals("§7"), "no rank fallback");
        var priority=new ColorPolicy(Map.of("vip",new ColorPolicy.Rule("&6",100),"admin",new ColorPolicy.Rule("&c",null)),"&7",false);
        check(priority.resolve(List.of(new ColorPolicy.Group("vip",0,false),new ColorPolicy.Group("admin",10,true)),null).equals("§6"), "explicit priority");
        check(ColorCodes.tagColor("&7[&9Midia&7] &r").orElseThrow().equals("§9"), "tag color ignores grey brackets and reset");
        check(ColorCodes.tagColor("&#123456&lMídia &7").orElseThrow().equals("§x§1§2§3§4§5§6"), "RGB tag with trailing chat color");
        check(policy.resolve(List.of(new ColorPolicy.Group("admin",10,true)),"&9Midia &7").equals("§9"), "active tag overrides inherited rank rule");
        var disabled=new ColorPolicy(Map.of("admin",new ColorPolicy.Rule("&c",100)),"&f",true,false);
        check(disabled.resolve(List.of(new ColorPolicy.Group("admin",10,true)),"&9Midia").equals("§f"), "disabled rank color ignores prefix and group");
        var folder=Files.createTempDirectory("ducknick-test-");
        try {
            var store=new HiddenStore(folder.resolve("players.yml"));
            check(store.load().isEmpty(), "new preferences empty");
            var ids=Set.of(UUID.randomUUID(),UUID.randomUUID());store.save(ids);
            check(store.load().equals(ids), "preference roundtrip");
            store.save(Set.of());check(store.load().isEmpty(),"restore persists");
        } finally { try(var paths=Files.walk(folder)){ for(var path:paths.sorted(Comparator.reverseOrder()).toList())Files.delete(path); } }
        testLease(false,true); testLease(true,true); testLease(false,false);
        System.out.println("PASS: "+checks+" checks (colors, permissions state storage, TAB nametag lifecycle). No client rendering test was performed.");
    }
    static void testLease(boolean initiallyHidden,boolean loaded) {
        boolean[] hidden={initiallyHidden}; int[] shows={0};
        var player=(TabPlayer)Proxy.newProxyInstance(TabPlayer.class.getClassLoader(),new Class[]{TabPlayer.class},(p,m,a)-> {
            if(m.getName().equals("isLoaded"))return loaded;
            throw new AssertionError("Unexpected TAB player call: "+m.getName());
        });
        var manager=(NameTagManager)Proxy.newProxyInstance(NameTagManager.class.getClassLoader(),new Class[]{NameTagManager.class},(p,m,a)-> {
            switch(m.getName()) {
                case "hasHiddenNameTag": return hidden[0];
                case "hideNameTag": hidden[0]=true; return null;
                case "showNameTag": hidden[0]=false; shows[0]++; return null;
                default: throw new AssertionError("Unexpected TAB mutation: "+m.getName());
            }
        });
        var lease=new NametagLease(manager,player);
        check(hidden[0],"TAB overhead hidden");
        hidden[0]=false;lease.enforce();check(hidden[0],"TAB refresh rehidden");
        lease.close();lease.close();check(shows[0]==(!initiallyHidden&&loaded?1:0),"restores once only when owned and loaded");
    }
}
