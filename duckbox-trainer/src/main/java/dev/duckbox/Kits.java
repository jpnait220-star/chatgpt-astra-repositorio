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
            Identifier.of("duckbox", id.getPath()),
            amount,
            EntityAttributeModifier.Operation.ADD_VALUE);
    held.set(DataComponentTypes.ATTRIBUTE_MODIFIERS, mods.with(attr, modifier, slot));
    p.getInventory().markDirty();
  }

  public static List<ItemStack> defaults() {
    List<ItemStack> kit = new ArrayList<>(Collections.nCopies(41, ItemStack.EMPTY));
    ItemStack sword = new ItemStack(Items.NETHERITE_SWORD);
    sword.set(DataComponentTypes.UNBREAKABLE, new UnbreakableComponent(true));
    kit.set(0, sword);
    kit.set(1, new ItemStack(Items.FIREWORK_ROCKET, 64));
    kit.set(2, new ItemStack(Items.ENCHANTED_GOLDEN_APPLE, 32));
    kit.set(3, new ItemStack(Items.COBWEB, 32));
    for (int i = 6; i <= 8; i++) kit.set(i, new ItemStack(Items.TOTEM_OF_UNDYING));
    for (int i = 9; i < 18; i++) kit.set(i, new ItemStack(Items.TOTEM_OF_UNDYING));
    kit.set(18, new ItemStack(Items.FIREWORK_ROCKET, 64));
    kit.set(36, new ItemStack(Items.NETHERITE_BOOTS));
    kit.set(37, new ItemStack(Items.NETHERITE_LEGGINGS));
    ItemStack elytra = new ItemStack(Items.ELYTRA);
    elytra.set(DataComponentTypes.UNBREAKABLE, new UnbreakableComponent(true));
    elytra.set(
        DataComponentTypes.ATTRIBUTE_MODIFIERS,
        AttributeModifiersComponent.builder()
            .add(
                EntityAttributes.ATTACK_DAMAGE,
                new EntityAttributeModifier(
                    Identifier.of("duckbox", "attack_damage"),
                    255,
                    EntityAttributeModifier.Operation.ADD_VALUE),
                AttributeModifierSlot.CHEST)
            .add(
                EntityAttributes.ATTACK_SPEED,
                new EntityAttributeModifier(
                    Identifier.of("duckbox", "attack_speed"),
                    255,
                    EntityAttributeModifier.Operation.ADD_VALUE),
                AttributeModifierSlot.CHEST)
            .build());
    kit.set(38, elytra);
    ItemStack head = new ItemStack(Items.PLAYER_HEAD);
    head.set(
        DataComponentTypes.ATTRIBUTE_MODIFIERS,
        AttributeModifiersComponent.builder()
            .add(
                EntityAttributes.MAX_HEALTH,
                new EntityAttributeModifier(
                    Identifier.of("duckbox", "max_health"),
                    1000,
                    EntityAttributeModifier.Operation.ADD_VALUE),
                AttributeModifierSlot.HEAD)
            .build());
    kit.set(39, head);
    kit.set(40, new ItemStack(Items.TOTEM_OF_UNDYING));
    return kit;
  }
}
