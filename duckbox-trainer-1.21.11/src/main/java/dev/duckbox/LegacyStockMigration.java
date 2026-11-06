package dev.duckbox;

import com.google.gson.*;
import com.mojang.serialization.Dynamic;
import net.minecraft.SharedConstants;
import net.minecraft.datafixer.*;
import net.minecraft.item.ItemStack;
import net.minecraft.nbt.*;
import net.minecraft.registry.RegistryWrapper;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.storage.*;
import net.minecraft.util.ErrorReporter;
import java.util.*;

/** Upgrade custom inventories explicitly: vanilla DFU does not recognize duckbox block entities. */
public final class LegacyStockMigration {
  private static final String NAME="minecraft:custom_name", ATTR="minecraft:attribute_modifiers";
  private static final class Catalog {
    static final Map<String,NbtCompound> ITEMS=load();
    private static Map<String,NbtCompound> load(){
      var result=new HashMap<String,NbtCompound>();var ambiguous=new HashSet<String>();
      try(var stream=LegacyStockMigration.class.getResourceAsStream("/duckbox/legacy-stock-items.json")){
        if(stream==null)return Map.of();
        for(var element:JsonParser.parseReader(new java.io.InputStreamReader(stream,java.nio.charset.StandardCharsets.UTF_8)).getAsJsonArray()){
          var item=StringNbtReader.readCompound(element.getAsString());String key=key(item);
          if(key.isEmpty())continue;
          var previous=result.putIfAbsent(key,item);
          if(previous!=null&&!previous.getCompoundOrEmpty("components").equals(item.getCompoundOrEmpty("components")))ambiguous.add(key);
        }
        ambiguous.forEach(result::remove);return Map.copyOf(result);
      }catch(Exception error){throw new IllegalStateException("Catalogo de migracao de itens invalido",error);}
    }
  }
  private static String key(NbtCompound item){
    String name=item.getCompoundOrEmpty("components").getString(NAME,"");
    return name.stripLeading().startsWith("{")?item.getString("id","")+"|"+name:"";
  }
  public static NbtCompound upgrade(NbtCompound raw){
    var c=raw.getCompoundOrEmpty("components");
    boolean oldName=c.get(NAME) instanceof NbtString && c.getString(NAME,"").stripLeading().startsWith("{");
    boolean oldAttributes=c.get(ATTR) instanceof NbtCompound;
    boolean oldEnchantments=c.getCompoundOrEmpty("minecraft:enchantments").contains("levels");
    if(!oldName&&!oldAttributes&&!oldEnchantments)return raw;
    var input=raw.copy();
    // beta.0.3.30 could save a literal JSON name after dropping invalid old attribute/enchantment wrappers.
    // Restore only exact named catalog items from the supplied map, never arbitrary custom items.
    var reference=Catalog.ITEMS.get(key(raw));
    if(reference!=null&&oldName){
      var components=input.getCompoundOrEmpty("components");var expected=reference.getCompoundOrEmpty("components");
      for(String component:List.of(ATTR,"minecraft:enchantments","minecraft:profile","minecraft:potion_contents","minecraft:max_stack_size","minecraft:enchantment_glint_override")){
        var existing=components.get(component);
        if(expected.contains(component)&&(existing==null||existing instanceof NbtList list&&list.isEmpty()
            ||existing instanceof NbtCompound compound&&compound.isEmpty())){components.remove("!"+component);components.put(component,expected.get(component).copy());}
      }
      input.put("components",components);
    }
    var currentComponents=new HashMap<String,NbtElement>();
    var before=input.getCompoundOrEmpty("components");
    if(before.get(ATTR) instanceof NbtList)currentComponents.put(ATTR,before.get(ATTR).copy());
    for(String id:List.of("minecraft:enchantments","minecraft:stored_enchantments"))
      if(before.get(id) instanceof NbtCompound value&&!value.contains("levels"))currentComponents.put(id,value.copy());
    if(before.get(NAME) instanceof NbtCompound||before.get(NAME) instanceof NbtList)currentComponents.put(NAME,before.get(NAME).copy());
    var fixed=Schemas.getFixer().update(TypeReferences.ITEM_STACK,new Dynamic<>(NbtOps.INSTANCE,input),4189,
        SharedConstants.getGameVersion().dataVersion().id()).getValue();
    if(!(fixed instanceof NbtCompound result))throw new IllegalStateException("Migracao nao retornou um item");
    var after=result.getCompoundOrEmpty("components");currentComponents.forEach(after::put);result.put("components",after);
    if(raw.contains("Slot"))result.put("Slot",raw.get("Slot").copy());
    return result;
  }
  public static ReadView inventoryView(ReadView original){
    var raw=original.read("Items",NbtCompound.CODEC.listOf()).orElse(List.of());
    var list=new NbtList();boolean changed=false;
    for(var item:raw){var updated=upgrade(item);list.add(updated);changed|=updated!=item;}
    if(!changed)return original;
    var root=new NbtCompound();root.put("Items",list);
    var replacement=NbtReadView.create(ErrorReporter.EMPTY,original.getRegistries(),root);
    return (ReadView)java.lang.reflect.Proxy.newProxyInstance(ReadView.class.getClassLoader(),new Class<?>[]{ReadView.class},
        (proxy,method,args)->{
          try{return method.invoke(args!=null&&args.length>0&&"Items".equals(args[0])?replacement:original,args);}
          catch(java.lang.reflect.InvocationTargetException e){throw e.getCause();}
        });
  }
  public static ItemStack repairSavedCopy(ItemStack stack,RegistryWrapper.WrapperLookup registries){
    if(stack.isEmpty()||!stack.getName().getString().stripLeading().startsWith("{"))return stack;
    var ops=registries.getOps(NbtOps.INSTANCE);
    var original=(NbtCompound)ItemStack.CODEC.encodeStart(ops,stack).getOrThrow();
    if(!Catalog.ITEMS.containsKey(key(original)))return stack;
    return ItemStack.CODEC.parse(ops,upgrade(original)).getOrThrow();
  }
  public static void repairPlayer(ServerPlayerEntity player){
    boolean changed=false;
    for(int slot=0;slot<player.getInventory().size();slot++){
      var original=player.getInventory().getStack(slot);var repaired=repairSavedCopy(original,player.getRegistryManager());
      if(repaired!=original){player.getInventory().setStack(slot,repaired);changed=true;}
    }
    if(changed){player.getInventory().markDirty();player.currentScreenHandler.sendContentUpdates();}
  }
}
