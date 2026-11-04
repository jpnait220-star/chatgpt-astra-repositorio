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
    var kit = Kits.defaults(world.getRegistryManager());
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
    java.lang.reflect.Field ticks =
        net.minecraft.server.MinecraftServer.class.getDeclaredField("field_4572");
    ticks.setAccessible(true);
    boolean hit = false, moved = false;
    int landed=0;float previousHealth=owner.getHealth();
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
        if(landed>=3){hit=true;break;}
      }
      previousHealth=owner.getHealth();
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
