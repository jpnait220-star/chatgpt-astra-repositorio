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
    var kit = Kits.defaults();
    check(kit.size() == 41);
    int totems = 0;
    for (var s : kit) if (s.isOf(Items.TOTEM_OF_UNDYING)) totems += s.getCount();
    check(totems == 13);
    check(
        kit.get(6).isOf(Items.TOTEM_OF_UNDYING)
            && kit.get(7).isOf(Items.TOTEM_OF_UNDYING)
            && kit.get(8).isOf(Items.TOTEM_OF_UNDYING)
            && kit.get(40).isOf(Items.TOTEM_OF_UNDYING));
    check(kit.get(38).isOf(Items.ELYTRA));
    double[] damage = {0}, speed = {0}, health = {0};
    kit.get(38)
        .applyAttributeModifiers(
            EquipmentSlot.CHEST,
            (a, m) -> {
              if (a == EntityAttributes.ATTACK_DAMAGE) damage[0] += m.value();
              if (a == EntityAttributes.ATTACK_SPEED) speed[0] += m.value();
            });
    kit.get(39)
        .applyAttributeModifiers(
            EquipmentSlot.HEAD,
            (a, m) -> {
              if (a == EntityAttributes.MAX_HEALTH) health[0] += m.value();
            });
    check(damage[0] == 255 && speed[0] == 255 && health[0] == 1000);
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
