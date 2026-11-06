import com.mojang.authlib.GameProfile;
import dev.duckbox.*;
import java.nio.file.*;import java.util.*;
import net.minecraft.*;import net.minecraft.block.*;

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
 var server=TestServer.create(Thread.currentThread(),save,packs,List.of(new GameTestBatch("duckbox",List.of(dummy),w->{},w->{})),new BlockPos(0,64,0));
 if(!server.setupServer())throw new AssertionError("setup");server.setPvpEnabled(true);DuckBox.server=server;var world=server.getOverworld();
 if(world.getBlockState(new BlockPos(-146,64,93)).isAir())throw new AssertionError("Supplied spawn floor must load from saved region");
 int arenaBlocks=0,panels=0;
 for(int x=-14;x<=4;x++)for(int z=102;z<=120;z++)for(int y=78;y<=89;y++){
  var state=world.getBlockState(new BlockPos(x,y,z));if(!state.isAir())arenaBlocks++;
  if(state.getBlock() instanceof dev.duckbox.panels.MapPanelBlock)panels++;
 }
 if(arenaBlocks<100)throw new AssertionError("Supplied arena chunks did not load");
 System.out.println("PASS SUPPLIED WORLD LOAD: actual converted region chunks/spawn/arena loaded natively,blocks="+arenaBlocks+" panels="+panels);

 var owner=new ServerPlayerEntity(server,world,new GameProfile(UUID.randomUUID(),"TrainOwner"));
 var bot=new TrainingBot(server,world);
 server.getPlayerManager().onPlayerConnect(new TrainingBot.LocalConnection(),owner);
 server.getPlayerManager().onPlayerConnect(new TrainingBot.LocalConnection(),bot);
 owner.changeGameMode(GameMode.SURVIVAL);bot.changeGameMode(GameMode.SURVIVAL);
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
  if(!p.isAlive()||!p.getOffHandStack().isEmpty())throw new AssertionError("Vanilla totem must pop");
 }
 System.out.println("PASS VANILLA TOTEM: both participants consume native offhand totem and survive");
 fight.closed=true;DuckBox.session=null;bot.session=null;
 var dispatcher=new com.mojang.brigadier.CommandDispatcher<net.minecraft.server.command.ServerCommandSource>();DuckBox.registerCommands(dispatcher);if(dispatcher.getRoot().getChild("box")==null)throw new AssertionError("Commands");
 for(int i=0;i<=4;i++){var chest=TrainerChests.item(i);if(chest.isEmpty())throw new AssertionError("Chest"+i);}
 System.out.println("PASS NATIVE COMMANDS/CHESTS: box tree,5custom chest items");
 server.shutdown();System.out.println("PASS PORT SERVER SMOKE");
 }
}
