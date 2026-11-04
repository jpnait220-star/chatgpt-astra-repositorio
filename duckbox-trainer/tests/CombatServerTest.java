import com.mojang.authlib.GameProfile;
import dev.duckbox.*;
import java.nio.file.*;
import java.util.*;
import net.minecraft.*;
import net.minecraft.block.Blocks;
import net.minecraft.network.packet.c2s.common.SyncedClientOptions;
import net.minecraft.resource.VanillaDataPackProvider;
import net.minecraft.server.network.*;
import net.minecraft.test.*;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.GameMode;
import net.minecraft.world.level.storage.LevelStorage;

/** Real vanilla test server: no socket, no EULA flow, no substituted world/player/physics. */
public final class CombatServerTest {
  public static void main(String[] args) throws Exception {
    SharedConstants.createGameVersion();
    Bootstrap.initialize();
    var storage = LevelStorage.create(Path.of(args[0]));
    var save = storage.createSession("combat");
    var packs = VanillaDataPackProvider.createManager(save);
    var dummy = new TestFunction("duckbox", "not_run", "empty", 200, 0, true, ctx -> {});
    var server =
        TestServer.create(
            Thread.currentThread(), save, packs, List.of(dummy), new BlockPos(0, 64, 0));
    if (!server.setupServer()) throw new AssertionError("setup");
    server.setPvpEnabled(true);
    DuckBox.server = server;
    var world = server.getOverworld();
    for (int x = -10; x <= 10; x++)
      for (int z = -10; z <= 10; z++)
        world.setBlockState(new BlockPos(x, 63, z), Blocks.STONE.getDefaultState(), 3);
    var owner =
        new ServerPlayerEntity(
            server,
            world,
            new GameProfile(UUID.randomUUID(), "TrainOwner"),
            SyncedClientOptions.createDefault());
    var bot = new TrainingBot(server, world);
    server
        .getPlayerManager()
        .onPlayerConnect(
            new TrainingBot.LocalConnection(),
            owner,
            ConnectedClientData.createDefault(owner.getGameProfile(), false));
    server
        .getPlayerManager()
        .onPlayerConnect(
            new TrainingBot.LocalConnection(),
            bot,
            ConnectedClientData.createDefault(bot.getGameProfile(), false));
    owner.changeGameMode(GameMode.SURVIVAL);
    bot.changeGameMode(GameMode.SURVIVAL);
    var kit = Kits.defaults(world.getRegistryManager(), Options.Rules.NORMAL_SPAM);
    var encodedKit = Kits.encode(owner, kit);
    var decodedKit = Kits.decode(owner, encodedKit);
    for (int i = 0; i < 41; i++)
      if (!net.minecraft.item.ItemStack.areEqual(kit.get(i), decodedKit.get(i)))
        throw new AssertionError("World kit round trip failed at " + i);
    System.out.println(
        "PASS REAL WORLD KIT CODEC: all41slots including high enchantments, RasyMc profile, unique"
            + " attributes and custom totem round trip");
    Kits.give(owner, kit);
    Kits.give(bot, kit);
    owner.teleport(world, 0.5, 64, 0.5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    bot.teleport(world, 3.5, 64, 0.5, Set.of(), 90, 0, false);
    bot.onTeleportationDone();
    Options options = new Options();
    options.x = 0;
    options.y = 63;
    options.z = 0;
    options.gap = false;
    options.teia = false;
    options.retotem = false;
    options.strafe = false;
    options.giro = true;
    options.difficulty = Options.Difficulty.HIGH;
    DuckBox.options = options;
    DuckBox.session = new Session(owner, bot, options);
    DuckBox.session.startingBuffs();
    java.lang.reflect.Field ticks =
        net.minecraft.server.MinecraftServer.class.getDeclaredField("field_4572");
    ticks.setAccessible(true);
    boolean hit = false, moved = false;
    int landed = 0;
    float previousHealth = owner.getHealth();
    double start = bot.getX();
    for (int t = 1; t <= 180; t++) {
      ticks.setInt(server, t);
      world.setTimeOfDay(t);
      owner.tick();
      owner.playerTick();
      owner.onTeleportationDone();
      bot.tick();
      if (t == 5 && Math.abs(owner.getMaxHealth() - 135) > 0.01)
        throw new AssertionError("Expected135 max health, got " + owner.getMaxHealth());
      if (Math.abs(bot.getX() - start) > 0.1) moved = true;
      if (t > 5 && owner.getHealth() < previousHealth - 0.1) {
        landed++;
        System.out.println(
            "PASS REAL COMBAT: bot moved="
                + moved
                + ", damaged survival owner at tick "
                + t
                + ", health="
                + owner.getHealth()
                + "/"
                + owner.getMaxHealth()
                + ", distance="
                + bot.distanceTo(owner));
        if (landed >= 3) {
          hit = true;
          break;
        }
      }
      previousHealth = owner.getHealth();
    }
    if (!hit)
      throw new AssertionError(
          "No damage: moved="
              + moved
              + " bot="
              + bot.getPos()
              + " owner="
              + owner.getPos()
              + " loaded="
              + owner.isLoaded()
              + " phase health="
              + owner.getHealth());
    var active = DuckBox.session;
    for (var actor : List.of(owner, bot)) {
      if (actor.getStatusEffect(net.minecraft.entity.effect.StatusEffects.RESISTANCE).getAmplifier()
              != 1
          || actor.getStatusEffect(net.minecraft.entity.effect.StatusEffects.REGENERATION) == null
          || actor.getStatusEffect(net.minecraft.entity.effect.StatusEffects.FIRE_RESISTANCE)
              == null) throw new AssertionError("Starting gap effects");
    }
    owner
        .getInventory()
        .setStack(40, new net.minecraft.item.ItemStack(net.minecraft.item.Items.TOTEM_OF_UNDYING));
    owner.setHealth(1);
    if (!owner.damage(world, world.getDamageSources().generic(), 100000)
        || owner.getHealth() <= 0
        || !owner.getOffHandStack().isEmpty())
      throw new AssertionError("Vanilla totem did not pop");
    if (owner.hasStatusEffect(net.minecraft.entity.effect.StatusEffects.RESISTANCE))
      throw new AssertionError("Totem did not clear resistance as expected");
    active.maintainRules();
    if (owner.getStatusEffect(net.minecraft.entity.effect.StatusEffects.RESISTANCE).getAmplifier()
        != 1) throw new AssertionError("ResistanceII not restored");
    options.rules = Options.Rules.INSTA_KILL;
    active.maintainRules();
    if (owner.getStatusEffect(net.minecraft.entity.effect.StatusEffects.RESISTANCE).getAmplifier()
        != 0) throw new AssertionError("Insta Kill resistance must beI");
    options.rules = Options.Rules.NORMAL_SPAM;
    active.maintainRules();
    owner.getInventory().setStack(40, Kits.duckCharm());
    owner.setHealth(135);
    bot.setHealth(40);
    options.retotem = true;
    options.giro = false;
    int tick = server.getTicks();
    for (int i = 0; i < 12; i++) {
      ticks.setInt(server, ++tick);
      bot.tick();
    }
    if (!bot.getOffHandStack().isOf(net.minecraft.item.Items.TOTEM_OF_UNDYING))
      throw new AssertionError("Bot did not select vanilla protector at low health");
    int charms = 0;
    for (int i = 0; i < 41; i++) if (Kits.isCharm(bot.getInventory().getStack(i))) charms++;
    if (charms != 1) throw new AssertionError("Charm duplicated or lost");
    bot.setHealth(bot.getMaxHealth());
    for (int i = 0; i < 12; i++) {
      ticks.setInt(server, ++tick);
      bot.tick();
    }
    if (!Kits.isCharm(bot.getOffHandStack()))
      throw new AssertionError("Charm not restored after healing");
    if (!DuckBox.allowTrainingDamage(owner, world.getDamageSources().generic())
        || DuckBox.allowTrainingDamage(owner, world.getDamageSources().fall())
        || DuckBox.allowTrainingDamage(owner, world.getDamageSources().flyIntoWall()))
      throw new AssertionError("Fall/wall damage scope");
    System.out.println(
        "PASS REAL RULES: initial gap buffs; vanilla totem consumed; ResistanceII restored after"
            + " pop and I for Insta Kill; low-health protector swap and healed charm restore"
            + " conserve one charm; fall/wall scoped cancellation");
    bot.getInventory().setStack(5, bot.getOffHandStack());
    bot.getInventory().setStack(40, net.minecraft.item.ItemStack.EMPTY);
    int removed = 0;
    for (int i = 0; i < 9; i++)
      if (bot.getInventory().getStack(i).isOf(net.minecraft.item.Items.TOTEM_OF_UNDYING)) {
        removed += bot.getInventory().getStack(i).getCount();
        bot.getInventory().setStack(i, net.minecraft.item.ItemStack.EMPTY);
      }
    bot.setHealth(30);
    for (int i = 0; i < 40; i++) {
      ticks.setInt(server, ++tick);
      bot.tick();
    }
    if (!bot.getOffHandStack().isOf(net.minecraft.item.Items.TOTEM_OF_UNDYING)
        || active.countTotems() != 12 - removed)
      throw new AssertionError("Vanilla reserve refill conservation");
    options.retotem = false;
    options.gap = true;
    options.giro = false;
    bot.setHealth(35);
    int applesBefore = bot.getInventory().getStack(2).getCount();
    int eaten = 0;
    for (int i = 0; i < 145; i++) {
      ticks.setInt(server, ++tick);
      bot.tick();
      eaten = applesBefore - bot.getInventory().getStack(2).getCount();
      if (eaten >= 2) break;
    }
    if (eaten != 2)
      throw new AssertionError("Low health must consume two real gap items, got" + eaten);
    System.out.println(
        "PASS REAL RECOVERY: vanilla reserve refilled after hotbar depletion without extra totems;"
            + " low-health recovery consumed two real apples");
    DuckBox.session.closed = true;
    DuckBox.session = null;
    options.built = true;
    var chest = Arena.kitChest(options);
    owner.teleport(
        world, chest.getX() + 0.5, chest.getY(), chest.getZ() + 0.5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    var config = Path.of(args[0]).resolve("kit-editor-test.json");
    var configField = DuckBox.class.getDeclaredField("file");
    configField.setAccessible(true);
    configField.set(null, config);
    KitEditor.open(owner);
    if (!(owner.currentScreenHandler instanceof KitEditor))
      throw new AssertionError("Kit chest did not open");
    var editor = (KitEditor) owner.currentScreenHandler;
    if (!editor.canUse(owner)
        || editor.getSlot(45).canTakeItems(owner)
        || editor
            .getSlot(45)
            .canInsert(new net.minecraft.item.ItemStack(net.minecraft.item.Items.STONE)))
      throw new AssertionError("Kit chest permissions/locked labels");
    editor
        .getInventory()
        .setStack(27, new net.minecraft.item.ItemStack(net.minecraft.item.Items.DIAMOND_SWORD));
    editor
        .getInventory()
        .setStack(
            0, new net.minecraft.item.ItemStack(net.minecraft.item.Items.FIREWORK_ROCKET, 32));
    owner.closeHandledScreen();
    var saved = DuckBox.currentKit(owner);
    if (KitEditor.editing()
        || !saved.get(0).isOf(net.minecraft.item.Items.DIAMOND_SWORD)
        || saved.get(9).getCount() != 32
        || !saved.get(40).isOf(net.minecraft.item.Items.YELLOW_DYE)
        || !Files.readString(config).contains("minecraft:diamond_sword"))
      throw new AssertionError("Kit chest close/save mapping failed");
    System.out.println(
        "PASS REAL KIT CHEST: native 54-slot handler opens/closes, labels locked,"
            + " hotbar/storage/offhand mapping saved to JSON and decoded with world registry");
    options.rules = Options.Rules.INSTA_KILL;
    var insta = DuckBox.currentKit(owner);
    if (!insta.get(0).isOf(net.minecraft.item.Items.GOLDEN_SWORD))
      throw new AssertionError("Rules kits leaked into each other");
    options.rules = Options.Rules.NORMAL_SPAM;
    if (!DuckBox.currentKit(owner).get(0).isOf(net.minecraft.item.Items.DIAMOND_SWORD))
      throw new AssertionError("Normal custom kit lost");
    options.initialized = true;
    Arena.create(owner, options);
    int batches = 0;
    while (Arena.building()) {
      Arena.tick();
      if (++batches > 100) throw new AssertionError("Arena build stalled");
    }
    if (!options.built
        || !world.getBlockState(Arena.kitChest(options)).isOf(Blocks.CHEST)
        || !world
            .getBlockState(new BlockPos(options.x + options.size / 2, options.y + 1, options.z))
            .isOf(Blocks.LIGHT_BLUE_STAINED_GLASS)
        || !world
            .getBlockState(new BlockPos(options.x, options.y + Arena.HEIGHT, options.z))
            .isOf(Blocks.GLASS))
      throw new AssertionError("Detailed arena/chest/roof construction failed");
    if (!world
        .getBlockState(new BlockPos(options.x - 31, options.y + 1, options.z - 4))
        .isOf(Blocks.STONE_BUTTON)) throw new AssertionError("Mode must be a separate button");
    DuckBox.control(owner, "modo");
    if (!options.tank) throw new AssertionError("Tank selection");
    DuckBox.control(owner, "modo");
    if (options.tank) throw new AssertionError("Duel selection");
    Arena.controls.clear();
    if (Arena.control(new BlockPos(options.x - 31, options.y + 1, options.z - 8), world, options)
        == null) throw new AssertionError("Controls after reload");
    System.out.println(
        "PASS REAL MAP BUILD:13x13 arena,8-high roof, blue glass, kit chest, duck lobby and"
            + " restored controls; "
            + batches
            + " bounded batches");
    server.getPlayerManager().remove(bot);
    server.getPlayerManager().remove(owner);
    server.shutdown();
    System.exit(0);
  }
}
