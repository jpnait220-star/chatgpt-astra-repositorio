package dev.duckbox;
import com.google.gson.*;
import java.util.*;
import net.minecraft.item.*;
import net.minecraft.nbt.*;
import net.minecraft.registry.*;
import net.minecraft.entity.attribute.*;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.enchantment.*;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.Identifier;
public final class Kits {
 public static List<ItemStack> capture(ServerPlayerEntity p){var a=new ArrayList<ItemStack>();for(int i=0;i<41;i++)a.add(p.getInventory().getStack(i).copy());return a;}
 public static void give(ServerPlayerEntity p,List<ItemStack> kit){p.stopUsingItem();p.getInventory().clear();for(int i=0;i<Math.min(41,kit.size());i++)p.getInventory().setStack(i,kit.get(i).copy());p.getInventory().selectedSlot=0;p.getInventory().markDirty();p.currentScreenHandler.sendContentUpdates();p.networkHandler.sendPacket(new net.minecraft.network.packet.s2c.play.UpdateSelectedSlotS2CPacket(0));}
 public static JsonArray encode(ServerPlayerEntity p,List<ItemStack> kit){var a=new JsonArray();for(var s:kit){if(s.isEmpty())a.add(JsonNull.INSTANCE);else {var e=new JsonObject();e.addProperty("snbt",s.writeNbt(new NbtCompound()).toString());a.add(e);}}return a;}
 public static List<ItemStack> decode(ServerPlayerEntity p,JsonArray a){var out=new ArrayList<ItemStack>();for(var e:a){if(e.isJsonNull())out.add(ItemStack.EMPTY);else try{out.add(ItemStack.fromNbt(StringNbtReader.parse(e.getAsJsonObject().get("snbt").getAsString())));}catch(Exception ex){throw new IllegalArgumentException("Kit invalido para1.20.1",ex);}}return out;}
 public static boolean isTotem(ItemStack s){return s.isOf(Items.TOTEM_OF_UNDYING);}
 public static boolean isCharm(ItemStack s){return s.isOf(Items.YELLOW_DYE);}
 private static UUID id(String key){return UUID.nameUUIDFromBytes(("duckbox:"+key).getBytes(java.nio.charset.StandardCharsets.UTF_8));}
 public static void add(ItemStack s,EntityAttribute attr,String name,double value,EquipmentSlot slot){
  var list=s.getOrCreateNbt().getList("AttributeModifiers",10);var uid=id(name);
  for(int i=list.size()-1;i>=0;i--)if(list.getCompound(i).containsUuid("UUID")&&list.getCompound(i).getUuid("UUID").equals(uid))list.remove(i);
  var n=new NbtCompound();n.putString("AttributeName",Registries.ATTRIBUTE.getId(attr).toString());n.putString("Name","duckbox:"+name);n.putUuid("UUID",uid);n.putDouble("Amount",value);n.putInt("Operation",0);if(slot!=null)n.putString("Slot",slot.getName());list.add(n);s.getOrCreateNbt().put("AttributeModifiers",list);
 }
 public static void attribute(ServerPlayerEntity p,String key,double amount,AttributeModifierSlot slot){if(p.getMainHandStack().isEmpty())throw new IllegalArgumentException("Segure um item.");var id=new Identifier(key.contains(":")?key:"minecraft:generic."+key);if(!Registries.ATTRIBUTE.containsId(id))throw new IllegalArgumentException("Atributo desconhecido.");add(p.getMainHandStack(),Registries.ATTRIBUTE.get(id),slot.asString()+"/"+id.getPath(),amount,slot==AttributeModifierSlot.ANY?null:slot.nativeSlot());p.getInventory().markDirty();}
 private static boolean ours(ItemStack s){return s.hasNbt()&&s.getNbt().getList("AttributeModifiers",10).stream().anyMatch(e->e instanceof NbtCompound n&&n.getString("Name").equals("duckbox:mainhand/attack_damage"));}
 public static boolean repairNormalKit(List<ItemStack> kit){boolean changed=false;for(var s:kit)if(s.isOf(Items.GOLDEN_SWORD)&&ours(s)){var list=s.getNbt().getList("AttributeModifiers",10);boolean configured=list.stream().anyMatch(e->e instanceof NbtCompound n&&n.getString("AttributeName").equals("minecraft:generic.attack_speed"));if(!configured){add(s,EntityAttributes.GENERIC_ATTACK_SPEED,"mainhand/attack_speed",-2.4,EquipmentSlot.MAINHAND);changed=true;}}return changed;}
 public static boolean upgradeTrainingSword(DynamicRegistryManager registry,List<ItemStack> kit){boolean changed=false;for(var s:kit)if(s.isOf(Items.GOLDEN_SWORD)&&ours(s)){add(s,EntityAttributes.GENERIC_ATTACK_DAMAGE,"mainhand/attack_damage",25,EquipmentSlot.MAINHAND);if(EnchantmentHelper.getLevel(Enchantments.SHARPNESS,s)!=58){var m=new HashMap<>(EnchantmentHelper.get(s));m.put(Enchantments.SHARPNESS,58);EnchantmentHelper.set(m,s);changed=true;}}return changed;}
 public static boolean protectEquipment(DynamicRegistryManager registry,List<ItemStack> kit){boolean changed=false;for(int i:new int[]{36,37,38}){var s=kit.get(i);if((s.getItem() instanceof ArmorItem||s.isOf(Items.ELYTRA))&&EnchantmentHelper.getLevel(Enchantments.PROTECTION,s)<60){var m=new HashMap<>(EnchantmentHelper.get(s));m.put(Enchantments.PROTECTION,60);EnchantmentHelper.set(m,s);changed=true;}}return changed;}
 private static void unbreakable(ItemStack s){s.getOrCreateNbt().putBoolean("Unbreakable",true);}
 public static ItemStack duckCharm(){var s=new ItemStack(Items.YELLOW_DYE);s.setCustomName(net.minecraft.text.Text.literal("Offhand de Pato"));s.getOrCreateNbt().put("Enchantments",new NbtList()); // explicit harmless glow marker below
  var glow=new NbtCompound();glow.putString("id","minecraft:unbreaking");glow.putShort("lvl",(short)1);var ench=new NbtList();ench.add(glow);s.getOrCreateNbt().put("Enchantments",ench);s.getOrCreateNbt().putInt("HideFlags",1);
  add(s,EntityAttributes.GENERIC_MAX_HEALTH,"offhand/max_health",30,EquipmentSlot.OFFHAND);add(s,EntityAttributes.GENERIC_ATTACK_DAMAGE,"offhand/attack_damage",1.5,EquipmentSlot.OFFHAND);return s;}
 public static List<ItemStack> defaults(){return defaults(null,Options.Rules.INSTA_KILL);}
 public static List<ItemStack> defaults(DynamicRegistryManager registry){return defaults(registry,Options.Rules.INSTA_KILL);}
 public static List<ItemStack> defaults(DynamicRegistryManager registry,Options.Rules rules){
  var a=new ArrayList<ItemStack>(Collections.nCopies(41,ItemStack.EMPTY));var sword=new ItemStack(Items.GOLDEN_SWORD);unbreakable(sword);add(sword,EntityAttributes.GENERIC_ATTACK_DAMAGE,"mainhand/attack_damage",25,EquipmentSlot.MAINHAND);sword.addEnchantment(Enchantments.SHARPNESS,58);a.set(0,sword);
  a.set(1,new ItemStack(Items.FIREWORK_ROCKET,64));a.set(2,new ItemStack(Items.ENCHANTED_GOLDEN_APPLE,32));a.set(3,new ItemStack(Items.COBWEB,32));a.set(5,new ItemStack(Items.BLACK_WOOL,64));for(int i=6;i<18;i++)a.set(i,new ItemStack(Items.TOTEM_OF_UNDYING));a.set(18,new ItemStack(Items.FIREWORK_ROCKET,64));a.set(36,new ItemStack(Items.NETHERITE_BOOTS));a.set(37,new ItemStack(Items.NETHERITE_LEGGINGS));unbreakable(a.get(36));unbreakable(a.get(37));
  var elytra=new ItemStack(Items.ELYTRA);unbreakable(elytra);add(elytra,EntityAttributes.GENERIC_MAX_HEALTH,"chest/max_health",25,EquipmentSlot.CHEST);add(elytra,EntityAttributes.GENERIC_ATTACK_SPEED,"chest/attack_speed",255,EquipmentSlot.CHEST);a.set(38,elytra);
  var head=new ItemStack(Items.PLAYER_HEAD);try(var in=Kits.class.getResourceAsStream("/duckbox/rasy_mc_profile.json")){var json=JsonParser.parseReader(new java.io.InputStreamReader(in)).getAsJsonObject();var raw=json.get("id").getAsString();var profile=new com.mojang.authlib.GameProfile(UUID.fromString(raw.replaceFirst("(........)(....)(....)(....)(............)","$1-$2-$3-$4-$5")),json.get("name").getAsString());for(var e:json.getAsJsonArray("properties")){var p=e.getAsJsonObject();profile.getProperties().put(p.get("name").getAsString(),new com.mojang.authlib.properties.Property(p.get("name").getAsString(),p.get("value").getAsString()));}head.getOrCreateNbt().put("SkullOwner",net.minecraft.nbt.NbtHelper.writeGameProfile(new NbtCompound(),profile));}catch(Exception e){throw new IllegalStateException(e);}
  add(head,EntityAttributes.GENERIC_MAX_HEALTH,"head/max_health",60,EquipmentSlot.HEAD);head.addEnchantment(Enchantments.PROTECTION,60);a.set(39,head);a.set(40,duckCharm());protectEquipment(registry,a);if(rules==Options.Rules.NORMAL_SPAM)repairNormalKit(a);return a;
 }
}
