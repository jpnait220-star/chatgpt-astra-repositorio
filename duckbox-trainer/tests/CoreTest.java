import dev.duckbox.*;
import java.io.*;
import java.util.*;
import net.minecraft.Bootstrap;
import net.minecraft.SharedConstants;
import net.minecraft.component.*;
import net.minecraft.component.type.*;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.attribute.*;
import net.minecraft.item.*;
import net.minecraft.nbt.*;

public class CoreTest {
  static int count;

  static void check(boolean value) {
    count++;
    if (!value) throw new AssertionError("case " + count);
  }

  static java.util.List<Integer> colors(net.minecraft.text.Text text) {
    var result = new java.util.ArrayList<Integer>();
    text.visit(
        (style, value) -> {
          if (!value.isEmpty())
            result.add(style.getColor() == null ? -1 : style.getColor().getRgb());
          return java.util.Optional.empty();
        },
        net.minecraft.text.Style.EMPTY);
    return result;
  }

  public static void main(String[] args) throws Exception {
    SharedConstants.createGameVersion();
    Bootstrap.initialize();
    for (int i = -1080; i <= 1080; i++) {
      check(Aim.wrap(i) >= -180 && Aim.wrap(i) < 180);
      check(Math.abs(Aim.wrap(Aim.approach(i, 137, 17) - i)) <= 17.001);
    }
    check(Math.abs(Aim.wrap(Aim.approach(179, -179, 5) + 179)) < 0.01);
    check(
        dev.duckbox.cosmetic.BotSkin.ROBOT
            .elytraTexture()
            .equals(dev.duckbox.cosmetic.BotSkin.CAPE));
    var capePng =
        javax.imageio.ImageIO.read(
            CoreTest.class.getResourceAsStream("/assets/duckbox/textures/entity/yellow_cape.png"));
    check(capePng.getWidth() == 64 && capePng.getHeight() == 32);
    var robotId = java.util.UUID.randomUUID();
    var humanId = java.util.UUID.randomUUID();
    dev.duckbox.cosmetic.CosmeticState.set(new CosmeticPayload(humanId, robotId, 0));
    var scope = Class.forName("com.duckunified.duckbox.HitDelayScope").getMethod("allow");
    Class.forName(
            "com.duckunified.mixin.LocalAttackDelayMixin", false, CoreTest.class.getClassLoader())
        .getDeclaredMethods();
    ClientTrainingState.clear();
    check((boolean) scope.invoke(null));
    ClientTrainingState.set(new TrainingPayload(humanId, robotId, true, false));
    check(!ClientTrainingState.localNoHitDelay(humanId));
    check(!(boolean) scope.invoke(null));
    ClientTrainingState.set(new TrainingPayload(humanId, robotId, true, true));
    check(ClientTrainingState.localNoHitDelay(humanId));
    check(!ClientTrainingState.localNoHitDelay(robotId));
    check((boolean) scope.invoke(null));
    ClientTrainingState.set(new TrainingPayload(humanId, new UUID(0, 0), false, false));
    check(!ClientTrainingState.localNoHitDelay(humanId));
    check((boolean) scope.invoke(null));
    ClientTrainingState.clear();
    var original =
        new net.minecraft.client.util.SkinTextures(
            net.minecraft.util.Identifier.of("minecraft", "original.png"),
            null,
            null,
            null,
            net.minecraft.client.util.SkinTextures.Model.SLIM,
            true);
    check(
        dev.duckbox.cosmetic.BotSkin.resolve(robotId, original)
            == dev.duckbox.cosmetic.BotSkin.ROBOT);
    check(dev.duckbox.cosmetic.BotSkin.resolve(humanId, original) == original);
    var renderState = new net.minecraft.client.render.entity.state.PlayerEntityRenderState();
    renderState.skinTextures = original;
    renderState.wearingSkullType = net.minecraft.block.SkullBlock.Type.PLAYER;
    dev.duckbox.cosmetic.BotSkin.apply(humanId, renderState);
    check(renderState.wearingSkullType == net.minecraft.block.SkullBlock.Type.PLAYER);
    dev.duckbox.cosmetic.BotSkin.apply(robotId, renderState);
    check(
        renderState.skinTextures.texture().equals(dev.duckbox.cosmetic.BotSkin.TEXTURE)
            && renderState.skinTextures.model()
                == net.minecraft.client.util.SkinTextures.Model.WIDE);
    check(
        renderState.wearingSkullType == null
            && renderState.hatVisible
            && renderState.jacketVisible);
    dev.duckbox.cosmetic.CosmeticState.clear();
    check(dev.duckbox.cosmetic.BotSkin.resolve(robotId, original) == original);
    try (var skin =
        CoreTest.class.getResourceAsStream("/assets/duckbox/textures/entity/robot_duck.png")) {
      var decoded = javax.imageio.ImageIO.read(skin);
      check(decoded.getWidth() == 64 && decoded.getHeight() == 64);
    }
    var registries = net.minecraft.registry.BuiltinRegistries.createWrapperLookup();
    CpsCadence cadence = new CpsCadence(15);
    int attempts = 0;
    for (int second = 0; second < 100; second++) {
      int local = 0;
      for (int tick = 0; tick < 20; tick++)
        if (cadence.next()) {
          local++;
          attempts++;
        }
      check(local == 15);
    }
    check(attempts == 1500);
    for (var level : Options.Difficulty.values()) check(level.cps == 15);
    var kit = Kits.defaults(registries);
    check(kit.size() == 41);
    int totems = 0;
    for (var s : kit) if (Kits.isTotem(s)) totems += s.getCount();
    check(totems == 12);
    check(
        Kits.isTotem(kit.get(6))
            && Kits.isTotem(kit.get(7))
            && Kits.isTotem(kit.get(8))
            && !Kits.isTotem(kit.get(40)));
    check(kit.get(38).isOf(Items.ELYTRA));
    double[] totals = {0, 0, 0};
    Set<String> modifierKeys = new HashSet<>();
    for (EquipmentSlot slot :
        List.of(
            EquipmentSlot.HEAD,
            EquipmentSlot.CHEST,
            EquipmentSlot.OFFHAND,
            EquipmentSlot.MAINHAND)) {
      var item =
          kit.get(
              switch (slot) {
                case HEAD -> 39;
                case CHEST -> 38;
                case OFFHAND -> 40;
                default -> 0;
              });
      item.applyAttributeModifiers(
          slot,
          (a, m) -> {
            check(modifierKeys.add(a.getIdAsString() + m.id()));
            if (a == EntityAttributes.MAX_HEALTH) totals[0] += m.value();
            if (a == EntityAttributes.ATTACK_DAMAGE) totals[1] += m.value();
            if (a == EntityAttributes.ATTACK_SPEED) totals[2] += m.value();
          });
    }
    check(totals[0] == 115 && totals[1] == 27.5 && totals[2] == 255);
    check(kit.get(0).isOf(Items.GOLDEN_SWORD));
    check(
        kit.get(0).contains(DataComponentTypes.UNBREAKABLE)
            && kit.get(38).contains(DataComponentTypes.UNBREAKABLE));
    check(!kit.get(40).contains(DataComponentTypes.DEATH_PROTECTION));
    check(
        kit.get(36).contains(DataComponentTypes.UNBREAKABLE)
            && kit.get(37).contains(DataComponentTypes.UNBREAKABLE));
    var normal = Kits.defaults(registries, Options.Rules.NORMAL_SPAM);
    double[] normalDamage = {0};
    normal
        .get(0)
        .applyAttributeModifiers(
            EquipmentSlot.MAINHAND,
            (a, m) -> {
              if (a == EntityAttributes.ATTACK_DAMAGE) normalDamage[0] += m.value();
            });
    check(normalDamage[0] == 20);
    check(Options.SpinLevel.EXTREMO.interval < Options.SpinLevel.MEDIO.interval);
    var ench = registries.getOrThrow(net.minecraft.registry.RegistryKeys.ENCHANTMENT);
    check(
        kit.get(0)
                .getEnchantments()
                .getLevel(ench.getOrThrow(net.minecraft.enchantment.Enchantments.SHARPNESS))
            == 54);
    check(
        kit.get(39)
                .getEnchantments()
                .getLevel(ench.getOrThrow(net.minecraft.enchantment.Enchantments.PROTECTION))
            == 60);
    check(kit.get(39).get(DataComponentTypes.PROFILE).gameProfile().getName().equals("RasyMc"));
    check(!kit.get(39).get(DataComponentTypes.PROFILE).properties().isEmpty());
    check(
        kit.get(40).isOf(Items.YELLOW_DYE)
            && kit.get(40).get(DataComponentTypes.ENCHANTMENT_GLINT_OVERRIDE));
    Set<Integer> logical = new HashSet<>();
    for (int i = 0; i < 54; i++) {
      int slot = KitEditor.logicalSlot(i);
      if (slot >= 0) check(logical.add(slot));
    }
    check(logical.size() == 41);
    for (int i = 0; i < 41; i++) check(logical.contains(i));
    check(new Options().size == 13);
    check(new com.google.gson.Gson().fromJson("{}", Options.class).cps == 15);
    check(
        Options.allowedCps(10)
            && Options.allowedCps(13)
            && Options.allowedCps(15)
            && !Options.allowedCps(11));
    check(Options.nextCps(10) == 13 && Options.nextCps(13) == 15 && Options.nextCps(15) == 10);
    check(new Options().x == -5 && new Options().y == 78 && new Options().z == 111);
    check(!new Options().autoBuildOnJoin);
    check(Options.nextSize(9) == 13 && Options.nextSize(13) == 17 && Options.nextSize(17) == 9);
    check(Options.allowedSize(41) == 17 && Options.allowedSize(11) == 13);
    check(CombatPlan.mayReposition(true, true, false, false, 80, 60, 9, 1));
    check(!CombatPlan.mayReposition(true, true, false, false, 80, 60, 100, 1));
    check(!CombatPlan.mayReposition(true, true, false, false, 80, 90, 9, 1));
    check(!CombatPlan.mayReposition(true, true, true, false, 80, 60, 9, 1));
    var copied = kit.get(1).copy();
    copied.decrement(1);
    check(kit.get(1).getCount() == 64 && copied.getCount() == 63);
    Options o = new Options();
    check(o.webCooldown == 200);
    for (String key :
        List.of("giro", "retotem", "gap", "teia", "wtap", "strafe", "foguete_teia", "tank")) {
      boolean first = o.toggle(key);
      check(o.toggle(key) != first);
    }
    for (var d : Options.Difficulty.values())
      check(d.reaction > 0 && d.swapDelay >= 2 && d.cps <= 20);
    var conn = new TrainingBot.LocalConnection();
    check(conn.isOpen() && conn.isLocal());
    conn.transitionOutbound(null);
    conn.transitionInbound(null, null);
    conn.send(null);
    conn.send(null, null);
    conn.send(null, null, true);
    check(conn.getAddress() != null);
    var packet =
        new TrainingPayload(java.util.UUID.randomUUID(), java.util.UUID.randomUUID(), true);
    var buffer =
        new net.minecraft.network.RegistryByteBuf(
            io.netty.buffer.Unpooled.buffer(), net.minecraft.registry.DynamicRegistryManager.EMPTY);
    TrainingPayload.CODEC.encode(buffer, packet);
    check(TrainingPayload.CODEC.decode(buffer).equals(packet));
    buffer.release();
    var cosmeticPacket =
        new CosmeticPayload(java.util.UUID.randomUUID(), java.util.UUID.randomUUID(), 15);
    var meshBuffer =
        new net.minecraft.network.RegistryByteBuf(
            io.netty.buffer.Unpooled.buffer(), net.minecraft.registry.DynamicRegistryManager.EMPTY);
    CosmeticPayload.CODEC.encode(meshBuffer, cosmeticPacket);
    check(CosmeticPayload.CODEC.decode(meshBuffer).equals(cosmeticPacket));
    meshBuffer.release();
    dev.duckbox.cosmetic.CosmeticState.set(cosmeticPacket);
    check(dev.duckbox.cosmetic.CosmeticState.enabled(cosmeticPacket.owner(), 1));
    check(dev.duckbox.cosmetic.CosmeticState.enabled(cosmeticPacket.bot(), 8));
    check(!dev.duckbox.cosmetic.CosmeticState.enabled(java.util.UUID.randomUUID(), 1));
    dev.duckbox.cosmetic.CosmeticState.clear();
    check(!dev.duckbox.cosmetic.CosmeticState.enabled(cosmeticPacket.owner(), 1));

    check(RichNames.parse("&aPato &lForte").getString().equals("Pato Forte"));
    check(colors(RichNames.parse("&#12abEFDuck")).getFirst() == 0x12abef);
    check(RichNames.parse("&x&f&f&0&0&8&8Duck").getString().equals("Duck"));
    var gradient = RichNames.parse("<gradient:#ff0000:#0000ff>ABC</gradient>");
    check(gradient.getString().equals("ABC"));
    check(colors(gradient).getFirst() == 0xff0000);
    check(colors(gradient).getLast() == 0x0000ff);
    check(RichNames.parse("<rainbow>Duck</rainbow>").getString().equals("Duck"));
    check(RichNames.parse("<bold><#123456>Duck</#123456></bold>").getString().equals("Duck"));
    boolean rejected = false;
    try {
      RichNames.parse("<gradient:#oops:#ffffff>A</gradient>");
    } catch (IllegalArgumentException expected) {
      rejected = true;
    }
    check(rejected);
    for (int profile = 0; profile <= 4; profile++) {
      var chest = TrainerChests.item(profile);
      check(chest.isOf(Items.CHEST));
      check(
          chest.get(DataComponentTypes.CUSTOM_DATA).copyNbt().getInt("duckbox_chest_profile")
              == profile);
    }
    for (String name : new String[] {"stock", "profile"}) {
      var chestPng =
          javax.imageio.ImageIO.read(
              CoreTest.class.getResourceAsStream(
                  "/assets/duckbox/textures/entity/chest/" + name + ".png"));
      check(chestPng.getWidth() == 64 && chestPng.getHeight() == 64);
      check(CoreTest.class.getResource("/assets/duckbox/items/" + name + "_chest.json") != null);
    }
    var armorRegistries = net.minecraft.registry.BuiltinRegistries.createWrapperLookup();
    var protection60 =
        armorRegistries
            .getOrThrow(net.minecraft.registry.RegistryKeys.ENCHANTMENT)
            .getOrThrow(net.minecraft.enchantment.Enchantments.PROTECTION);
    for (var combatRule : Options.Rules.values()) {
      var protectedSet = Kits.defaults(armorRegistries, combatRule);
      for (int equipmentSlot : new int[] {36, 37, 38}) {
        check(
            net.minecraft.enchantment.EnchantmentHelper.getLevel(
                    protection60, protectedSet.get(equipmentSlot))
                == 60);
        check(protectedSet.get(equipmentSlot).contains(DataComponentTypes.UNBREAKABLE));
      }
      check(!Kits.protectEquipment(armorRegistries, protectedSet));
      protectedSet.get(38).remove(DataComponentTypes.ENCHANTMENTS);
      var beforeUpgradeAttributes =
          protectedSet.get(38).get(DataComponentTypes.ATTRIBUTE_MODIFIERS);
      check(Kits.protectEquipment(armorRegistries, protectedSet));
      check(
          net.minecraft.enchantment.EnchantmentHelper.getLevel(protection60, protectedSet.get(38))
              == 60);
      check(
          protectedSet
              .get(38)
              .get(DataComponentTypes.ATTRIBUTE_MODIFIERS)
              .equals(beforeUpgradeAttributes));
    }
    NbtCompound root =
        NbtIo.readCompressed(new FileInputStream(args[0]), NbtSizeTracker.ofUnlimitedBytes());
    NbtCompound data = root.getCompound("Data");
    check(data.getInt("DataVersion") == 4189);
    check(data.getString("LevelName").equals("DuckBoxTreino"));
    check(
        data.getCompound("WorldGenSettings")
            .getCompound("dimensions")
            .getCompound("minecraft:overworld")
            .getCompound("generator")
            .getString("type")
            .equals("minecraft:flat"));
    var ops =
        net.minecraft.registry.RegistryOps.of(
            NbtOps.INSTANCE, net.minecraft.registry.BuiltinRegistries.createWrapperLookup());
    check(
        net.minecraft.world.gen.GeneratorOptions.CODEC
            .codec()
            .parse(ops, data.getCompound("WorldGenSettings"))
            .result()
            .isPresent());
    var dimensions =
        net.minecraft.world.dimension.DimensionOptionsRegistryHolder.CODEC
            .codec()
            .parse(ops, data.getCompound("WorldGenSettings"));
    if (dimensions.error().isPresent())
      throw new AssertionError(dimensions.error().get().message());
    check(dimensions.result().isPresent());
    System.out.println(
        "PASS "
            + count
            + " real Minecraft registry/kit attributes/totem budgets/copy isolation/local"
            + " connection/map NBT/aim angle checks. No graphical gameplay test.");
  }
}
