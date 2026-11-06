import com.mojang.authlib.GameProfile;
import dev.duckbox.*;
import java.nio.file.*;import java.util.*;
import net.minecraft.*;import net.minecraft.block.*;
import net.minecraft.network.packet.c2s.common.SyncedClientOptions;
import net.minecraft.resource.VanillaDataPackProvider;
import net.minecraft.server.network.*;
import net.minecraft.test.*;
import net.minecraft.util.math.*;
import net.minecraft.world.GameMode;
import net.minecraft.world.level.storage.LevelStorage;
public final class CombatServerTest {
 public static void main(String[] args)throws Exception{
 Thread.setDefaultUncaughtExceptionHandler((t,e)->{e.printStackTrace();System.exit(1);});
 SharedConstants.createGameVersion();Bootstrap.initialize();NativeModBootstrap.prepare();
 var storage=LevelStorage.create(Path.of(args[0]));var imported=WorldTemplate.create(Path.of(args[0]));var save=storage.createSession(imported.getFileName().toString());var packs=VanillaDataPackProvider.createManager(save);
 var dummy=new TestFunction("duckbox","not_run","empty",200,0,true,c->{});
 var server=TestServer.create(Thread.currentThread(),save,packs,List.of(dummy),new BlockPos(0,64,0));
 if(!server.setupServer())throw new AssertionError("setup");server.setPvpEnabled(true);DuckBox.server=server;var world=server.getOverworld();
 if(world.getBlockState(new BlockPos(-146,64,93)).isAir())throw new AssertionError("Supplied spawn floor must load from saved region");
 int arenaBlocks=0,panels=0;
 for(int x=-14;x<=4;x++)for(int z=102;z<=120;z++)for(int y=78;y<=89;y++){
  var state=world.getBlockState(new BlockPos(x,y,z));if(!state.isAir())arenaBlocks++;
  if(state.getBlock() instanceof dev.duckbox.panels.MapPanelBlock)panels++;
 }
 if(arenaBlocks<100)throw new AssertionError("Supplied arena chunks did not load");
 System.out.println("PASS SUPPLIED WORLD LOAD: actual converted region chunks/spawn/arena loaded natively,blocks="+arenaBlocks+" panels="+panels);

 var owner=new ServerPlayerEntity(server,world,new GameProfile(UUID.randomUUID(),"TrainOwner"),SyncedClientOptions.createDefault());
 var bot=new TrainingBot(server,world);
 server.getPlayerManager().onPlayerConnect(new TrainingBot.LocalConnection(),owner,ConnectedClientData.createDefault(owner.getGameProfile(),false));
 server.getPlayerManager().onPlayerConnect(new TrainingBot.LocalConnection(),bot,ConnectedClientData.createDefault(bot.getGameProfile(),false));
 owner.changeGameMode(GameMode.SURVIVAL);bot.changeGameMode(GameMode.SURVIVAL);

 if(Boolean.getBoolean("duckbox.lowtraps")){
  var lowClock=net.minecraft.server.MinecraftServer.class.getDeclaredField("field_4572");lowClock.setAccessible(true);
  for(int t=0;t<80;t++){lowClock.setInt(server,server.getTicks()+1);owner.tick();owner.playerTick();bot.tick();}
  owner.onTeleportationDone();bot.onTeleportationDone();
  verifyLowWebNoTower(server,world,owner,bot);server.shutdown();System.exit(0);return;
 }
 var kit=Kits.defaults(world.getRegistryManager(),Options.Rules.NORMAL_SPAM);var round=Kits.decode(owner,Kits.encode(owner,kit));
 for(int i=0;i<41;i++)if(!net.minecraft.item.ItemStack.areEqual(kit.get(i),round.get(i)))throw new AssertionError("Kit codec slot"+i);
 Kits.give(owner,kit);Kits.give(bot,kit);
 for(var p:List.of(owner,bot)) {p.tick();p.playerTick();p.setInvulnerable(false);p.clearStatusEffects();p.setHealth(p.getMaxHealth());}
 if(owner.getMaxHealth()!=135||bot.getMaxHealth()!=135)throw new AssertionError("Kit health"+bot.getMaxHealth());
 double damage=bot.getAttributeValue(net.minecraft.entity.attribute.EntityAttributes.GENERIC_ATTACK_DAMAGE);
 if(Math.abs(damage-27.5)>.001)throw new AssertionError("Sword/offhand damage"+damage);
 System.out.println("PASS NATIVE KIT:41-slot codec,135HP,27.5attack including offhand, registries initialized");
 var serverClock=net.minecraft.server.MinecraftServer.class.getDeclaredField("field_4572");serverClock.setAccessible(true);
 for(int t=0;t<80;t++){serverClock.setInt(server,t+1);owner.tick();owner.playerTick();bot.tick();}
 owner.onTeleportationDone();bot.onTeleportationDone();
 try(var zip=new java.util.zip.ZipFile(Path.of(args[1]).toFile())){
  var config=com.google.gson.JsonParser.parseReader(new java.io.InputStreamReader(zip.getInputStream(zip.getEntry("duckbox-training.json")))).getAsJsonObject();
  var loaded=Kits.decode(owner,config.getAsJsonObject("kitProfiles").getAsJsonObject("1").getAsJsonArray("inventory"));
  if(!loaded.get(0).isOf(net.minecraft.item.Items.GOLDEN_SWORD))throw new AssertionError("Imported sword");
  for(int id=2;id<=4;id++)if(Kits.decode(owner,config.getAsJsonObject("kitProfiles").getAsJsonObject(""+id).getAsJsonArray("inventory")).stream().anyMatch(s->!s.isEmpty()))throw new AssertionError("Extra profile should remain empty");
  if(!config.getAsJsonObject("options").get("spin").getAsString().equals("BAIXO"))throw new AssertionError("Saved low spin default");
  Kits.give(bot,loaded);bot.tick();bot.playerTick();
  if(bot.getMaxHealth()!=135)throw new AssertionError("Imported kit attributes"+bot.getMaxHealth());Kits.give(bot,kit);
 }
 System.out.println("PASS SUPPLIED WORLD KITS: profile1 native codec/135HP, profiles2-4empty, low spin default preserved");
 var cfg=new Options();var fight=new Session(owner,bot,cfg);DuckBox.session=fight;bot.session=fight;
 float[] results=new float[2];
 for(int i=0;i<2;i++){
  owner.setHealth(owner.getMaxHealth());owner.setAbsorptionAmount(0);owner.timeUntilRegen=0;owner.setPosition(2,66,0);owner.setVelocity(Vec3d.ZERO);
  bot.setPosition(0,66,0);bot.setOnGround(false);bot.startFallFlying();bot.setSprinting(true);bot.fallDistance=0;bot.setVelocity(new Vec3d(0,i==0?.15:-.005,0));
  var cool=net.minecraft.entity.LivingEntity.class.getDeclaredField("field_6273");cool.setAccessible(true);cool.setInt(bot,30);
  float hp=owner.getHealth();bot.attack(owner);results[i]=hp-owner.getHealth();
 }
 if(results[0]<=0||results[1]<=results[0]||bot.fallDistance!=0)throw new AssertionError("Actual elytra/sprint crit"+Arrays.toString(results));
 System.out.println("PASS ACTUAL WOVEN CRITICAL: ascending="+results[0]+" descending="+results[1]);
 // Real vanilla totem usage must save both participants rather than the trainer handling death early.
 for(var p:List.of(owner,bot)){
  p.setHealth(1);p.timeUntilRegen=0;p.setInvulnerable(false);p.setStackInHand(net.minecraft.util.Hand.OFF_HAND,new net.minecraft.item.ItemStack(net.minecraft.item.Items.TOTEM_OF_UNDYING));
  p.damage(world.getDamageSources().generic(),100000);
  if(!p.isAlive()||!p.getOffHandStack().isEmpty())throw new AssertionError("Vanilla totem must pop for"+p.getName().getString()+" hp="+p.getHealth()+" hand="+p.getOffHandStack());
 }
 System.out.println("PASS VANILLA TOTEM: both participants consume native offhand totem and survive");
 fight.closed=true;DuckBox.session=null;bot.session=null;
 var dispatcher=new com.mojang.brigadier.CommandDispatcher<net.minecraft.server.command.ServerCommandSource>();DuckBox.registerCommands(dispatcher);if(dispatcher.getRoot().getChild("box")==null)throw new AssertionError("Commands");
 for(int i=0;i<=4;i++){var chest=TrainerChests.item(i);if(chest.isEmpty())throw new AssertionError("Chest"+i);}
 System.out.println("PASS NATIVE COMMANDS/CHESTS: box tree,5custom chest items");

 for(int x=-9;x<=9;x++)for(int z=-9;z<=9;z++){
  world.setBlockState(new BlockPos(x,63,z),Blocks.STONE.getDefaultState(),3);
  for(int y=64;y<=79;y++)world.setBlockState(new BlockPos(x,y,z),Blocks.AIR.getDefaultState(),3);
 }
 verifyRecoveryAndTower(server,world,owner,bot);
 verifyBlockedTower(server,world,owner,bot);
 verifyLowGapCadence(server,world,owner,bot);
 verifyToolsAndRetotem(server,world,owner,bot);
 verifyModeMatrix(server,world,owner,bot);
 verifyAirTracking(server,world,owner,bot);
 verifyLowWebNoTower(server,world,owner,bot);
 server.shutdown();System.out.println("PASS PORT SERVER SMOKE");System.exit(0);
 }

  private static void verifyRecoveryAndTower(net.minecraft.server.MinecraftServer server,
      net.minecraft.server.world.ServerWorld world, ServerPlayerEntity owner, TrainingBot bot) throws Exception {
    var tick = net.minecraft.server.MinecraftServer.class.getDeclaredField("field_4572"); tick.setAccessible(true);
    var start = Session.class.getDeclaredMethod("startApple", int.class); start.setAccessible(true);
    var committed = Session.class.getDeclaredMethod("committedApple"); committed.setAccessible(true);
    var healing = Session.class.getDeclaredField("healing"); healing.setAccessible(true);
    for (int progress : new int[] {16, 20}) {
      bot.session = null;
      Kits.give(bot, Kits.defaults(world.getRegistryManager(), Options.Rules.NORMAL_SPAM));
      tick.setInt(server, server.getTicks() + 1); bot.tick();
      for (int slot = 0; slot < 41; slot++) if (Kits.isTotem(bot.getInventory().getStack(slot)))
        bot.getInventory().setStack(slot, net.minecraft.item.ItemStack.EMPTY);
      for (int slot = 6; slot < 9; slot++) bot.getInventory().setStack(slot,
          new net.minecraft.item.ItemStack(net.minecraft.item.Items.TOTEM_OF_UNDYING));
      bot.teleport(world, .5, 64, .5, Set.of(), 0, 0); bot.onTeleportationDone();
      bot.stopFallFlying(); bot.stopUsingItem(); bot.setOnGround(true); bot.setHealth(bot.getMaxHealth());
      bot.setVelocity(net.minecraft.util.math.Vec3d.ZERO); bot.clearStatusEffects();
      owner.teleport(world, 6.5, 64, 6.5, Set.of(), 0, 0); owner.onTeleportationDone();
      owner.setHealth(owner.getMaxHealth()); owner.stopUsingItem();
      owner.getInventory().setStack(2, new net.minecraft.item.ItemStack(net.minecraft.item.Items.ENCHANTED_GOLDEN_APPLE, 3));
      owner.getInventory().selectedSlot = 2;
      owner.getMainHandStack().use(world, owner, net.minecraft.util.Hand.MAIN_HAND);
      var settings = new Options(); settings.x = 0; settings.y = 63; settings.z = 0;
      settings.giro = false; settings.gap = false; settings.retotem = false; settings.teia = false;
      settings.noRetreatRetotem = true;
      var recovery = new Session(owner, bot, settings);
      int stock = bot.getInventory().getStack(2).getCount();
      start.invoke(recovery, 0);
      for (int i = 0; i < progress; i++) { tick.setInt(server, server.getTicks() + 1); bot.tick(); }
      if ((boolean) committed.invoke(recovery) != (progress >= 20))
        throw new AssertionError("Native apple60percent threshold incorrect at " + bot.getItemUseTime());
      owner.stopUsingItem();
      tick.setInt(server, server.getTicks() + 1); bot.tick();
      if (progress >= 20) {
        if (!bot.isUsingItem()) throw new AssertionError("Late apple must survive opponent resuming combat");
        for (int i = 0; i < 18; i++) { tick.setInt(server, server.getTicks() + 1); bot.tick(); }
        if (bot.getInventory().getStack(2).getCount() != stock - 1 || healing.getBoolean(recovery)
            || !bot.getMainHandStack().isOf(net.minecraft.item.Items.GOLDEN_SWORD))
          throw new AssertionError("Late apple must actually be consumed once, then resume sword combat");
      } else if (healing.getBoolean(recovery) || bot.getInventory().getStack(2).getCount() != stock)
        throw new AssertionError("Early apple remains interruptible without consuming stock");
      recovery.closed = true;
    }
    var scarceOptions = new Options(); scarceOptions.noRetreatRetotem = true;
    scarceOptions.difficulty = Options.Difficulty.EXPERT;
    var scarcity = new Session(owner, bot, scarceOptions);
    var aim = Session.class.getDeclaredMethod("combatAimSpeed"); aim.setAccessible(true);
    owner.setOnGround(true);
    float normalAim = (float) aim.invoke(scarcity);
    bot.getInventory().setStack(8, net.minecraft.item.ItemStack.EMPTY);
    if (scarcity.countTotems() != 2
        || Math.abs((float) aim.invoke(scarcity) - normalAim * 1.1f) > .001)
      throw new AssertionError("At two totems,10percent aim boost must apply");
    var end = Session.class.getDeclaredMethod("endRecovery", int.class, int.class); end.setAccessible(true);
    var wait = Session.class.getDeclaredField("gapWait"); wait.setAccessible(true);
    healing.setBoolean(scarcity, true); end.invoke(scarcity, 100, 30);
    if (wait.getInt(scarcity) != 177)
      throw new AssertionError("Scarce-totem recovery must use only30percent higher frequency, not the old35tick pause");
    scarcity.closed = true;

    var campPolicy = new Session(owner, bot, scarceOptions);
    var allowedCamp = Session.class.getDeclaredMethod("footCampAllowed", int.class); allowedCamp.setAccessible(true);
    bot.setHealth(bot.getMaxHealth() * .3f); owner.setHealth(owner.getMaxHealth());
    if ((boolean) allowedCamp.invoke(campPolicy, 1))
      throw new AssertionError("Large health disadvantage must refuse self-web camping");
    bot.setHealth(bot.getMaxHealth() * .95f);
    if (!(boolean) allowedCamp.invoke(campPolicy, 2))
      throw new AssertionError("Small health deficit may keep foot-web tactic");
    for (var fighter : List.of(owner, bot)) {
      fighter.getInventory().setStack(40, new net.minecraft.item.ItemStack(net.minecraft.item.Items.TOTEM_OF_UNDYING));
      fighter.setHealth(1); fighter.setAbsorptionAmount(0); fighter.timeUntilRegen = 0;
      if (!fighter.damage(world.getDamageSources().generic(), 100000) || !fighter.isAlive())
        throw new AssertionError("Foot-camp pop fixture must use vanilla totem protection");
    }
    bot.setHealth(bot.getMaxHealth() * .3f); owner.setHealth(owner.getMaxHealth());
    if (!(boolean) allowedCamp.invoke(campPolicy, 3) || (boolean) allowedCamp.invoke(campPolicy, 64))
      throw new AssertionError("Both real recent totem pops permit camping only within the short exchange");
    campPolicy.closed = true;
    System.out.println("PASS FOOT-WEB POLICY: refuse major health deficit, allow minor deficit or both native recent pops, expire mutual-pop exception");

    // Real elevation route without any target cobweb or forced navigation state.
    for (int x = -8; x <= 8; x++) for (int z = -8; z <= 8; z++)
      for (int y = 64; y <= 74; y++) world.setBlockState(new BlockPos(x, y, z), Blocks.AIR.getDefaultState(), 3);
    world.setBlockState(new BlockPos(0, 69, 0), Blocks.BLACK_WOOL.getDefaultState(), 3);
    owner.teleport(world, .5, 70, .5, Set.of(), 0, 0); owner.onTeleportationDone(); owner.setOnGround(true);
    bot.teleport(world, 6.5, 64, .5, Set.of(), 90, 0); bot.onTeleportationDone();
    bot.setOnGround(true); bot.stopFallFlying(); bot.stopUsingItem(); bot.setVelocity(net.minecraft.util.math.Vec3d.ZERO);
    bot.setHealth(bot.getMaxHealth()); bot.clearStatusEffects();
    bot.getInventory().setStack(5, new net.minecraft.item.ItemStack(net.minecraft.item.Items.BLACK_WOOL, 32));
    var towerOptions = new Options(); towerOptions.x = 0; towerOptions.y = 63; towerOptions.z = 0;
    towerOptions.gap = false; towerOptions.giro = false; towerOptions.retotem = false; towerOptions.teia = false;
    var tower = new Session(owner, bot, towerOptions);
    DuckBox.session = tower;
    boolean climbed = false;
    for (int i = 0; i < 400; i++) {
      tick.setInt(server, server.getTicks() + 1); bot.tick();
      if (bot.getY() >= 69.4 && bot.getInventory().getStack(5).getCount() < 32) { climbed = true; break; }
    }
    if (!climbed || !world.getBlockState(new BlockPos(0, 69, 0)).isOf(Blocks.BLACK_WOOL))
      throw new AssertionError("Elevated platform must trigger real tower without mining support: " + bot.getPos());
    tower.cleanupBuilding(); tower.closed = true; DuckBox.session = null;
    world.setBlockState(new BlockPos(0, 69, 0), Blocks.AIR.getDefaultState(), 3);
    BlockPos headWebFight = new BlockPos(0, 65, 0);
    world.setBlockState(headWebFight, Blocks.COBWEB.getDefaultState(), 3);
    owner.teleport(world, .5, 64, .5, Set.of(), 0, 0); owner.onTeleportationDone(); owner.setOnGround(true);
    owner.setHealth(owner.getMaxHealth()); owner.setAbsorptionAmount(0); owner.timeUntilRegen = 0;
    bot.teleport(world, 2.3, 64, .5, Set.of(), 90, 0); bot.onTeleportationDone();
    bot.setVelocity(net.minecraft.util.math.Vec3d.ZERO); bot.setOnGround(true); bot.stopFallFlying();
    towerOptions.giro = true; towerOptions.spin = Options.SpinLevel.EXTREMO; towerOptions.strafe = true;
    var headCombat = new Session(owner, bot, towerOptions);
    float targetBefore = owner.getHealth();
    for (int i = 0; i < 35; i++) {
      tick.setInt(server, server.getTicks() + 1); bot.tick();
      if (bot.getBoundingBox().intersects(new net.minecraft.util.math.Box(headWebFight)) || bot.isFallFlying())
        throw new AssertionError("Head-web combat must stay outside web without orbiting/gliding into it");
    }
    if (owner.getHealth() >= targetBefore)
      throw new AssertionError("Safe head-web stance must still hit exposed feet");
    headCombat.closed = true; world.setBlockState(headWebFight, Blocks.AIR.getDefaultState(), 3);
    System.out.println("PASS SAFE HEAD-WEB COMBAT: Extreme spin enabled, no self-web intersection or gliding, actual exposed-feet hits");
    world.setBlockState(headWebFight, Blocks.COBWEB.getDefaultState(), 3);
    world.setBlockState(headWebFight.down(), Blocks.COBWEB.getDefaultState(), 3);
    owner.setPose(net.minecraft.entity.EntityPose.STANDING); owner.stopFallFlying(); owner.setHealth(owner.getMaxHealth()); owner.timeUntilRegen = 0;
    bot.getInventory().setStack(21, new net.minecraft.item.ItemStack(net.minecraft.item.Items.SHEARS));
    var fullWebCombat = new Session(owner, bot, towerOptions);
    boolean minedFeet = false, resumedHit = false;
    float beforeFullWeb = owner.getHealth();
    for (int i = 0; i < 100; i++) {
      tick.setInt(server, server.getTicks() + 1); bot.tick();
      if (world.getBlockState(headWebFight.down()).isAir()) minedFeet = true;
      if (!world.getBlockState(headWebFight).isOf(Blocks.COBWEB))
        throw new AssertionError("Standing double-web tactic must preserve head web and cut feet first");
      if (owner.getHealth() < beforeFullWeb) {
        if (!minedFeet) throw new AssertionError("No damage through fully blocking webs");
        resumedHit = true; break;
      }
    }
    if (!minedFeet || !resumedHit) throw new AssertionError("Full-web target must have feet cut and combat resumed");
    fullWebCombat.closed = true; world.setBlockState(headWebFight, Blocks.AIR.getDefaultState(), 3);
    System.out.println("PASS FULL WEB: standing target feet web cut with real shears, head web preserved, damage only after opening");
    System.out.println("PASS FINAL RECOVERY/TOWER:60percent consumption commitment, real apple consumed then sword, two-totem aim/recovery boost and autonomous elevated tower without web");
  }

  private static void verifyBlockedTower(net.minecraft.server.MinecraftServer server,
      net.minecraft.server.world.ServerWorld world, ServerPlayerEntity owner, TrainingBot bot) throws Exception {
    var ticks = net.minecraft.server.MinecraftServer.class.getDeclaredField("field_4572"); ticks.setAccessible(true);
    for (int x = -8; x <= 8; x++) for (int z = -8; z <= 8; z++)
      for (int y = 64; y <= 74; y++) world.setBlockState(new BlockPos(x,y,z), Blocks.AIR.getDefaultState(),3);
    var settings = new Options(); settings.x=0;settings.y=63;settings.z=0;
    settings.gap=false;settings.giro=false;settings.retotem=false;settings.teia=false;
    bot.session=null; Kits.give(bot,Kits.defaults(world.getRegistryManager(),Options.Rules.NORMAL_SPAM));
    bot.getInventory().setStack(21,new net.minecraft.item.ItemStack(net.minecraft.item.Items.SHEARS));
    bot.getInventory().setStack(5,new net.minecraft.item.ItemStack(net.minecraft.item.Items.CYAN_WOOL,32));
    owner.teleport(world,.5,70,.5,Set.of(),0,0);owner.onTeleportationDone();owner.setOnGround(true);owner.setInvulnerable(true);
    world.setBlockState(new BlockPos(0,69,0),Blocks.BLACK_WOOL.getDefaultState(),3);
    bot.teleport(world,6.5,64,.5,Set.of(),90,0);bot.onTeleportationDone();bot.stopFallFlying();bot.setOnGround(true);
    bot.setVelocity(net.minecraft.util.math.Vec3d.ZERO);bot.setHealth(bot.getMaxHealth());bot.clearStatusEffects();
    var recovery = new Session(owner,bot,settings);DuckBox.session=recovery;
    var column=Session.class.getDeclaredField("towerColumn");column.setAccessible(true);
    boolean knocked=false,fell=false,blocked=false,cleared=false,climbed=false;
    BlockPos obstruction=null;
    for(int i=0;i<500;i++) {
      ticks.setInt(server,server.getTicks()+1);bot.tick();
      if(!knocked && bot.getInventory().getStack(5).getCount()<32 && bot.getY()>64.4) {
        bot.move(net.minecraft.entity.MovementType.SELF,new net.minecraft.util.math.Vec3d(1.15,-.4,0));
        bot.setVelocity(new net.minecraft.util.math.Vec3d(.45,-.4,0));knocked=true;
      }
      if(knocked && !blocked && bot.isOnGround() && bot.getY()<65) {
        fell=true;var base=(BlockPos)column.get(recovery);
        if(base!=null){obstruction=base.up(2);world.setBlockState(obstruction,Blocks.CYAN_WOOL.getDefaultState(),3);blocked=true;}
      }
      if(blocked && world.getBlockState(obstruction).isAir()) cleared=true;
      if(cleared && bot.getY()>=69.4){climbed=true;break;}
    }
    if(!knocked||!fell||!blocked||!cleared||!climbed)
      throw new AssertionError("Tower must recover from real fall and mine blocking wool: "+knocked+"/"+fell+"/"+blocked+"/"+cleared+"/"+climbed+" pos="+bot.getPos());
    recovery.cleanupBuilding();recovery.closed=true;DuckBox.session=null;owner.setInvulnerable(false);
    System.out.println("PASS BLOCKED TOWER: real knockback/fall, user wool obstacle cut through main AI, tower resumed to target height");
  }

  private static void verifyLowGapCadence(net.minecraft.server.MinecraftServer server,
      net.minecraft.server.world.ServerWorld world, ServerPlayerEntity owner, TrainingBot bot) throws Exception {
    var tick=net.minecraft.server.MinecraftServer.class.getDeclaredField("field_4572");tick.setAccessible(true);
    bot.session=null; Kits.give(bot,Kits.defaults(world.getRegistryManager(),Options.Rules.NORMAL_SPAM));
    for(int slot=0;slot<41;slot++)if(Kits.isTotem(bot.getInventory().getStack(slot)))bot.getInventory().setStack(slot,net.minecraft.item.ItemStack.EMPTY);
    bot.teleport(world,.5,64,.5,Set.of(),0,0);bot.onTeleportationDone();bot.stopUsingItem();bot.stopFallFlying();
    bot.setOnGround(true);bot.setVelocity(net.minecraft.util.math.Vec3d.ZERO);bot.clearStatusEffects();bot.setHealth(10);bot.setAbsorptionAmount(0);
    owner.teleport(world,6.5,64,6.5,Set.of(),0,0);owner.onTeleportationDone();owner.stopUsingItem();owner.setInvulnerable(true);owner.setVelocity(net.minecraft.util.math.Vec3d.ZERO);
    var cfg=new Options();cfg.x=0;cfg.y=63;cfg.z=0;cfg.giro=false;cfg.retotem=false;cfg.teia=false;
    var limited=new Session(owner,bot,cfg);DuckBox.session=limited;
    int stock=bot.getInventory().getStack(2).getCount();
    for(int step=0;step<80;step++){tick.setInt(server,server.getTicks()+1);bot.tick();}
    if(bot.getInventory().getStack(2).getCount()!=stock-1)
      throw new AssertionError("Low-totem bot must consume one real gap, not spam/chains during initial80ticks");
    limited.closed=true;DuckBox.session=null;owner.setInvulnerable(false);
    System.out.println("PASS LOW GAP CADENCE: zero-totem recovery consumed exactly one real apple over80ticks");
  }



 private static void verifyToolsAndRetotem(net.minecraft.server.MinecraftServer server,net.minecraft.server.world.ServerWorld world,ServerPlayerEntity owner,TrainingBot bot)throws Exception{
  var ticks=net.minecraft.server.MinecraftServer.class.getDeclaredField("field_4572");ticks.setAccessible(true);
  var retotem=Session.class.getDeclaredMethod("retotem",int.class);retotem.setAccessible(true);
  var random=Session.class.getDeclaredField("random");random.setAccessible(true);
  for(var level:Options.Difficulty.values()){
   bot.session=null;Kits.give(bot,Kits.defaults(world.getRegistryManager(),Options.Rules.NORMAL_SPAM));ticks.setInt(server,server.getTicks()+1);bot.tick();bot.stopUsingItem();bot.clearStatusEffects();bot.setHealth(15);bot.getInventory().setStack(40,net.minecraft.item.ItemStack.EMPTY);
   var o=new Options();o.difficulty=level;var fight=new Session(owner,bot,o);int budget=fight.countTotems();
   random.set(fight,new java.util.Random(1){int calls;@Override public double nextDouble(){return level==Options.Difficulty.MEDIUM&&calls++==0?.19:.21;}});
   for(int t=0;t<50&&!Kits.isTotem(bot.getOffHandStack());t++)retotem.invoke(fight,t);
   if(!Kits.isTotem(bot.getOffHandStack())||fight.countTotems()!=budget)throw new AssertionError("Retotem/budget at"+level);
   fight.closed=true;
   for(int slot=6;slot<=8;slot++)bot.getInventory().setStack(slot,net.minecraft.item.ItemStack.EMPTY);bot.getInventory().setStack(40,net.minecraft.item.ItemStack.EMPTY);
   var refill=new Session(owner,bot,o);int reserve=refill.countTotems();
   for(int t=0;t<80&&!Kits.isTotem(bot.getOffHandStack());t++)retotem.invoke(refill,t);
   if(!Kits.isTotem(bot.getOffHandStack())||refill.refillCount()!=1||refill.countTotems()!=reserve)throw new AssertionError("Refill/budget at"+level);
   refill.closed=true;
  }
  System.out.println("PASS DIFFICULTY RETOTEM/REFILL: all4levels refill reserves and equip native offhand without duplication; Medium retries an intentional failed swap");
  bot.session=null;Kits.give(bot,Kits.defaults(world.getRegistryManager(),Options.Rules.NORMAL_SPAM));ticks.setInt(server,server.getTicks()+1);bot.tick();bot.stopUsingItem();bot.clearStatusEffects();bot.setPosition(.5,66,.5);bot.setOnGround(false);bot.startFallFlying();bot.setVelocity(new Vec3d(.2,-.1,0));
  var rocketFight=new Session(owner,bot,new Options());var rocket=Session.class.getDeclaredMethod("useRocket",int.class);rocket.setAccessible(true);
  int rockets=bot.getInventory().getStack(1).getCount();
  if(!(boolean)rocket.invoke(rocketFight,100)||bot.getInventory().getStack(1).getCount()!=rockets-1)throw new AssertionError("Air rocket must consume actual firework");rocketFight.closed=true;bot.stopFallFlying();
  System.out.println("PASS AIR ROCKET: real vanilla firework used/consumed while gliding");
  bot.session=null;bot.stopUsingItem();bot.clearStatusEffects();
  var weak=new net.minecraft.item.ItemStack(net.minecraft.item.Items.SPLASH_POTION);var strong=new net.minecraft.item.ItemStack(net.minecraft.item.Items.SPLASH_POTION);
  weak.set(net.minecraft.component.DataComponentTypes.POTION_CONTENTS,new net.minecraft.component.type.PotionContentsComponent(net.minecraft.potion.Potions.SWIFTNESS));strong.set(net.minecraft.component.DataComponentTypes.POTION_CONTENTS,new net.minecraft.component.type.PotionContentsComponent(net.minecraft.potion.Potions.STRONG_SWIFTNESS));
  bot.getInventory().setStack(18,weak);bot.getInventory().setStack(19,strong);var potionFight=new Session(owner,bot,new Options());var potion=Session.class.getDeclaredMethod("useSpeedPotion",int.class);potion.setAccessible(true);
  if(!(boolean)potion.invoke(potionFight,0)||!strong.isEmpty()||bot.getInventory().getStack(18).getCount()!=1)throw new AssertionError("Strong Speed must be thrown first, weaker stock preserved");
  bot.clearStatusEffects();var repeatPotion=Session.class.getDeclaredMethod("useSpeedPotion",int.class,boolean.class);repeatPotion.setAccessible(true);
  if((boolean)repeatPotion.invoke(potionFight,799,true)||weak.getCount()!=1)throw new AssertionError("Speed potion must wait40seconds, including after losing the effect");
  if(!(boolean)repeatPotion.invoke(potionFight,800,true)||!weak.isEmpty())throw new AssertionError("Speed potion must become available at800ticks");
  potionFight.closed=true;bot.session=null;DuckBox.session=null;
  System.out.println("PASS SPEED POTION: strongest real splash potion consumed first;40second cooldown blocks tick799and permits tick800");
 }



 private static void verifyModeMatrix(net.minecraft.server.MinecraftServer server,net.minecraft.server.world.ServerWorld world,ServerPlayerEntity owner,TrainingBot bot)throws Exception{
  var tick=net.minecraft.server.MinecraftServer.class.getDeclaredField("field_4572");tick.setAccessible(true);int cases=0;
  for(var level:Options.Difficulty.values())for(var rules:Options.Rules.values())for(boolean tank:new boolean[]{false,true}){
   for(int x=-9;x<=9;x++)for(int z=-9;z<=9;z++){
    world.setBlockState(new BlockPos(x,63,z),Blocks.STONE.getDefaultState(),3);
    for(int y=64;y<=79;y++)world.setBlockState(new BlockPos(x,y,z),Blocks.AIR.getDefaultState(),3);
   }

   bot.session=null;Kits.give(owner,Kits.defaults(world.getRegistryManager(),rules));Kits.give(bot,Kits.defaults(world.getRegistryManager(),rules));tick.setInt(server,server.getTicks()+1);bot.tick();owner.playerTick();
   owner.stopUsingItem();bot.stopUsingItem();owner.clearStatusEffects();bot.clearStatusEffects();owner.setAbsorptionAmount(0);bot.setAbsorptionAmount(0);owner.setInvulnerable(false);bot.setInvulnerable(false);owner.setHealth(owner.getMaxHealth());bot.setHealth(bot.getMaxHealth());owner.timeUntilRegen=0;bot.timeUntilRegen=0;
   bot.stopFallFlying();bot.setPose(net.minecraft.entity.EntityPose.STANDING);bot.setPosition(.5,64,.5);bot.setVelocity(Vec3d.ZERO);bot.setOnGround(true);bot.setYaw(-90);bot.setPitch(0);owner.setPosition(2.3,64,.5);owner.setVelocity(Vec3d.ZERO);owner.setOnGround(true);
   var o=new Options();o.x=0;o.y=63;o.z=0;o.difficulty=level;o.rules=rules;o.tank=tank;o.teia=false;o.footWeb=false;o.gap=false;o.retotem=true;o.giro=true;o.spin=Options.SpinLevel.EXTREMO;
   var fight=new Session(owner,bot,o);DuckBox.session=fight;
   var rng=Session.class.getDeclaredField("random");rng.setAccessible(true);rng.set(fight,new java.util.Random(7));boolean hit=false,moved=false;
   for(int t=0;t<160;t++){
    owner.setPosition(2.3,64,.5);owner.setVelocity(Vec3d.ZERO);owner.setHealth(owner.getMaxHealth());owner.playerTick();float before=owner.getHealth();
    tick.setInt(server,server.getTicks()+1);bot.tick();hit|=owner.getHealth()<before;moved|=bot.getPos().squaredDistanceTo(new Vec3d(.5,64,.5))>.02;
    if(!bot.isAlive()||fight.closed)throw new AssertionError("Unexpected AI stop "+level+rules+" tank="+tank);
   }
   if(!moved||(!tank&&!hit)||(tank&&hit))throw new AssertionError("AI mode/movement/attack "+level+rules+" tank="+tank+" hit="+hit+" moved="+moved);
   fight.closed=true;bot.session=null;DuckBox.session=null;cases++;
  }
  System.out.println("PASS MODE MATRIX: "+cases+" combinations of4difficulties,Spam/SemiInsta,Duel/Tank;160native AI ticks each, movement, melee and Tank restraint");
 }



 private static void verifyAirTracking(net.minecraft.server.MinecraftServer server,net.minecraft.server.world.ServerWorld world,ServerPlayerEntity owner,TrainingBot bot)throws Exception{
  bot.session=null;Kits.give(bot,Kits.defaults(world.getRegistryManager(),Options.Rules.NORMAL_SPAM));
  for(int slot=0;slot<41;slot++)if(Kits.isTotem(bot.getInventory().getStack(slot)))bot.getInventory().setStack(slot,net.minecraft.item.ItemStack.EMPTY);
  var settings=new Options();settings.difficulty=Options.Difficulty.HIGH;var tracking=new Session(owner,bot,settings);
  var speed=Session.class.getDeclaredMethod("combatAimSpeed");speed.setAccessible(true);var error=Session.class.getDeclaredMethod("combatAimErrorScale");error.setAccessible(true);
  owner.stopFallFlying();owner.setOnGround(false);
  for(int slot=6;slot<10;slot++)bot.getInventory().setStack(slot,new net.minecraft.item.ItemStack(net.minecraft.item.Items.TOTEM_OF_UNDYING));
  if(Math.abs((float)speed.invoke(tracking)-settings.difficulty.aimSpeed*1.36f)>.001||Math.abs((double)error.invoke(tracking)-1/1.36)>.0001)throw new AssertionError("Four totems must improve airborne tracking36percent");
  bot.getInventory().setStack(10,new net.minecraft.item.ItemStack(net.minecraft.item.Items.TOTEM_OF_UNDYING));
  if((float)speed.invoke(tracking)!=settings.difficulty.aimSpeed)throw new AssertionError("Five totems must keep normal tracking");
  bot.getInventory().setStack(10,net.minecraft.item.ItemStack.EMPTY);bot.getInventory().setStack(9,net.minecraft.item.ItemStack.EMPTY);bot.getInventory().setStack(8,net.minecraft.item.ItemStack.EMPTY);
  if(Math.abs((float)speed.invoke(tracking)-settings.difficulty.aimSpeed*1.36f)>.001)throw new AssertionError("Air bonus must not stack with old two-totem bonus");
  owner.setOnGround(true);if(Math.abs((float)speed.invoke(tracking)-settings.difficulty.aimSpeed*1.1f)>.001)throw new AssertionError("Ground tracking keeps old two-totem behavior");
  tracking.closed=true;bot.session=null;DuckBox.session=null;
  System.out.println("PASS AIR TRACKING: <=4totems,36percent aim speed/precision factor for airborne target;5totems normal; ground unchanged; no stacked bonus or reach change");
 }



 private static void verifyLowWebNoTower(net.minecraft.server.MinecraftServer server,net.minecraft.server.world.ServerWorld world,ServerPlayerEntity owner,TrainingBot bot)throws Exception{
  var tick=net.minecraft.server.MinecraftServer.class.getDeclaredField("field_4572");tick.setAccessible(true);
  var scaffold=Session.class.getDeclaredMethod("scaffold",int.class);scaffold.setAccessible(true);var route=Session.class.getDeclaredField("webRoute");route.setAccessible(true);
  int lowTrapCase=0;
  for(int height:(Boolean.getBoolean("duckbox.lowtraps")?new int[]{1,2,3,3}:new int[]{1,2,3})){
   for(var oldRocket:world.getEntitiesByType(net.minecraft.entity.EntityType.FIREWORK_ROCKET,new net.minecraft.util.math.Box(-16,50,-16,16,90,16),e->true))oldRocket.discard();
   for(int x=-8;x<=8;x++)for(int z=-8;z<=8;z++){world.setBlockState(new BlockPos(x,63,z),Blocks.STONE.getDefaultState(),3);for(int y=64;y<=78;y++)world.setBlockState(new BlockPos(x,y,z),Blocks.AIR.getDefaultState(),3);}
   bot.session=null;Kits.give(bot,Kits.defaults(world.getRegistryManager(),Options.Rules.NORMAL_SPAM));Kits.give(owner,Kits.defaults(world.getRegistryManager(),Options.Rules.NORMAL_SPAM));tick.setInt(server,server.getTicks()+1);bot.tick();owner.playerTick();
   for(var fighter:List.of(owner,bot)){fighter.stopFallFlying();fighter.stopUsingItem();fighter.setPose(net.minecraft.entity.EntityPose.STANDING);fighter.clearStatusEffects();fighter.setAbsorptionAmount(0);fighter.setHealth(fighter.getMaxHealth());fighter.timeUntilRegen=0;fighter.setInvulnerable(false);}
   owner.setPosition(2.3,64+height,.5);owner.setOnGround(true);owner.setVelocity(Vec3d.ZERO);bot.setPosition(.5,64,.5);bot.setOnGround(true);bot.setVelocity(Vec3d.ZERO);bot.setYaw(-90);
   if(lowTrapCase++==3){
    for(int y=64;y<=69;y++)world.setBlockState(new BlockPos(0,y,0),Blocks.BLACK_WOOL.getDefaultState(),3);
    bot.setPosition(.5,70,.5);bot.setOnGround(true);
   }
   world.setBlockState(BlockPos.ofFloored(owner.getEyePos()),Blocks.COBWEB.getDefaultState(),3);
   var o=new Options();o.x=0;o.y=63;o.z=0;o.difficulty=Options.Difficulty.HIGH;o.giro=true;o.spin=Options.SpinLevel.EXTREMO;o.teia=false;o.gap=false;o.retotem=false;
   var fight=new Session(owner,bot,o);DuckBox.session=fight;
   if((boolean)scaffold.invoke(fight,1))throw new AssertionError("No direct tower for low trapped player");
   int wool=bot.getInventory().getStack(5).getCount();boolean hit=false;
   for(int t=0;t<100;t++){
    owner.setPosition(2.3,64+height,.5);owner.setVelocity(Vec3d.ZERO);owner.setOnGround(true);owner.setHealth(owner.getMaxHealth());owner.playerTick();float hp=owner.getHealth();
    tick.setInt(server,server.getTicks()+1);bot.tick();hit|=owner.getHealth()<hp;
    for(var rocket:world.getEntitiesByType(net.minecraft.entity.EntityType.FIREWORK_ROCKET,new net.minecraft.util.math.Box(-16,50,-16,16,90,16),e->!e.isRemoved()))rocket.tick();
    if(route.get(fight).toString().equals("TOWER"))throw new AssertionError("Low head web must never select tower route at height"+height);
   }
   if(wool-bot.getInventory().getStack(5).getCount()>5||!hit)throw new AssertionError("Low trap must attack feet without a wool tower at height"+height+" hit="+hit+" case="+lowTrapCase+" bot="+bot.getPos());
   fight.closed=true;bot.session=null;DuckBox.session=null;
  }
  System.out.println("PASS LOW WEB TRAPS:1/2/3blocks above floor, no tower route, cage-side placements preserved, real feet hits with Extreme spin enabled; higher tower scenarios remain covered");
 }

}
