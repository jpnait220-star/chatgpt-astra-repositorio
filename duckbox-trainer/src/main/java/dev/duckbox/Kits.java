package dev.duckbox;

import com.google.gson.*;
import com.mojang.serialization.JsonOps;
import java.util.*;
import net.minecraft.component.*;
import net.minecraft.component.type.*;
import net.minecraft.entity.attribute.*;
import net.minecraft.item.*;
import net.minecraft.registry.Registries;
import net.minecraft.registry.RegistryOps;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.Identifier;

public final class Kits {
  public static List<ItemStack> capture(ServerPlayerEntity p) {
    List<ItemStack> a = new ArrayList<>();
    for (int i = 0; i < p.getInventory().size(); i++) a.add(p.getInventory().getStack(i).copy());
    return a;
  }

  public static void give(ServerPlayerEntity p, List<ItemStack> kit) {
    p.stopUsingItem();
    p.getInventory().clear();
    for (int i = 0; i < Math.min(kit.size(), p.getInventory().size()); i++)
      p.getInventory().setStack(i, kit.get(i).copy());
    p.getInventory().selectedSlot = 0;
    p.getInventory().markDirty();
    p.currentScreenHandler.sendContentUpdates();
    p.networkHandler.sendPacket(
        new net.minecraft.network.packet.s2c.play.UpdateSelectedSlotS2CPacket(
            p.getInventory().selectedSlot));
  }

  public static JsonArray encode(ServerPlayerEntity p, List<ItemStack> kit) {
    JsonArray a = new JsonArray();
    var ops = RegistryOps.of(JsonOps.INSTANCE, p.getRegistryManager());
    for (ItemStack s : kit)
      a.add(s.isEmpty() ? JsonNull.INSTANCE : ItemStack.CODEC.encodeStart(ops, s).getOrThrow());
    return a;
  }

  public static List<ItemStack> decode(ServerPlayerEntity p, JsonArray a) {
    List<ItemStack> list = new ArrayList<>();
    var ops = RegistryOps.of(JsonOps.INSTANCE, p.getRegistryManager());
    for (JsonElement e : a)
      list.add(e.isJsonNull() ? ItemStack.EMPTY : ItemStack.CODEC.parse(ops, e).getOrThrow());
    return list;
  }

  public static void attribute(
      ServerPlayerEntity p, String key, double amount, AttributeModifierSlot slot) {
    ItemStack held = p.getMainHandStack();
    if (held.isEmpty()) throw new IllegalArgumentException("Segure um item.");
    var id = Identifier.of(key.contains(":") ? key : "minecraft:" + key);
    var attr =
        Registries.ATTRIBUTE
            .getEntry(id)
            .orElseThrow(() -> new IllegalArgumentException("Atributo desconhecido."));
    var mods =
        held.getOrDefault(
            DataComponentTypes.ATTRIBUTE_MODIFIERS, AttributeModifiersComponent.DEFAULT);
    var modifier =
        new EntityAttributeModifier(
            Identifier.of("duckbox", slot.asString() + "/" + id.getPath()),
            amount,
            EntityAttributeModifier.Operation.ADD_VALUE);
    held.set(DataComponentTypes.ATTRIBUTE_MODIFIERS, mods.with(attr, modifier, slot));
    p.getInventory().markDirty();
  }

  public static boolean repairNormalKit(List<ItemStack> kit) {
    boolean changed = false;
    for (ItemStack stack : kit) {
      if (!stack.isOf(Items.GOLDEN_SWORD)) continue;
      var mods =
          stack.getOrDefault(
              DataComponentTypes.ATTRIBUTE_MODIFIERS, AttributeModifiersComponent.DEFAULT);
      boolean duckSword =
          mods.modifiers().stream()
              .anyMatch(
                  e ->
                      e.attribute().equals(EntityAttributes.ATTACK_DAMAGE)
                          && e.modifier()
                              .id()
                              .equals(Identifier.of("duckbox", "mainhand/attack_damage")));
      boolean speedConfigured =
          mods.modifiers().stream()
              .anyMatch(e -> e.attribute().equals(EntityAttributes.ATTACK_SPEED));
      if (!duckSword || speedConfigured) continue;
      stack.set(
          DataComponentTypes.ATTRIBUTE_MODIFIERS,
          mods.with(
              EntityAttributes.ATTACK_SPEED,
              new EntityAttributeModifier(
                  Item.BASE_ATTACK_SPEED_MODIFIER_ID,
                  -2.4,
                  EntityAttributeModifier.Operation.ADD_VALUE),
              AttributeModifierSlot.MAINHAND));
      changed = true;
    }
    return changed;
  }

  public static boolean isTotem(ItemStack stack) {
    return !stack.isEmpty() && stack.contains(DataComponentTypes.DEATH_PROTECTION);
  }

  public static boolean isCharm(ItemStack stack) {
    return stack.isOf(Items.YELLOW_DYE) && !isTotem(stack);
  }

  public static ItemStack duckCharm() {
    ItemStack dye = new ItemStack(Items.YELLOW_DYE);
    dye.set(DataComponentTypes.CUSTOM_NAME, net.minecraft.text.Text.literal("Offhand de Pato"));
    dye.set(DataComponentTypes.ENCHANTMENT_GLINT_OVERRIDE, true);
    dye.set(DataComponentTypes.MAX_STACK_SIZE, 1);

    dye.set(
        DataComponentTypes.ATTRIBUTE_MODIFIERS,
        AttributeModifiersComponent.builder()
            .add(
                EntityAttributes.MAX_HEALTH,
                modifier("offhand/max_health", 30),
                AttributeModifierSlot.OFFHAND)
            .add(
                EntityAttributes.ATTACK_DAMAGE,
                modifier("offhand/attack_damage", 1.5),
                AttributeModifierSlot.OFFHAND)
            .build());
    return dye;
  }

  private static EntityAttributeModifier modifier(String name, double value) {
    return new EntityAttributeModifier(
        Identifier.of("duckbox", name), value, EntityAttributeModifier.Operation.ADD_VALUE);
  }

  private static ProfileComponent duckProfile() {
    try (var in = Kits.class.getResourceAsStream("/duckbox/rasy_mc_profile.json")) {
      JsonObject json =
          JsonParser.parseReader(
                  new java.io.InputStreamReader(in, java.nio.charset.StandardCharsets.UTF_8))
              .getAsJsonObject();
      String id = json.get("id").getAsString();
      java.util.UUID uuid =
          java.util.UUID.fromString(
              id.replaceFirst("(........)(....)(....)(....)(............)", "$1-$2-$3-$4-$5"));
      var profile = new com.mojang.authlib.GameProfile(uuid, json.get("name").getAsString());
      for (var value : json.getAsJsonArray("properties")) {
        JsonObject property = value.getAsJsonObject();
        profile
            .getProperties()
            .put(
                property.get("name").getAsString(),
                new com.mojang.authlib.properties.Property(
                    property.get("name").getAsString(),
                    property.get("value").getAsString(),
                    property.has("signature") ? property.get("signature").getAsString() : null));
      }
      return new ProfileComponent(profile);
    } catch (Exception e) {
      throw new IllegalStateException("Perfil de RasyMc ausente ou invalido", e);
    }
  }

  public static boolean upgradeTrainingSword(
      net.minecraft.registry.RegistryWrapper.WrapperLookup registries, List<ItemStack> kit) {
    var sharpness =
        registries
            .getOrThrow(net.minecraft.registry.RegistryKeys.ENCHANTMENT)
            .getOrThrow(net.minecraft.enchantment.Enchantments.SHARPNESS);
    boolean changed = false;
    for (var stack : kit) {
      if (!stack.isOf(Items.GOLDEN_SWORD)) continue;
      var mods =
          stack.getOrDefault(
              DataComponentTypes.ATTRIBUTE_MODIFIERS, AttributeModifiersComponent.DEFAULT);
      var id = Identifier.of("duckbox", "mainhand/attack_damage");
      boolean ours =
          mods.modifiers().stream()
              .anyMatch(
                  e ->
                      e.attribute().equals(EntityAttributes.ATTACK_DAMAGE)
                          && e.modifier().id().equals(id));
      if (!ours) continue;
      if (mods.modifiers().stream()
          .anyMatch(
              e ->
                  e.attribute().equals(EntityAttributes.ATTACK_DAMAGE)
                      && e.modifier().id().equals(id)
                      && e.modifier().value() != 25)) {
        stack.set(
            DataComponentTypes.ATTRIBUTE_MODIFIERS,
            mods.with(
                EntityAttributes.ATTACK_DAMAGE,
                new EntityAttributeModifier(id, 25, EntityAttributeModifier.Operation.ADD_VALUE),
                AttributeModifierSlot.MAINHAND));
        changed = true;
      }
      if (net.minecraft.enchantment.EnchantmentHelper.getLevel(sharpness, stack) != 58) {
        if (!stack.contains(DataComponentTypes.ENCHANTMENTS))
          stack.set(DataComponentTypes.ENCHANTMENTS, ItemEnchantmentsComponent.DEFAULT);
        stack.addEnchantment(sharpness, 58);
        changed = true;
      }
    }
    return changed;
  }

  public static boolean protectEquipment(
      net.minecraft.registry.RegistryWrapper.WrapperLookup registries, List<ItemStack> kit) {
    var protection =
        registries
            .getOrThrow(net.minecraft.registry.RegistryKeys.ENCHANTMENT)
            .getOrThrow(net.minecraft.enchantment.Enchantments.PROTECTION);
    boolean changed = false;
    for (int slot : new int[] {36, 37, 38}) {
      var stack = kit.get(slot);
      var gear = stack.get(DataComponentTypes.EQUIPPABLE);
      var expected =
          slot == 36
              ? net.minecraft.entity.EquipmentSlot.FEET
              : slot == 37
                  ? net.minecraft.entity.EquipmentSlot.LEGS
                  : net.minecraft.entity.EquipmentSlot.CHEST;
      if (gear != null
          && gear.slot() == expected
          && net.minecraft.enchantment.EnchantmentHelper.getLevel(protection, stack) < 60) {
        if (!stack.contains(DataComponentTypes.ENCHANTMENTS))
          stack.set(DataComponentTypes.ENCHANTMENTS, ItemEnchantmentsComponent.DEFAULT);
        stack.addEnchantment(protection, 60);
        changed = true;
      }
    }
    return changed;
  }

  public static List<ItemStack> defaults() {
    return defaults(net.minecraft.registry.BuiltinRegistries.createWrapperLookup());
  }

  public static List<ItemStack> defaults(
      net.minecraft.registry.RegistryWrapper.WrapperLookup registries) {
    return defaults(registries, Options.Rules.INSTA_KILL);
  }

  public static List<ItemStack> defaults(
      net.minecraft.registry.RegistryWrapper.WrapperLookup registries, Options.Rules rules) {
    List<ItemStack> kit = new ArrayList<>(Collections.nCopies(41, ItemStack.EMPTY));
    ItemStack sword = new ItemStack(Items.GOLDEN_SWORD);
    sword.set(DataComponentTypes.UNBREAKABLE, new UnbreakableComponent(true));
    sword.set(
        DataComponentTypes.ATTRIBUTE_MODIFIERS,
        AttributeModifiersComponent.builder()
            .add(
                EntityAttributes.ATTACK_DAMAGE,
                modifier("mainhand/attack_damage", 25),
                AttributeModifierSlot.MAINHAND)
            .build());
    sword.addEnchantment(
        registries
            .getOrThrow(net.minecraft.registry.RegistryKeys.ENCHANTMENT)
            .getOrThrow(net.minecraft.enchantment.Enchantments.SHARPNESS),
        58);
    kit.set(0, sword);
    kit.set(1, new ItemStack(Items.FIREWORK_ROCKET, 64));
    kit.set(2, new ItemStack(Items.ENCHANTED_GOLDEN_APPLE, 32));
    kit.set(3, new ItemStack(Items.COBWEB, 32));
    kit.set(5, new ItemStack(Items.BLACK_WOOL, 64));
    for (int i = 6; i <= 8; i++) kit.set(i, new ItemStack(Items.TOTEM_OF_UNDYING));
    for (int i = 9; i < 18; i++) kit.set(i, new ItemStack(Items.TOTEM_OF_UNDYING));
    kit.set(18, new ItemStack(Items.FIREWORK_ROCKET, 64));
    kit.set(36, new ItemStack(Items.NETHERITE_BOOTS));
    kit.set(37, new ItemStack(Items.NETHERITE_LEGGINGS));
    kit.get(36).set(DataComponentTypes.UNBREAKABLE, new UnbreakableComponent(true));
    kit.get(37).set(DataComponentTypes.UNBREAKABLE, new UnbreakableComponent(true));
    ItemStack elytra = new ItemStack(Items.ELYTRA);
    elytra.set(DataComponentTypes.UNBREAKABLE, new UnbreakableComponent(true));
    elytra.set(
        DataComponentTypes.ATTRIBUTE_MODIFIERS,
        AttributeModifiersComponent.builder()
            .add(
                EntityAttributes.MAX_HEALTH,
                modifier("chest/max_health", 25),
                AttributeModifierSlot.CHEST)
            .add(
                EntityAttributes.ATTACK_SPEED,
                modifier("chest/attack_speed", 255),
                AttributeModifierSlot.CHEST)
            .build());
    kit.set(38, elytra);
    ItemStack head = new ItemStack(Items.PLAYER_HEAD);
    head.set(DataComponentTypes.PROFILE, duckProfile());
    head.set(
        DataComponentTypes.ATTRIBUTE_MODIFIERS,
        AttributeModifiersComponent.builder()
            .add(
                EntityAttributes.MAX_HEALTH,
                modifier("head/max_health", 60),
                AttributeModifierSlot.HEAD)
            .build());
    head.addEnchantment(
        registries
            .getOrThrow(net.minecraft.registry.RegistryKeys.ENCHANTMENT)
            .getOrThrow(net.minecraft.enchantment.Enchantments.PROTECTION),
        60);
    kit.set(39, head);
    kit.set(40, duckCharm());
    protectEquipment(registries, kit);
    if (rules == Options.Rules.NORMAL_SPAM) repairNormalKit(kit);
    return kit;
  }
}
