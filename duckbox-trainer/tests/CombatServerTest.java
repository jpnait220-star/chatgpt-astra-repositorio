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
  private static final class FeedbackConnection extends TrainingBot.LocalConnection {
    final java.util.List<net.minecraft.network.packet.Packet<?>> messages =
        new java.util.ArrayList<>();

    private void record(net.minecraft.network.packet.Packet<?> packet) {
      if (packet instanceof net.minecraft.network.packet.s2c.play.GameMessageS2CPacket
          || packet instanceof net.minecraft.network.packet.s2c.play.OverlayMessageS2CPacket)
        messages.add(packet);
    }

    @Override
    public void send(net.minecraft.network.packet.Packet<?> packet) {
      record(packet);
    }

    @Override
    public void send(
        net.minecraft.network.packet.Packet<?> packet,
        net.minecraft.network.PacketCallbacks callbacks) {
      record(packet);
    }

    @Override
    public void send(
        net.minecraft.network.packet.Packet<?> packet,
        net.minecraft.network.PacketCallbacks callbacks,
        boolean flush) {
      record(packet);
    }

    boolean chat() {
      return messages.stream()
          .anyMatch(
              p ->
                  p instanceof net.minecraft.network.packet.s2c.play.GameMessageS2CPacket m
                      && !m.overlay());
    }

    boolean overlay(String text) {
      return messages.stream()
          .anyMatch(
              p ->
                  p instanceof net.minecraft.network.packet.s2c.play.OverlayMessageS2CPacket overlay
                      ? overlay.text().getString().contains(text)
                      : p instanceof net.minecraft.network.packet.s2c.play.GameMessageS2CPacket game
                          && game.overlay()
                          && game.content().getString().contains(text));
    }
  }

  public static void main(String[] args) throws Exception {
    Thread.setDefaultUncaughtExceptionHandler(
        (thread, error) -> {
          error.printStackTrace();
          System.exit(1);
        });
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
    var feedbackConnection = new FeedbackConnection();
    server
        .getPlayerManager()
        .onPlayerConnect(
            feedbackConnection,
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
    if (!DuckBox.allowTrainingDeath(owner, world.getDamageSources().generic(), 100000)
        || active.finish != null)
      throw new AssertionError("Fabric death guard must allow vanilla totem before interception");
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
    bot.getInventory()
        .setStack(40, new net.minecraft.item.ItemStack(net.minecraft.item.Items.TOTEM_OF_UNDYING));
    bot.setHealth(1);
    bot.setAbsorptionAmount(0);
    bot.timeUntilRegen = 0;
    if (!DuckBox.allowTrainingDeath(bot, world.getDamageSources().generic(), 100000)
        || !bot.damage(world, world.getDamageSources().generic(), 100000)
        || bot.getHealth() <= 0
        || !bot.getOffHandStack().isEmpty()
        || active.finish != null)
      throw new AssertionError("Bot vanilla pop must not finish session");
    bot.getInventory().setStack(40, Kits.duckCharm());
    bot.getInventory().selectedSlot = 0;
    if (DuckBox.allowTrainingDeath(bot, world.getDamageSources().generic(), 100000)
        || active.finish == null) throw new AssertionError("No totem must end round without drops");
    active.finish = null;
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
    DuckBox.session = new Session(owner, bot, options);
    // Native block placement and destruction: stock is consumed; no setBlock shortcut in AI.
    owner.teleport(world, 0.5, 68, 0.5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    bot.teleport(world, 0.5, 64, 0.5, Set.of(), 0, 0, false);
    bot.onTeleportationDone();
    world.setBlockState(new BlockPos(0, 68, 0), Blocks.COBWEB.getDefaultState(), 3);
    bot.getInventory()
        .setStack(5, new net.minecraft.item.ItemStack(net.minecraft.item.Items.BLACK_WOOL, 8));
    var scaffold = Session.class.getDeclaredMethod("scaffold", int.class);
    scaffold.setAccessible(true);
    if (!(boolean) scaffold.invoke(DuckBox.session, 1000))
      throw new AssertionError("Tower must start from floor");
    bot.teleport(world, 0.5, 65.1, 0.5, Set.of(), 0, 0, false);
    bot.onTeleportationDone();
    if (!(boolean) scaffold.invoke(DuckBox.session, 1005)
        || !world.getBlockState(new BlockPos(0, 64, 0)).isOf(Blocks.BLACK_WOOL)
        || bot.getInventory().getStack(5).getCount() != 7)
      throw new AssertionError("Native tower stock/placement");
    DuckBox.session.cleanupBuilding();
    if (!world.getBlockState(new BlockPos(0, 64, 0)).isAir())
      throw new AssertionError("Tower cleanup");
    bot.teleport(world, 1.5, 67, 0.5, Set.of(), 90, 0, false);
    bot.onTeleportationDone();
    var breakWeb = Session.class.getDeclaredMethod("breakTargetWeb");
    breakWeb.setAccessible(true);
    if ((boolean) breakWeb.invoke(DuckBox.session))
      throw new AssertionError("Never break web from below/air route");
    var routeField = Session.class.getDeclaredField("webRoute");
    routeField.setAccessible(true);
    routeField.set(DuckBox.session, java.lang.Enum.valueOf((Class) routeField.getType(), "TOWER"));
    bot.teleport(world, 1.5, 68, 0.5, Set.of(), 90, 0, false);
    bot.onTeleportationDone();
    bot.setOnGround(true);
    var builtField = Session.class.getDeclaredField("builtBlocks");
    builtField.setAccessible(true);
    ((Map) builtField.get(DuckBox.session))
        .put(new BlockPos(1, 67, 0), Blocks.BLACK_WOOL.getDefaultState());
    world.setBlockState(new BlockPos(1, 67, 0), Blocks.BLACK_WOOL.getDefaultState(), 3);
    boolean triedBreak = false;
    for (int n = 0;
        n < 400 && world.getBlockState(new BlockPos(0, 68, 0)).isOf(Blocks.COBWEB);
        n++) {
      ticks.setInt(server, 1000 + n);
      bot.interactionManager.update();
      triedBreak |= (boolean) breakWeb.invoke(DuckBox.session);
    }
    if (!triedBreak || !world.getBlockState(new BlockPos(0, 68, 0)).isAir())
      throw new AssertionError("Native web destruction");
    owner.teleport(world, 0.5, 64, 0.5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    bot.teleport(world, 1.5, 64, 0.5, Set.of(), 0, 0, false);
    bot.onTeleportationDone();
    world.setBlockState(new BlockPos(0, 65, -1), Blocks.STONE.getDefaultState(), 3);
    bot.setOnGround(true);
    var placeWeb = Session.class.getDeclaredMethod("placeWeb", BlockPos.class, int.class);
    placeWeb.setAccessible(true);
    if ((boolean) placeWeb.invoke(DuckBox.session, owner.getBlockPos(), 1990))
      throw new AssertionError("No web at feet/floor");
    owner.startGliding();
    owner.setPose(net.minecraft.entity.EntityPose.GLIDING);
    options.tank = true;
    if ((boolean) placeWeb.invoke(DuckBox.session, BlockPos.ofFloored(owner.getEyePos()), 1991))
      throw new AssertionError("No floor web when head shares feet block, including Tank");
    owner.stopGliding();
    owner.setPose(net.minecraft.entity.EntityPose.STANDING);
    options.tank = false;
    if (!(boolean) placeWeb.invoke(DuckBox.session, BlockPos.ofFloored(owner.getEyePos()), 2000)
        || !world.getBlockState(BlockPos.ofFloored(owner.getEyePos())).isOf(Blocks.COBWEB))
      throw new AssertionError("Head web placement");
    bot.setOnGround(false);
    if ((boolean) placeWeb.invoke(DuckBox.session, new BlockPos(1, 65, -1), 2010))
      throw new AssertionError("Airborne bot must not web");
    bot.setOnGround(true);
    if ((boolean) placeWeb.invoke(DuckBox.session, new BlockPos(0, 67, 0), 2010))
      throw new AssertionError("Web above three blocks must be refused");
    bot.getInventory()
        .setStack(5, new net.minecraft.item.ItemStack(net.minecraft.item.Items.BLACK_WOOL, 8));
    var cage = Session.class.getDeclaredMethod("cageHead", int.class);
    cage.setAccessible(true);
    if ((boolean) cage.invoke(DuckBox.session, 2020)
        || (boolean) cage.invoke(DuckBox.session, 2079))
      throw new AssertionError("Head cage must wait three seconds");
    if (!(boolean) cage.invoke(DuckBox.session, 2080)
        || !world.getBlockState(new BlockPos(0, 66, 0)).isOf(Blocks.BLACK_WOOL)
        || bot.getInventory().getStack(5).getCount() != 7)
      throw new AssertionError("Head cage must place black wool after three seconds");
    DuckBox.session.cleanupBuilding();
    var webMelee = Session.class.getDeclaredMethod("canHit");
    webMelee.setAccessible(true);
    bot.setPose(net.minecraft.entity.EntityPose.STANDING);
    owner.setPose(net.minecraft.entity.EntityPose.STANDING);
    bot.setYaw(90);
    bot.setHeadYaw(90);
    bot.setPitch(0);
    if ((boolean) webMelee.invoke(DuckBox.session))
      throw new AssertionError("No hit through head web");
    bot.setPitch(56);
    if (!(boolean) webMelee.invoke(DuckBox.session))
      throw new AssertionError(
          "Exposed feet must remain hittable below head web: eye="
              + bot.getEyePos()
              + " rotation="
              + bot.getRotationVec(1)
              + " bbox="
              + owner.getBoundingBox()
              + " owner="
              + owner.getPos());
    world.setBlockState(new BlockPos(0, 65, -1), Blocks.AIR.getDefaultState(), 3);
    world.setBlockState(BlockPos.ofFloored(owner.getEyePos()), Blocks.AIR.getDefaultState(), 3);
    // Full AI/physics route, not just a direct placement helper: black wool must become a tower.
    owner.teleport(world, 0.5, 68, 0.5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    bot.teleport(world, 1.5, 64, 0.5, Set.of(), 90, 0, false);
    bot.onTeleportationDone();
    bot.setVelocity(net.minecraft.util.math.Vec3d.ZERO);
    bot.setOnGround(true);
    bot.stopGliding();
    bot.clearStatusEffects();
    bot.setHealth(bot.getMaxHealth());
    bot.getInventory()
        .setStack(5, new net.minecraft.item.ItemStack(net.minecraft.item.Items.BLACK_WOOL, 32));
    world.setBlockState(new BlockPos(0, 69, 0), Blocks.COBWEB.getDefaultState(), 3);
    options.gap = false;
    options.retotem = false;
    options.giro = false;
    options.teia = false;
    DuckBox.session = new Session(owner, bot, options);
    routeField.set(DuckBox.session, java.lang.Enum.valueOf((Class) routeField.getType(), "TOWER"));
    var routeTargetField = Session.class.getDeclaredField("routeTarget");
    routeTargetField.setAccessible(true);
    routeTargetField.set(DuckBox.session, new BlockPos(0, 69, 0));
    var routeUntilField = Session.class.getDeclaredField("routeUntil");
    routeUntilField.setAccessible(true);
    routeUntilField.setInt(DuckBox.session, 10000);
    boolean climbed = false, brokeAfterTower = false;
    for (int n = 0; n < 300; n++) {
      ticks.setInt(server, 3000 + n);
      bot.tick();
      if (bot.getY() >= 67.4 && bot.getInventory().getStack(5).getCount() < 32) climbed = true;
      if (world.getBlockState(new BlockPos(0, 69, 0)).isAir()) {
        if (!climbed || bot.getY() < 67.4)
          throw new AssertionError("Web broken before completing tower");
        brokeAfterTower = true;
        break;
      }
    }
    if (!climbed || !brokeAfterTower)
      throw new AssertionError(
          "Full tower must finish and mine target web: bot="
              + bot.getPos()
              + " stock="
              + bot.getInventory().getStack(5));
    owner.timeUntilRegen = 0;
    float towerTargetBefore = owner.getHealth() + owner.getAbsorptionAmount();
    boolean hitAfterTower = false;
    int afterTowerTick = server.getTicks();
    for (int n = 0; n < 30; n++) {
      ticks.setInt(server, afterTowerTick + 1 + n);
      bot.tick();
      if (owner.getHealth() + owner.getAbsorptionAmount() < towerTargetBefore) {
        hitAfterTower = true;
        break;
      }
    }
    if (!hitAfterTower)
      throw new AssertionError("Bot must attack after finishing tower and breaking web");
    DuckBox.session.cleanupBuilding();
    world.setBlockState(new BlockPos(0, 69, 0), Blocks.AIR.getDefaultState(), 3);
    DuckBox.session.closed = true;
    DuckBox.session = new Session(owner, bot, options);
    System.out.println(
        "PASS FULL NATIVE NAVIGATION: AI completed black-wool tower, mined web after landing and"
            + " attacked target with real ticks/physics");
    owner.getInventory().selectedSlot = 2;
    owner
        .getInventory()
        .setStack(2, new net.minecraft.item.ItemStack(net.minecraft.item.Items.FIREWORK_ROCKET, 8));
    owner.startGliding();
    if (!DuckBox.useFlyingRocket(owner, net.minecraft.util.Hand.MAIN_HAND).isAccepted()
        || owner.getMainHandStack().getCount() != 7)
      throw new AssertionError("Flying block click must use rocket once");
    owner.stopGliding();
    if (DuckBox.useFlyingRocket(owner, net.minecraft.util.Hand.MAIN_HAND).isAccepted())
      throw new AssertionError("Ground rocket should keep vanilla behavior");
    System.out.println(
        "PASS REAL WEB AI: head placement, native tower stock/cleanup, native web break, airborne"
            + " rocket use");
    DuckBox.session.closed = true;
    DuckBox.session = null;
    options.tank = true;
    options.gap = true;
    options.giro = true;
    options.retotem = false;
    owner.teleport(world, 4.5, 64, 4.5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    bot.teleport(world, 0.5, 68, 0.5, Set.of(), 0, 0, false);
    bot.onTeleportationDone();
    bot.setVelocity(net.minecraft.util.math.Vec3d.ZERO);
    bot.setOnGround(false);
    bot.startGliding();
    bot.clearStatusEffects();
    bot.setHealth(bot.getMaxHealth());
    bot.setAbsorptionAmount(0);
    bot.getInventory()
        .setStack(
            2,
            new net.minecraft.item.ItemStack(net.minecraft.item.Items.ENCHANTED_GOLDEN_APPLE, 32));
    DuckBox.session = new Session(owner, bot, options);
    var groundAt = Session.class.getDeclaredField("tankGroundAt");
    groundAt.setAccessible(true);
    groundAt.setInt(DuckBox.session, 0);
    boolean landedForGap = false, ateGroundGap = false, resumedFlight = false;
    float tankOwnerHealth = owner.getHealth();
    for (int n = 0; n < 150; n++) {
      ticks.setInt(server, 6000 + n);
      bot.tick();
      if (bot.isUsingItem()
          && bot.getActiveItem().isOf(net.minecraft.item.Items.ENCHANTED_GOLDEN_APPLE)) {
        if (!bot.isOnGround()) throw new AssertionError("Tank ground gap started before landing");
        landedForGap = true;
      }
      if (bot.getInventory().getStack(2).getCount() == 31) ateGroundGap = true;
      if (ateGroundGap && bot.isGliding()) {
        resumedFlight = true;
        break;
      }
    }
    if (!landedForGap || !ateGroundGap || !resumedFlight || owner.getHealth() != tankOwnerHealth)
      throw new AssertionError(
          "Tank must land, eat one real apple, resume flight without attacking: "
              + landedForGap
              + "/"
              + ateGroundGap
              + "/"
              + resumedFlight
              + " pos="
              + bot.getPos());
    DuckBox.session.closed = true;
    DuckBox.session = null;
    options.tank = false;
    options.gap = false;
    System.out.println(
        "PASS REAL TANK CYCLE: descent from flight, grounded consumption of one apple, return to"
            + " elytra and no attacks");
    // A bot has no client loading ACK: test receiving real player attacks after a fresh load.
    bot.session = null;
    bot.setLoaded(false);
    bot.clearStatusEffects();
    bot.setAbsorptionAmount(0);
    bot.setHealth(bot.getMaxHealth());
    bot.timeUntilRegen = 0;
    owner.clearStatusEffects();
    owner.setLoaded(true);
    owner.getInventory().selectedSlot = 0;
    owner.setSprinting(false);
    ticks.setInt(server, 4000);
    bot.tick();
    if (!bot.isLoaded() || bot.isInTeleportationState())
      throw new AssertionError("Bot must acknowledge its own load/teleport");
    float beforeIncoming = bot.getHealth();
    owner.attack(bot);
    if (bot.getHealth() >= beforeIncoming)
      throw new AssertionError("Player hit rejected after fresh bot load");
    float afterIncoming = bot.getHealth();
    owner.attack(bot);
    if (bot.getHealth() != afterIncoming)
      throw new AssertionError("Vanilla equal-hit immunity must remain");
    for (int n = 0; n < 12; n++) {
      ticks.setInt(server, 4001 + n);
      bot.tick();
      owner.tick();
      owner.playerTick();
    }
    float beforeNextHit = bot.getHealth();
    owner.attack(bot);
    if (bot.getHealth() >= beforeNextHit)
      throw new AssertionError("Player hit rejected after vanilla immunity elapsed");
    System.out.println(
        "PASS REAL INCOMING HITS: fresh bot load accepts player attack immediately; vanilla"
            + " immunity preserved and later hits accepted");
    var countdownSession = new Session(owner, bot, options);
    DuckBox.session = countdownSession;
    owner.clearStatusEffects();
    bot.clearStatusEffects();
    countdownSession.beginCountdown();
    if (!countdownSession.countingDown()
        || owner.distanceTo(bot) < options.size - 4
        || Math.abs(owner.getZ() - (options.z + 0.5)) > 0.001
        || Math.abs(bot.getZ() - owner.getZ()) > 0.001
        || DuckBox.allowTrainingDamage(owner, world.getDamageSources().playerAttack(bot)))
      throw new AssertionError("Countdown corners/protection");
    owner.setPosition(owner.getPos().add(1, 0, 0));
    countdownSession.control();
    double offset = options.size / 2.0 - 1.5;
    if (Math.abs(owner.getX() - (options.x - offset)) > 0.001
        || owner.hasStatusEffect(net.minecraft.entity.effect.StatusEffects.REGENERATION))
      throw new AssertionError("Countdown must hold corner and postpone buffs");
    for (int n = 1; n < 99; n++) countdownSession.control();
    if (!countdownSession.countingDown())
      throw new AssertionError("Countdown shorter than100ticks");
    countdownSession.control();
    if (countdownSession.countingDown()
        || !owner.hasStatusEffect(net.minecraft.entity.effect.StatusEffects.REGENERATION)
        || !DuckBox.allowTrainingDamage(owner, world.getDamageSources().playerAttack(bot)))
      throw new AssertionError("Countdown did not release combat/buffs after100ticks");
    bot.setHealth(bot.getMaxHealth() - 10);
    owner.setHealth(owner.getMaxHealth() - 10);
    float botAfterStart = bot.getHealth(), ownerAfterStart = owner.getHealth();
    countdownSession.control();
    countdownSession.control();
    countdownSession.control();
    if (bot.getHealth() > botAfterStart || owner.getHealth() > ownerAfterStart)
      throw new AssertionError("Opening hits must not be erased by startup health resets");
    owner.teleport(world, 0.5, 64, 3.4, Set.of(), 180, 0, false);
    owner.onTeleportationDone();
    bot.teleport(world, 0.5, 64, 0.5, Set.of(), 0, 0, false);
    bot.onTeleportationDone();
    owner.stopGliding();
    bot.stopGliding();
    owner.setPose(net.minecraft.entity.EntityPose.STANDING);
    bot.setPose(net.minecraft.entity.EntityPose.STANDING);
    var canHit = Session.class.getDeclaredMethod("canHit");
    canHit.setAccessible(true);
    options.wtap = false;
    if ((boolean) canHit.invoke(countdownSession))
      throw new AssertionError("Wtap-off must close before hitting");
    options.wtap = true;
    if (!(boolean) canHit.invoke(countdownSession))
      throw new AssertionError("Wtap-on should allow normal reach");
    world.setBlockState(new BlockPos(0, 65, 2), Blocks.COBWEB.getDefaultState(), 3);
    if ((boolean) canHit.invoke(countdownSession))
      throw new AssertionError("Melee ray must not pass through full web");
    world.setBlockState(new BlockPos(0, 65, 2), Blocks.AIR.getDefaultState(), 3);
    owner.setPosition(0.5, 64, 4.0);
    if ((boolean) canHit.invoke(countdownSession))
      throw new AssertionError("Bot must not exceed3block ray reach");
    countdownSession.closed = true;
    DuckBox.session = null;
    System.out.println(
        "PASS REAL COUNTDOWN/REACH:100ticks, opposite corners, hold/protection/buffs, short reach"
            + " without Wtap and3block cap with Wtap");
    DuckBox.session = new Session(owner, bot, options);
    owner.teleport(world, 0.5, 64, 3.5, Set.of(), 180, 0, false);
    owner.onTeleportationDone();
    bot.teleport(world, 0.5, 64, 0.5, Set.of(), 0, 0, false);
    bot.onTeleportationDone();
    bot.setPose(net.minecraft.entity.EntityPose.STANDING);
    bot.setOnGround(true);
    var woolBreak = Session.class.getDeclaredMethod("breakBlockingWool");
    woolBreak.setAccessible(true);
    BlockPos woolPos = new BlockPos(0, 65, 2);
    world.setBlockState(woolPos, Blocks.BLACK_WOOL.getDefaultState(), 3);
    for (int n = 0; n < 200 && !world.getBlockState(woolPos).isAir(); n++) {
      ticks.setInt(server, 8000 + n);
      bot.interactionManager.update();
      woolBreak.invoke(DuckBox.session);
    }
    if (!world.getBlockState(woolPos).isAir()) throw new AssertionError("Native wool break failed");
    int woolFinishedAt = server.getTicks();
    world.setBlockState(woolPos, Blocks.RED_WOOL.getDefaultState(), 3);
    for (int n = 0; n < 5; n++) {
      ticks.setInt(server, woolFinishedAt + n);
      if ((boolean) woolBreak.invoke(DuckBox.session))
        throw new AssertionError("Missing five-tick break pause");
    }
    ticks.setInt(server, woolFinishedAt + 5);
    if (!(boolean) woolBreak.invoke(DuckBox.session) || world.getBlockState(woolPos).isAir())
      throw new AssertionError("New wool mining must begin progressively, not instant");
    world.setBlockState(woolPos, Blocks.STONE.getDefaultState(), 3);
    if ((boolean) woolBreak.invoke(DuckBox.session)
        || !world.getBlockState(woolPos).isOf(Blocks.STONE))
      throw new AssertionError("Bot must not break other materials");
    world.setBlockState(woolPos, Blocks.AIR.getDefaultState(), 3);
    int placedColors = 0;
    for (var block : net.minecraft.registry.Registries.BLOCK) {
      if (block.getDefaultState().isIn(net.minecraft.registry.tag.BlockTags.WOOL)) {
        world.setBlockState(
            new BlockPos(-3 + placedColors % 4, 64, -3 + placedColors / 4),
            block.getDefaultState(),
            3);
        placedColors++;
      }
    }
    if (placedColors != 16) throw new AssertionError("Expected all16 wool colors");
    world.setBlockState(new BlockPos(2, 64, 2), Blocks.COBWEB.getDefaultState(), 3);
    BlockPos preserved = new BlockPos(3, 64, 3);
    world.setBlockState(preserved, Blocks.STONE.getDefaultState(), 3);
    Arena.clearWebs(world, options);
    for (int n = 0; n < 16; n++)
      if (!world.getBlockState(new BlockPos(-3 + n % 4, 64, -3 + n / 4)).isAir())
        throw new AssertionError("Wool cleanup color" + n);
    if (!world.getBlockState(new BlockPos(2, 64, 2)).isAir()
        || !world.getBlockState(preserved).isOf(Blocks.STONE)
        || !world.getBlockState(new BlockPos(0, 63, 0)).isOf(Blocks.STONE))
      throw new AssertionError(
          "Cleanup must remove only wool/web and preserve other materials/floor");
    DuckBox.session.closed = true;
    DuckBox.session = null;
    System.out.println(
        "PASS WOOL: native black wool destruction, other blocks rejected, all16 colors/web cleaned"
            + " with floor/stone preserved");
    bot.session = null;
    options.rules = Options.Rules.NORMAL_SPAM;
    var cooldownSession = new Session(owner, bot, options);
    cooldownSession.closed = true;
    var ready = Session.class.getDeclaredMethod("readyToAttack");
    ready.setAccessible(true);
    var oldElytra = bot.getEquippedStack(net.minecraft.entity.EquipmentSlot.CHEST).copy();
    bot.equipStack(net.minecraft.entity.EquipmentSlot.CHEST, net.minecraft.item.ItemStack.EMPTY);
    ticks.setInt(server, 10000);
    bot.tick();
    bot.resetLastAttackedTicks();
    for (int n = 0; n < 20; n++)
      if ((boolean) ready.invoke(cooldownSession))
        throw new AssertionError(
            "Normal must respect uncharged vanilla attack on every scheduled attempt");
    for (int n = 0; n < 13; n++) {
      ticks.setInt(server, 10001 + n);
      bot.tick();
    }
    int chargedNormal = 0;
    for (int n = 0; n < 20; n++) if ((boolean) ready.invoke(cooldownSession)) chargedNormal++;
    if (chargedNormal != 15)
      throw new AssertionError("Normal must schedule15 attacks when natively charged");
    bot.equipStack(net.minecraft.entity.EquipmentSlot.CHEST, oldElytra);
    ticks.setInt(server, 10020);
    bot.tick();
    bot.resetLastAttackedTicks();
    ticks.setInt(server, 10021);
    bot.tick();
    int elytraNormal = 0;
    for (int n = 0; n < 20; n++) if ((boolean) ready.invoke(cooldownSession)) elytraNormal++;
    if (elytraNormal != 15)
      throw new AssertionError("Normal with255 attack speed must retain15 CPS");
    options.rules = Options.Rules.INSTA_KILL;
    var instaCadenceSession = new Session(owner, bot, options);
    instaCadenceSession.closed = true;
    int instaAttempts = 0;
    for (int n = 0; n < 20; n++) if ((boolean) ready.invoke(instaCadenceSession)) instaAttempts++;
    if (instaAttempts != 15)
      throw new AssertionError("Insta Kill cadence changed: " + instaAttempts);
    options.rules = Options.Rules.NORMAL_SPAM;
    System.out.println(
        "PASS COMBAT RULES: both modes15/20 attempts; Normal also respects native cooldown and"
            + " elytra attack speed; Insta Kill unchanged");
    options.tank = false;
    options.gap = false;
    options.giro = false;
    options.teia = false;
    options.retotem = false;
    options.strafe = false;
    bot.teleport(world, 0.5, 64, 0.5, Set.of(), 180, 0, false);
    bot.onTeleportationDone();
    owner.teleport(world, 0.5, 64, 6.5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    float clickTargetHealth = owner.getHealth();
    for (var mode : Options.Rules.values()) {
      options.rules = mode;
      var swingSession = new Session(owner, bot, options);
      DuckBox.session = swingSession;
      int swings = 0;
      for (int n = 0; n < 20; n++) {
        bot.handSwinging = false;
        swingSession.control();
        if (bot.handSwinging) swings++;
      }
      if (swings != 15 || owner.getHealth() != clickTargetHealth)
        throw new AssertionError(
            "At6blocks must swing15 times without remote damage: " + mode + " swings=" + swings);
      owner.setPosition(0.5, 64, 6.6);
      for (int n = 0; n < 20; n++) {
        bot.handSwinging = false;
        swingSession.control();
        if (bot.handSwinging) throw new AssertionError("No clicks beyond6blocks");
      }
      swingSession.closed = true;
      owner.setPosition(0.5, 64, 6.5);
    }
    DuckBox.session = null;
    options.rules = Options.Rules.NORMAL_SPAM;
    System.out.println(
        "PASS CLICK RANGE: both modes15 native swings at6blocks, no remote damage, no clicks"
            + " beyond6blocks");
    bot.session = null;
    var correctedKit = Kits.defaults(world.getRegistryManager(), Options.Rules.NORMAL_SPAM);
    var savedNormalChest = correctedKit.get(38).copy();
    correctedKit.set(38, net.minecraft.item.ItemStack.EMPTY);
    Kits.give(bot, correctedKit);
    ticks.setInt(server, 11000);
    bot.tick();
    double normalSpeed =
        bot.getAttributeValue(net.minecraft.entity.attribute.EntityAttributes.ATTACK_SPEED);
    if (Math.abs(normalSpeed - 1.6) > 0.001)
      throw new AssertionError(
          "Normal gold sword must have native1.6 attack speed without elytra: " + normalSpeed);
    bot.resetLastAttackedTicks();
    if (bot.getAttackCooldownProgress(0.5f) >= 0.3)
      throw new AssertionError("Normal sword cooldown must recover gradually");
    for (int n = 0; n < 13; n++) {
      ticks.setInt(server, 11001 + n);
      bot.tick();
    }
    if (bot.getAttackCooldownProgress(0.5f) < 1)
      throw new AssertionError("Native sword recovery failed");
    bot.equipStack(net.minecraft.entity.EquipmentSlot.CHEST, savedNormalChest);
    ticks.setInt(server, 11020);
    bot.tick();
    if (Math.abs(
            bot.getAttributeValue(net.minecraft.entity.attribute.EntityAttributes.ATTACK_SPEED)
                - 256.6)
        > 0.001) throw new AssertionError("Elytra must add255 only while equipped");
    bot.equipStack(net.minecraft.entity.EquipmentSlot.CHEST, net.minecraft.item.ItemStack.EMPTY);
    ticks.setInt(server, 11021);
    bot.tick();
    if (Math.abs(
            bot.getAttributeValue(net.minecraft.entity.attribute.EntityAttributes.ATTACK_SPEED)
                - 1.6)
        > 0.001) throw new AssertionError("Elytra speed leaked after removal");
    bot.getInventory().selectedSlot = 4;
    bot.getInventory().setStack(4, net.minecraft.item.ItemStack.EMPTY);
    ticks.setInt(server, 11022);
    bot.tick();
    if (Math.abs(
            bot.getAttributeValue(net.minecraft.entity.attribute.EntityAttributes.ATTACK_SPEED) - 4)
        > 0.001) throw new AssertionError("Empty hand must keep vanilla4 attack speed");
    var legacyNormal = Kits.defaults(world.getRegistryManager(), Options.Rules.INSTA_KILL);
    var legacyHead = legacyNormal.get(39).copy();
    if (!Kits.repairNormalKit(legacyNormal)
        || Kits.repairNormalKit(legacyNormal)
        || !net.minecraft.item.ItemStack.areEqual(legacyHead, legacyNormal.get(39)))
      throw new AssertionError(
          "Normal kit migration must be idempotent and preserve other kit items");
    System.out.println(
        "PASS NATIVE PLAYER COOLDOWN: sword1.6, elytra256.6, removal1.6, empty hand4, saved-kit"
            + " repair idempotent");
    var doRetotem = Session.class.getDeclaredMethod("retotem", int.class);
    doRetotem.setAccessible(true);
    var rngField = Session.class.getDeclaredField("random");
    rngField.setAccessible(true);
    long failSeed = 0;
    while (new java.util.Random(failSeed).nextDouble() >= 0.20) failSeed++;
    options.difficulty = Options.Difficulty.MEDIUM;
    Kits.give(bot, Kits.defaults(world.getRegistryManager(), Options.Rules.NORMAL_SPAM));
    bot.setHealth(1);
    var mediumSwap = new Session(owner, bot, options);
    ((java.util.Random) rngField.get(mediumSwap)).setSeed(failSeed);
    doRetotem.invoke(mediumSwap, 0);
    doRetotem.invoke(mediumSwap, options.difficulty.swapDelay);
    if (!Kits.isCharm(bot.getOffHandStack()) || mediumSwap.countTotems() != 12)
      throw new AssertionError("Medium failed roll must preserve items and miss transfer");
    int retryAt = options.difficulty.swapDelay + options.difficulty.reaction;
    if ((boolean) doRetotem.invoke(mediumSwap, retryAt - 1))
      throw new AssertionError("Medium failure needs retry delay");
    ((java.util.Random) rngField.get(mediumSwap)).setSeed(0);
    doRetotem.invoke(mediumSwap, retryAt);
    doRetotem.invoke(mediumSwap, retryAt + options.difficulty.swapDelay);
    if (!bot.getOffHandStack().isOf(net.minecraft.item.Items.TOTEM_OF_UNDYING)
        || mediumSwap.countTotems() != 12)
      throw new AssertionError("Medium must recover with successful next roll and no duplicates");
    for (var level : List.of(Options.Difficulty.HIGH, Options.Difficulty.EXPERT)) {
      options.difficulty = level;
      Kits.give(bot, Kits.defaults(world.getRegistryManager(), Options.Rules.NORMAL_SPAM));
      bot.setHealth(1);
      var reliableSwap = new Session(owner, bot, options);
      ((java.util.Random) rngField.get(reliableSwap)).setSeed(failSeed);
      doRetotem.invoke(reliableSwap, 0);
      doRetotem.invoke(reliableSwap, level.swapDelay);
      if (!bot.getOffHandStack().isOf(net.minecraft.item.Items.TOTEM_OF_UNDYING)
          || reliableSwap.countTotems() != 12)
        throw new AssertionError("High/Expert cannot randomly miss retotem");
      reliableSwap.closed = true;
    }
    mediumSwap.closed = true;
    options.difficulty = Options.Difficulty.HIGH;
    System.out.println(
        "PASS RETOTEM DIFFICULTY: seeded Medium20percent failure preserves stock, retries"
            + " successfully; High/Expert do not randomly miss");
    options.difficulty = Options.Difficulty.HIGH;
    options.retotem = true;
    options.gap = false;
    options.giro = false;
    options.tank = true;
    Kits.give(bot, Kits.defaults(world.getRegistryManager(), Options.Rules.NORMAL_SPAM));
    bot.setHealth(1);
    bot.clearStatusEffects();
    bot.setAbsorptionAmount(0);
    DuckBox.session = new Session(owner, bot, options);
    int refillTick = 12000;
    for (int pop = 0; pop < 12; pop++) {
      boolean readyTotem = false;
      for (int n = 0; n < 100; n++) {
        ticks.setInt(server, refillTick++);
        bot.tick();
        if (bot.getOffHandStack().isOf(net.minecraft.item.Items.TOTEM_OF_UNDYING)
            && !bot.getMainHandStack().isOf(net.minecraft.item.Items.TOTEM_OF_UNDYING)) {
          readyTotem = true;
          break;
        }
      }
      if (!readyTotem) throw new AssertionError("No retotem/refill for pop " + pop);
      if (pop == 2) {
        for (int n = 0; n < 20; n++) {
          ticks.setInt(server, refillTick++);
          bot.tick();
        }
        int hotTotems = 0;
        for (int i = 0; i < 9; i++)
          if (bot.getInventory().getStack(i).isOf(net.minecraft.item.Items.TOTEM_OF_UNDYING))
            hotTotems++;
        if (hotTotems != 3
            || DuckBox.session.refillCount() < 1
            || !bot.getOffHandStack().isOf(net.minecraft.item.Items.TOTEM_OF_UNDYING))
          throw new AssertionError(
              "Refill must happen proactively while offhand is still protected");
      }
      int beforePop = DuckBox.session.countTotems();
      bot.timeUntilRegen = 0;
      bot.clearStatusEffects();
      bot.setAbsorptionAmount(0);
      bot.setHealth(1);
      if (!DuckBox.allowTrainingDeath(bot, world.getDamageSources().generic(), 1000000)
          || !bot.damage(world, world.getDamageSources().generic(), 1000000)
          || bot.getHealth() <= 0
          || DuckBox.session.countTotems() != beforePop - 1)
        throw new AssertionError("Real vanilla totem pop/conservation failed at " + pop);
    }
    if (DuckBox.session.countTotems() != 0 || DuckBox.session.refillCount() != 3)
      throw new AssertionError(
          "Expected all12 totems consumed and three reserve refills: "
              + DuckBox.session.countTotems()
              + "/"
              + DuckBox.session.refillCount());
    for (int n = 0; n < 30; n++) {
      ticks.setInt(server, refillTick++);
      bot.tick();
    }
    if (DuckBox.session.countTotems() != 0)
      throw new AssertionError("Refill must not generate new totems");
    DuckBox.session.closed = true;
    DuckBox.session = null;
    options.tank = false;
    options.retotem = false;
    System.out.println(
        "PASS FULL RETOTEM/REFILL:12 real vanilla pops, proactive3-totem refill while protected,"
            + " three refills, stock exhausted without duplication");
    var phaseField = Session.class.getDeclaredField("phase");
    phaseField.setAccessible(true);
    options.rules = Options.Rules.NORMAL_SPAM;
    var hudSession = new Session(owner, bot, options);
    phaseField.set(hudSession, "Combate");
    String actionBar = hudSession.statusText().getString();
    if (!actionBar.contains("Spam")
        || !actionBar.contains("◆")
        || !actionBar.contains("↻")
        || actionBar.contains("NORMAL_SPAM")
        || actionBar.contains("Combate")
        || actionBar.contains(" | Bot "))
      throw new AssertionError("Actionbar labels/icons/remove combat and HP: " + actionBar);
    if (Options.Rules.parse("SPAM") != Options.Rules.NORMAL_SPAM
        || Options.Rules.parse("NORMAL_SPAM") != Options.Rules.NORMAL_SPAM)
      throw new AssertionError("Spam alias and old profiles must remain compatible");
    for (var level : Options.Difficulty.values()) {
      options.difficulty = level;
      Kits.give(bot, Kits.defaults(world.getRegistryManager(), Options.Rules.NORMAL_SPAM));
      for (int i = 6; i <= 8; i++)
        bot.getInventory().setStack(i, net.minecraft.item.ItemStack.EMPTY);
      bot.getInventory()
          .setStack(
              40, new net.minecraft.item.ItemStack(net.minecraft.item.Items.TOTEM_OF_UNDYING));
      bot.setHealth(1);
      var timedRefill = new Session(owner, bot, options);
      int before = timedRefill.countTotems();
      doRetotem.invoke(timedRefill, 0);
      if (timedRefill.refillCount() != 0)
        throw new AssertionError("Refill cannot complete instantly");
      doRetotem.invoke(timedRefill, level.refillDelayTicks() - 1);
      if (timedRefill.refillCount() != 0)
        throw new AssertionError("Refill completed before difficulty delay");
      doRetotem.invoke(timedRefill, level.refillDelayTicks());
      if (timedRefill.refillCount() != 1 || timedRefill.countTotems() != before)
        throw new AssertionError("Timed refill failed for " + level);
      timedRefill.closed = true;
    }
    options.difficulty = Options.Difficulty.HIGH;
    options.tank = false;
    options.retotem = false;
    options.gap = true;
    options.giro = true;
    Kits.give(bot, Kits.defaults(world.getRegistryManager(), Options.Rules.NORMAL_SPAM));
    owner.teleport(world, 0.5, 64, 0.5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    bot.teleport(world, 4.9, 64, 4.9, Set.of(), 0, -85, false);
    bot.onTeleportationDone();
    bot.setOnGround(true);
    bot.setVelocity(net.minecraft.util.math.Vec3d.ZERO);
    bot.stopGliding();
    bot.setHealth(30);
    bot.clearStatusEffects();
    var cornerGap = new Session(owner, bot, options);
    DuckBox.session = cornerGap;
    var escapingField = Session.class.getDeclaredField("escaping");
    escapingField.setAccessible(true);
    escapingField.setBoolean(cornerGap, true);
    var escapeEndField = Session.class.getDeclaredField("escapeUntil");
    escapeEndField.setAccessible(true);
    escapeEndField.setInt(cornerGap, 0);
    var gapsField = Session.class.getDeclaredField("gapsLeft");
    gapsField.setAccessible(true);
    gapsField.setInt(cornerGap, 1);
    var pointField = Session.class.getDeclaredField("recoveryPoint");
    pointField.setAccessible(true);
    pointField.set(cornerGap, new net.minecraft.util.math.Vec3d(4.9, 69.4, 4.9));
    boolean ateInCorner = false;
    for (int n = 0; n < 60; n++) {
      ticks.setInt(server, 14000 + n);
      bot.tick();
      if (bot.getY() > 64.12)
        throw new AssertionError("Ground gap must not loop jumps in corner: " + bot.getPos());
      if (n > 6 && bot.isUsingItem() && bot.getPitch() < -20)
        throw new AssertionError("Ground gap must stop staring at ceiling");
      if (bot.getInventory().getStack(2).getCount() == 31) {
        ateInCorner = true;
        break;
      }
    }
    if (!ateInCorner || bot.getX() >= 4.9 || bot.getZ() >= 4.9)
      throw new AssertionError("Corner recovery must eat and walk inward: " + bot.getPos());
    cornerGap.closed = true;
    DuckBox.session = null;
    options.gap = false;
    System.out.println(
        "PASS UI/REFILL/CORNER: Spam alias, colored icon actionbar without life/combat,"
            + " delays8/5/3/2 ticks, grounded corner apple without repeated jumping/ceiling stare");
    Kits.give(bot, Kits.defaults(world.getRegistryManager(), Options.Rules.NORMAL_SPAM));
    bot.equipStack(net.minecraft.entity.EquipmentSlot.CHEST, net.minecraft.item.ItemStack.EMPTY);
    bot.teleport(world, 0.5, 64, 0.5, Set.of(), 0, 0, false);
    bot.onTeleportationDone();
    bot.setOnGround(true);
    owner.teleport(world, 4.5, 64, 4.5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    world.setBlockState(new BlockPos(0, 64, 0), Blocks.COBWEB.getDefaultState(), 3);
    world.setBlockState(new BlockPos(0, 65, 0), Blocks.COBWEB.getDefaultState(), 3);
    options.gap = false;
    options.retotem = false;
    options.giro = false;
    options.webRocket = true;
    DuckBox.session = new Session(owner, bot, options);
    for (int n = 0;
        n < 220
            && (world.getBlockState(new BlockPos(0, 64, 0)).isOf(Blocks.COBWEB)
                || world.getBlockState(new BlockPos(0, 65, 0)).isOf(Blocks.COBWEB));
        n++) {
      ticks.setInt(server, 15000 + n);
      bot.tick();
    }
    if (world.getBlockState(new BlockPos(0, 64, 0)).isOf(Blocks.COBWEB)
        || world.getBlockState(new BlockPos(0, 65, 0)).isOf(Blocks.COBWEB))
      throw new AssertionError(
          "Bot must actively escape/mine its own web without usable elytra: "
              + bot.getPos()
              + " feet="
              + world.getBlockState(new BlockPos(0, 64, 0))
              + " head="
              + world.getBlockState(new BlockPos(0, 65, 0)));
    DuckBox.session.closed = true;
    // Native move demonstration: packet deltas have already been slowed client-side.
    var slowField = net.minecraft.entity.Entity.class.getDeclaredField("field_17046");
    slowField.setAccessible(true);
    owner.teleport(world, 0.5, 64, 0.5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    slowField.set(owner, DuckBox.WEB_SLOWDOWN);
    owner.move(
        net.minecraft.entity.MovementType.PLAYER, new net.minecraft.util.math.Vec3d(0.2, 0, 0));
    double duplicated = owner.getX() - 0.5;
    owner.teleport(world, 0.5, 64, 0.5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    slowField.set(owner, net.minecraft.util.math.Vec3d.ZERO);
    owner.move(
        net.minecraft.entity.MovementType.PLAYER, new net.minecraft.util.math.Vec3d(0.2, 0, 0));
    if (Math.abs(duplicated - 0.09) > 0.001 || Math.abs(owner.getX() - 0.7) > 0.001)
      throw new AssertionError(
          "Packet web slowdown must be consumed once: " + duplicated + "/" + owner.getPos());
    world.setBlockState(new BlockPos(1, 64, 0), Blocks.STONE.getDefaultState(), 3);
    world.setBlockState(new BlockPos(1, 65, 0), Blocks.STONE.getDefaultState(), 3);
    owner.move(
        net.minecraft.entity.MovementType.PLAYER, new net.minecraft.util.math.Vec3d(1, 0, 0));
    if (owner.getX() > 0.701)
      throw new AssertionError("Normal wall collision must remain enforced");
    world.setBlockState(new BlockPos(1, 64, 0), Blocks.AIR.getDefaultState(), 3);
    world.setBlockState(new BlockPos(1, 65, 0), Blocks.AIR.getDefaultState(), 3);
    DuckBox.session = null;
    System.out.println(
        "PASS WEB RECOVERY/PACKET PHYSICS: bot mines its own webs; native packet0.2 moves0.09 when"
            + " doubled vs0.2 once; walls still collide");
    options.gap = false;
    options.retotem = false;
    options.giro = false;
    options.teia = false;
    options.strafe = false;
    options.tank = false;
    Kits.give(bot, Kits.defaults(world.getRegistryManager(), Options.Rules.NORMAL_SPAM));
    bot.session = null;
    ticks.setInt(server, 17000);
    bot.tick();
    bot.teleport(world, 0.5, 64, 0.5, Set.of(), 180, 0, false);
    bot.onTeleportationDone();
    bot.setVelocity(net.minecraft.util.math.Vec3d.ZERO);
    bot.setOnGround(true);
    owner.teleport(world, 0.5, 64, 6.5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    for (var mode : Options.Rules.values())
      for (int rate : new int[] {10, 13, 15}) {
        options.rules = mode;
        options.cps = rate;
        var selectedCps = new Session(owner, bot, options);
        DuckBox.session = selectedCps;
        int swingCount = 0;
        float healthBefore = owner.getHealth() + owner.getAbsorptionAmount();
        for (int n = 0; n < 40; n++) {
          bot.handSwinging = false;
          selectedCps.control();
          if (bot.handSwinging) swingCount++;
        }
        if (swingCount != 2 * rate
            || owner.getHealth() + owner.getAbsorptionAmount() != healthBefore)
          throw new AssertionError(
              "Selected CPS cadence/range: " + mode + " rate=" + rate + " count=" + swingCount);
        options.cps = 13;
        int switched = 0;
        for (int n = 0; n < 20; n++) {
          bot.handSwinging = false;
          selectedCps.control();
          if (bot.handSwinging) switched++;
        }
        if (switched != 13)
          throw new AssertionError("Live CPS change must apply without catchup burst");
        selectedCps.closed = true;
      }
    DuckBox.session = null;
    options.rules = Options.Rules.NORMAL_SPAM;
    options.cps = 15;
    System.out.println(
        "PASS CPS SELECTOR:10/13/15 rates in both modes, live changes,40tick counts, no damage"
            + " at6blocks");
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
    DuckBox.options = new Options();
    BlockPos customFloor = new BlockPos(-5, 78, 111), customSign = new BlockPos(-32, 79, 120);
    world.setBlockState(customFloor, Blocks.DIAMOND_BLOCK.getDefaultState(), 3);
    world.setBlockState(customSign, Blocks.GOLD_BLOCK.getDefaultState(), 3);
    var beforeBinding = Kits.capture(owner);
    DuckBox.useCustomMap(owner);
    for (int size : new int[] {17, 9, 13}) {
      DuckBox.control(owner, "tamanho");
      if (DuckBox.options.size != size || Arena.building())
        throw new AssertionError("Custom map size must change bounds without building");
    }
    Arena.updateRulesLabel(world, DuckBox.options);
    if (!world.getBlockState(customFloor).isOf(Blocks.DIAMOND_BLOCK)
        || !world.getBlockState(customSign).isOf(Blocks.GOLD_BLOCK)
        || DuckBox.options.x != -5
        || DuckBox.options.y != 78
        || DuckBox.options.z != 111
        || !DuckBox.options.customMap)
      throw new AssertionError("Custom binding must preserve build and fixed floor coordinates");
    for (int i = 0; i < 41; i++)
      if (!net.minecraft.item.ItemStack.areEqual(
          beforeBinding.get(i), owner.getInventory().getStack(i)))
        throw new AssertionError("Custom map binding changed inventory");
    System.out.println(
        "PASS CUSTOM MAP: floor -5/78/111, only9/13/17 bounds, no regeneration, custom"
            + " blocks/sign/inventory preserved");
    DuckBox.setBotCps(owner, 13);
    var savedCps =
        com.google.gson.JsonParser.parseString(Files.readString(config))
            .getAsJsonObject()
            .getAsJsonObject("options")
            .get("cps")
            .getAsInt();
    if (savedCps != 13
        || !new Session(owner, bot, DuckBox.options).statusText().getString().contains("13 CPS"))
      throw new AssertionError("CPS choice must persist and display");
    for (int expected : new int[] {15, 10, 13}) {
      DuckBox.control(owner, "cps");
      if (DuckBox.options.cps != expected) throw new AssertionError("CPS cycle order");
    }
    try {
      DuckBox.setBotCps(owner, 11);
      throw new AssertionError("Invalid CPS accepted");
    } catch (IllegalArgumentException expected) {
    }
    System.out.println(
        "PASS CPS SETTINGS: saved JSON, actionbar value,10/13/15 cycle and invalid rates rejected");
    var boxDispatcher = server.getCommandManager().getDispatcher();
    DuckBox.registerCommands(boxDispatcher);
    BlockPos commandPos = new BlockPos(-100, 78, 111);
    world.setBlockState(commandPos, Blocks.COMMAND_BLOCK.getDefaultState(), 3);
    var commandTile =
        (net.minecraft.block.entity.CommandBlockBlockEntity) world.getBlockEntity(commandPos);
    var blockSource = commandTile.getCommandExecutor().getSource();
    owner.teleport(world, -97.5, 79, 111.5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    bot.teleport(world, -99.5, 79, 111.5, Set.of(), 0, 0, false);
    bot.onTeleportationDone();
    if (blockSource.getEntity() != null || DuckBox.resolveCommandPlayer(blockSource) != owner)
      throw new AssertionError("Real command block must resolve human, not closer bot");
    for (String cmd :
        new String[] {
          "box cps 10",
          "box cps",
          "box dificuldade MEDIUM",
          "box giro EXTREMO",
          "box regras SPAM",
          "box modo TANK",
          "box habilidade wtap",
          "box cosmetico blood"
        })
      if (boxDispatcher.execute(cmd, blockSource) != 1)
        throw new AssertionError("Command block failed: " + cmd);
    if (DuckBox.options.cps != 13
        || DuckBox.options.difficulty != Options.Difficulty.MEDIUM
        || !DuckBox.options.tank) throw new AssertionError("Command block settings not applied");
    if (boxDispatcher.execute("box cps 11", blockSource) != 0 || DuckBox.options.cps != 13)
      throw new AssertionError("Invalid CB option must fail without changing setting");
    if (boxDispatcher.execute("box kit abrir", blockSource) != 1
        || !(owner.currentScreenHandler instanceof KitEditor)
        || !owner.currentScreenHandler.canUse(owner))
      throw new AssertionError("Remote CB kit editor must stay open");
    owner.closeHandledScreen();
    var beforeMenu = Kits.capture(owner);
    if (boxDispatcher.execute("box configurar", blockSource) != 1
        || !(owner.currentScreenHandler instanceof ConfigMenu))
      throw new AssertionError("Command block configuration menu failed");
    var configMenu = owner.currentScreenHandler;
    if (configMenu.getSlot(5).canTakeItems(owner)
        || configMenu
            .getSlot(5)
            .canInsert(new net.minecraft.item.ItemStack(net.minecraft.item.Items.STONE))
        || !configMenu.quickMove(owner, 5).isEmpty())
      throw new AssertionError("Config icons must not be transferable");
    configMenu.onSlotClick(5, 0, net.minecraft.screen.slot.SlotActionType.PICKUP, owner);
    if (DuckBox.options.cps != 15) throw new AssertionError("Config menu CPS selection failed");
    for (int i = 0; i < 41; i++)
      if (!net.minecraft.item.ItemStack.areEqual(
          beforeMenu.get(i), owner.getInventory().getStack(i)))
        throw new AssertionError("Config menu altered player inventory");
    owner.closeHandledScreen();
    if (DuckBox.resolveCommandPlayer(blockSource.withEntity(owner)) != owner)
      throw new AssertionError("Explicit execute-as actor must be respected");
    if (boxDispatcher.execute(
            "box cps 10", blockSource.withWorld(server.getWorld(net.minecraft.world.World.NETHER)))
        != 0) throw new AssertionError("Must not target players in another world");
    try {
      boxDispatcher.execute("box cps 10", owner.getCommandSource().withLevel(0));
      throw new AssertionError("Player permission gate bypassed");
    } catch (com.mojang.brigadier.exceptions.CommandSyntaxException expected) {
    }
    DuckBox.session = new Session(owner, bot, DuckBox.options);
    feedbackConnection.messages.clear();
    DuckBox.options.giro = true;
    DuckBox.control(owner, "giro");
    if (feedbackConnection.chat() || !feedbackConnection.overlay("Giro OFF"))
      throw new AssertionError("Giro OFF must use actionbar only");
    int shown = feedbackConnection.messages.size();
    DuckBox.session.status();
    if (feedbackConnection.messages.size() != shown)
      throw new AssertionError("Status immediately overwrote setting confirmation");
    feedbackConnection.messages.clear();
    DuckBox.control(owner, "giro");
    if (feedbackConnection.chat() || !feedbackConnection.overlay("Giro ON"))
      throw new AssertionError("Giro ON must use actionbar only");
    feedbackConnection.messages.clear();
    DuckBox.setBotCps(owner, 13);
    if (feedbackConnection.chat() || !feedbackConnection.overlay("CPS do bot: 13"))
      throw new AssertionError("CPS setting must use actionbar only");
    ticks.setInt(server, server.getTicks() + 41);
    feedbackConnection.messages.clear();
    DuckBox.session.status();
    if (!feedbackConnection.overlay("Refill"))
      throw new AssertionError("Normal status did not resume after setting display");
    feedbackConnection.messages.clear();
    DuckBox.say(owner, "Ajuda importante");
    if (!feedbackConnection.chat())
      throw new AssertionError("Important messages must remain in chat");
    DuckBox.session.closed = true;
    DuckBox.session = null;
    System.out.println(
        "PASS FEEDBACK PACKETS: GiroON/OFF and CPS only in actionbar, held40ticks before status"
            + " resumes, important help remains chat");
    server.getPlayerManager().remove(bot);
    if (boxDispatcher.execute("box iniciar", blockSource) != 1
        || DuckBox.session == null
        || DuckBox.session.owner != owner
        || !DuckBox.session.countingDown())
      throw new AssertionError("Real command block must start nearest player's round");
    if (boxDispatcher.execute("box parar", blockSource) != 1 || DuckBox.session != null)
      throw new AssertionError("Real command block must stop round and restore player");
    System.out.println(
        "PASS REAL COMMAND BLOCKS: native source/Brigadier start-stop/settings/GUI, excludes NPC,"
            + " explicit actor, same-world targeting, permissions, kit editor remote anchor and"
            + " locked menu icons");
    if (server.getPlayerManager().getPlayer(bot.getUuid()) == bot)
      server.getPlayerManager().remove(bot);

    // Four profile inventories remain isolated and legacy saves migrate to profile1.
    DuckBox.options.rules = Options.Rules.NORMAL_SPAM;
    var oldProfileOne = DuckBox.currentKit(owner, 1);
    for (int id = 1; id <= 4; id++) {
      if (boxDispatcher.execute("box profile " + id, blockSource) != 1
          || DuckBox.options.profile != id)
        throw new AssertionError("Command-block profile selection failed: " + id);
      var profileKit = new ArrayList<>(DuckBox.currentKit(owner));
      profileKit.set(0, new net.minecraft.item.ItemStack(net.minecraft.item.Items.BLACK_WOOL, id));
      DuckBox.storeKit(owner, profileKit);
    }
    for (int id = 1; id <= 4; id++)
      if (DuckBox.currentKit(owner, id).get(0).getCount() != id)
        throw new AssertionError("Profile inventory leaked: " + id);
    if (boxDispatcher.execute(
                "box rename profile 2 <gradient:#ff0000:#0000ff>Treino</gradient>", blockSource)
            != 1
        || !DuckBox.profileName(2).getString().equals("Treino"))
      throw new AssertionError("RGB profile naming failed");
    owner
        .getInventory()
        .setStack(
            owner.getInventory().selectedSlot,
            new net.minecraft.item.ItemStack(net.minecraft.item.Items.GOLDEN_SWORD));
    if (boxDispatcher.execute("box rename &#ffaa00&lPato", blockSource) != 1
        || !owner.getMainHandStack().getName().getString().equals("Pato"))
      throw new AssertionError("Held item naming failed");
    var savedProfiles =
        com.google.gson.JsonParser.parseString(Files.readString(config)).getAsJsonObject();
    if (savedProfiles.getAsJsonObject("kitProfiles").size() != 4
        || savedProfiles.getAsJsonObject("options").get("profile").getAsInt() != 4)
      throw new AssertionError("Profiles did not persist to world config");
    DuckBox.setProfile(owner, 1);
    KitEditor.open(owner, 3);
    owner
        .currentScreenHandler
        .slots
        .get(27)
        .setStack(new net.minecraft.item.ItemStack(net.minecraft.item.Items.WHITE_WOOL, 17));
    owner.closeHandledScreen();
    if (DuckBox.currentKit(owner, 3).get(0).getCount() != 17
        || DuckBox.currentKit(owner, 1).get(0).getCount() != 1
        || DuckBox.options.profile != 1)
      throw new AssertionError(
          "Physical profile editor saved into selected profile instead of its own");

    // Place marked chests using the real vanilla BlockItem placement path.
    for (int id : new int[] {0, 2}) {
      BlockPos base = new BlockPos(-96 + id, 78, 111);
      world.setBlockState(base, Blocks.STONE.getDefaultState(), 3);
      world.setBlockState(base.up(), Blocks.AIR.getDefaultState(), 3);
      var marked = TrainerChests.item(id);
      owner.setStackInHand(net.minecraft.util.Hand.MAIN_HAND, marked);
      var placementHit =
          new net.minecraft.util.hit.BlockHitResult(
              net.minecraft.util.math.Vec3d.ofCenter(base).add(0, .5, 0),
              net.minecraft.util.math.Direction.UP,
              base,
              false);
      var context =
          new net.minecraft.item.ItemPlacementContext(
              owner, net.minecraft.util.Hand.MAIN_HAND, marked, placementHit);
      var result = ((net.minecraft.item.BlockItem) marked.getItem()).place(context);
      if (!result.isAccepted()
          || !(world.getBlockEntity(base.up())
              instanceof net.minecraft.block.entity.ChestBlockEntity placedChest)
          || TrainerChests.profile(placedChest) != id)
        throw new AssertionError("Vanilla placedStockChest placement lost profile marker: " + id);
      var placedStockChest =
          (net.minecraft.block.entity.ChestBlockEntity) world.getBlockEntity(base.up());
      var chestNbt = placedStockChest.createNbtWithIdentifyingData(world.getRegistryManager());
      var visualOnly =
          TrainerChests.visualData(
              placedStockChest, world.getRegistryManager(), new net.minecraft.nbt.NbtCompound());
      var visualClientChest =
          new net.minecraft.block.entity.ChestBlockEntity(
              base.up(), placedStockChest.getCachedState());
      visualClientChest.read(visualOnly, world.getRegistryManager());
      if (TrainerChests.profile(visualClientChest) != id || visualOnly.contains("Items"))
        throw new AssertionError(
            "Chest role must sync through native read without copying stock inventory");

      var restoredChest =
          net.minecraft.block.entity.BlockEntity.createFromNbt(
              base.up(), placedStockChest.getCachedState(), chestNbt, world.getRegistryManager());
      if (!(restoredChest instanceof net.minecraft.block.entity.ChestBlockEntity restored)
          || TrainerChests.profile(restored) != id)
        throw new AssertionError("Chest role did not survive NBT world save");
      var chestHit =
          new net.minecraft.util.hit.BlockHitResult(
              net.minecraft.util.math.Vec3d.ofCenter(base.up()),
              net.minecraft.util.math.Direction.UP,
              base.up(),
              false);
      if (id > 0) {
        if (!TrainerChests.open(owner, world, net.minecraft.util.Hand.MAIN_HAND, chestHit)
                .isAccepted()
            || !(owner.currentScreenHandler instanceof KitEditor))
          throw new AssertionError(
              "Physical profile placedStockChest did not open profileKit editor");
        owner.closeHandledScreen();
      } else {
        placedStockChest.setStack(
            0, new net.minecraft.item.ItemStack(net.minecraft.item.Items.TOTEM_OF_UNDYING));
        placedStockChest.setStack(
            1, new net.minecraft.item.ItemStack(net.minecraft.item.Items.BLACK_WOOL, 64));
        owner.setSneaking(false);
        if (!TrainerChests.open(owner, world, net.minecraft.util.Hand.MAIN_HAND, chestHit)
                .isAccepted()
            || !(owner.currentScreenHandler instanceof StockChestMenu))
          throw new AssertionError("Stock placedStockChest did not open protected infinite menu");
        var stock = owner.currentScreenHandler;
        stock.onSlotClick(0, 0, net.minecraft.screen.slot.SlotActionType.PICKUP, owner);
        if (!stock.getCursorStack().isOf(net.minecraft.item.Items.TOTEM_OF_UNDYING)
            || placedStockChest.getStack(0).getCount() != 1)
          throw new AssertionError("Supply pickup consumed template");
        stock.setCursorStack(net.minecraft.item.ItemStack.EMPTY);
        stock.onSlotClick(1, 1, net.minecraft.screen.slot.SlotActionType.PICKUP, owner);
        if (stock.getCursorStack().getCount() != 1 || placedStockChest.getStack(1).getCount() != 64)
          throw new AssertionError("Supply right-click should copy only one");
        stock.setCursorStack(net.minecraft.item.ItemStack.EMPTY);
        owner.getInventory().clear();
        stock.quickMove(owner, 1);
        if (owner.getInventory().count(net.minecraft.item.Items.BLACK_WOOL) != 64
            || placedStockChest.getStack(1).getCount() != 64)
          throw new AssertionError("Supply shift-click lost stock or failed copy");
        owner.closeHandledScreen();
      }
    }
    System.out.println(
        "PASS PROFILES/CHESTS: four isolated saved kits, command-block selection, RGB item/profile"
            + " names, explicit editor profile, actual vanilla chest placement+NBT and infinite"
            + " stock pickup/right-click/shift-click");

    // New tactics exercise real native placement/mining, not direct position writes.
    owner.closeHandledScreen();
    world.setBlockState(new BlockPos(-2, 63, 0), Blocks.STONE.getDefaultState(), 3);
    world.setBlockState(new BlockPos(0, 63, 0), Blocks.STONE.getDefaultState(), 3);
    owner.teleport(world, 0.5, 64, .5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    var tacticBot = new TrainingBot(server, world);
    server
        .getPlayerManager()
        .onPlayerConnect(
            new TrainingBot.LocalConnection(),
            tacticBot,
            net.minecraft.server.network.ConnectedClientData.createDefault(
                tacticBot.getGameProfile(), false));
    tacticBot.teleport(world, -1.5, 64, .5, Set.of(), -90, 0, false);
    tacticBot.onTeleportationDone();
    tacticBot.setOnGround(true);
    owner.setOnGround(true);
    var tacticOptions = new Options();
    tacticOptions.x = 0;
    tacticOptions.y = 63;
    tacticOptions.z = 0;
    tacticOptions.footWeb = true;
    tacticOptions.noRetreatRetotem = true;
    tacticOptions.retotem = false;
    tacticBot.getInventory().clear();
    tacticBot
        .getInventory()
        .setStack(0, new net.minecraft.item.ItemStack(net.minecraft.item.Items.GOLDEN_SWORD));
    tacticBot
        .getInventory()
        .setStack(1, new net.minecraft.item.ItemStack(net.minecraft.item.Items.COBWEB, 16));
    var tactics = new Session(owner, tacticBot, tacticOptions);
    if (tactics.mayRecover(false, 4)
        || tactics.mayRecover(true, 4)
        || !tactics.mayRecover(true, 16))
      throw new AssertionError(
          "No-retreat mode must allow gap only when opponent retreats and eats");
    var footFight = Session.class.getDeclaredMethod("footWebFight", int.class, double.class);
    footFight.setAccessible(true);
    BlockPos ownFeet = tacticBot.getBlockPos();
    world.setBlockState(ownFeet, Blocks.AIR.getDefaultState(), 3);
    if (!(boolean) footFight.invoke(tactics, 100, 4.0)
        || !world.getBlockState(ownFeet).isOf(Blocks.COBWEB)
        || tacticBot.getInventory().getStack(1).getCount() != 15
        || tacticBot.isGliding()
        || tacticBot.forwardSpeed != 0)
      throw new AssertionError(
          "Foot tactic must place real web, spend item, stop flight and hold ground");
    footFight.invoke(tactics, 121, 4.0);
    if (!world.getBlockState(owner.getBlockPos()).isOf(Blocks.COBWEB)
        || tacticBot.getInventory().getStack(1).getCount() != 14)
      throw new AssertionError(
          "Foot tactic must place opponent foot web with real placement and stock");
    var planted = Session.class.getDeclaredField("plantedFootWeb");
    planted.setAccessible(true);
    if (!ownFeet.equals(planted.get(tactics))) throw new AssertionError("Foot camp not tracked");
    owner.teleport(world, 6.5, 64, .5, Set.of(), 0, 0, false);
    owner.onTeleportationDone();
    footFight.invoke(tactics, 150, 64.0);
    if (!world.getBlockState(ownFeet).isOf(Blocks.COBWEB))
      throw new AssertionError(
          "Leaving foot camp must mine with native progress, never instant delete");
    var leaving = Session.class.getDeclaredField("leavingFootWeb");
    leaving.setAccessible(true);
    if (!leaving.getBoolean(tactics))
      throw new AssertionError("Retreating opponent must trigger leaving the web");
    world.setBlockState(ownFeet, Blocks.AIR.getDefaultState(), 3);
    if ((boolean) footFight.invoke(tactics, 151, 64.0) || planted.get(tactics) != null)
      throw new AssertionError("Removed foot web must release bot back to normal combat");
    server.getPlayerManager().remove(tacticBot);
    System.out.println(
        "PASS NEW TACTICS: no-retreat recovery gate, actual self-web placement consumes stock, no"
            + " flight/spin, opponent retreat starts native mining and releases camp");

    server.getPlayerManager().remove(owner);
    server.shutdown();
    System.exit(0);
  }
}
