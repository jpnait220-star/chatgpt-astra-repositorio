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

  public static void main(String[] args) throws Exception {
    SharedConstants.createGameVersion();
    Bootstrap.initialize();
    for (int i = -1080; i <= 1080; i++) {
      check(Aim.wrap(i) >= -180 && Aim.wrap(i) < 180);
      check(Math.abs(Aim.wrap(Aim.approach(i, 137, 17) - i)) <= 17.001);
    }
    check(Math.abs(Aim.wrap(Aim.approach(179, -179, 5) + 179)) < 0.01);
    var registries = net.minecraft.registry.BuiltinRegistries.createWrapperLookup();
    var kit = Kits.defaults(registries);
    check(kit.size() == 41);
    int totems = 0;
    for (var s : kit) if (Kits.isTotem(s)) totems += s.getCount();
    check(totems == 13);
    check(
        Kits.isTotem(kit.get(6))
            && Kits.isTotem(kit.get(7))
            && Kits.isTotem(kit.get(8))
            && Kits.isTotem(kit.get(40)));
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
