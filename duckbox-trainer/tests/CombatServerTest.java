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
    boolean climbed = false;
    for (int n = 0; n < 240; n++) {
      ticks.setInt(server, 3000 + n);
      bot.tick();
      if (bot.getY() >= 67.4 && bot.getInventory().getStack(5).getCount() < 32) {
        climbed = true;
        break;
      }
    }
    if (!climbed)
      throw new AssertionError(
          "Full AI black-wool tower failed: bot="
              + bot.getPos()
              + " stock="
              + bot.getInventory().getStack(5));
    DuckBox.session.cleanupBuilding();
    world.setBlockState(new BlockPos(0, 69, 0), Blocks.AIR.getDefaultState(), 3);
    DuckBox.session.closed = true;
    DuckBox.session = new Session(owner, bot, options);
    System.out.println(
        "PASS FULL NATIVE NAVIGATION: AI climbed with black wool using real ticks/physics and"
            + " consumed stock");
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
    if ((boolean) ready.invoke(cooldownSession))
      throw new AssertionError("Normal must respect uncharged vanilla attack");
    for (int n = 0; n < 10; n++) {
      ticks.setInt(server, 10001 + n);
      bot.tick();
    }
    if (!(boolean) ready.invoke(cooldownSession))
      throw new AssertionError("Normal must accept full native cooldown");
    bot.equipStack(net.minecraft.entity.EquipmentSlot.CHEST, oldElytra);
    ticks.setInt(server, 10020);
    bot.tick();
    bot.resetLastAttackedTicks();
    ticks.setInt(server, 10021);
    bot.tick();
    for (int n = 0; n < 20; n++)
      if (!(boolean) ready.invoke(cooldownSession))
        throw new AssertionError(
            "Elytra attack speed must control Normal without artificial CPS gate");
    options.rules = Options.Rules.INSTA_KILL;
    var instaCadenceSession = new Session(owner, bot, options);
    instaCadenceSession.closed = true;
    int instaAttempts = 0;
    for (int n = 0; n < 20; n++) if ((boolean) ready.invoke(instaCadenceSession)) instaAttempts++;
    if (instaAttempts != 15)
      throw new AssertionError("Insta Kill cadence changed: " + instaAttempts);
    options.rules = Options.Rules.NORMAL_SPAM;
    System.out.println(
        "PASS COMBAT RULES: Normal waits only for native cooldown/elytra attack speed; Insta Kill"
            + " retains15/20 attempts");
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
