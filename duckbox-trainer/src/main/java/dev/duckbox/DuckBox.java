package dev.duckbox;

import static net.minecraft.server.command.CommandManager.*;

import com.google.gson.*;
import com.mojang.brigadier.arguments.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.*;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.command.CommandSource;
import net.minecraft.command.argument.IdentifierArgumentType;
import net.minecraft.component.type.AttributeModifierSlot;
import net.minecraft.entity.*;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.*;
import net.minecraft.server.*;
import net.minecraft.server.command.*;
import net.minecraft.server.network.*;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.*;
import net.minecraft.util.math.*;
import net.minecraft.world.*;
import net.minecraft.world.GameMode;

public final class DuckBox implements ModInitializer {
  public static MinecraftServer server;
  public static Options options = new Options();
  public static Session session;
  private static JsonObject disk = new JsonObject();
  private static final Gson JSON = new GsonBuilder().setPrettyPrinting().create();
  private static Path file;
  private static final Map<UUID, Long> rockets = new HashMap<>();
  private static final Map<UUID, Long> clicks = new HashMap<>();

  @Override
  public void onInitialize() {
    dev.duckbox.panels.MapPanels.init();
    PayloadTypeRegistry.playS2C().register(TrainingPayload.ID, TrainingPayload.CODEC);
    PayloadTypeRegistry.playS2C().register(ChestRolePayload.ID, ChestRolePayload.CODEC);
    PayloadTypeRegistry.playS2C().register(LobbyBotPayload.ID, LobbyBotPayload.CODEC);
    net.fabricmc.fabric.api.event.lifecycle.v1.ServerChunkEvents.CHUNK_LOAD.register(
        (world, chunk) -> {
          for (var entity : chunk.getBlockEntities().values())
            if (entity instanceof net.minecraft.block.entity.ChestBlockEntity chest)
              ChestRoleSync.remember(world, chest);
        });
    PayloadTypeRegistry.playS2C().register(CosmeticPayload.ID, CosmeticPayload.CODEC);
    ServerLifecycleEvents.SERVER_STARTED.register(
        s -> {
          server = s;
          file =
              s.getSavePath(net.minecraft.util.WorldSavePath.ROOT).resolve("duckbox-training.json");
          load();
        });
    ServerLifecycleEvents.SERVER_STOPPING.register(
        s -> {
          KitEditor.flush();
          LobbyBot.clear(s);
          if (session != null) stop("Servidor encerrado.");
        });
    ServerLifecycleEvents.SERVER_STOPPED.register(
        s -> {
          server = null;
          session = null;
          rockets.clear();
          clicks.clear();
          Arena.reset();
          SpawnControl.clear();
          ChestRoleSync.clear();
          KitEditor.reset();
          FixedHolograms.clear();
        });
    ServerTickEvents.END_SERVER_TICK.register(
        s -> {
          Arena.tick();
          LobbyBot.tick(s);
          SpawnControl.tick(s);
          ChestRoleSync.tick(s);
          if (session != null) {
            if (session.finish != null) stop(session.finish);
            else if (session.owner.isDisconnected()) stop("Jogador saiu.");
            else {
              try {
                session.bot.tick();
                if (session.finish != null) stop(session.finish);
                else session.status();
              } catch (RuntimeException e) {
                org.slf4j.LoggerFactory.getLogger("DuckBox")
                    .error("Erro no tick do bot; encerrando treino", e);
                stop("Treino interrompido. Veja o log DuckBox.");
              }
            }
          }
        });
    ServerPlayConnectionEvents.JOIN.register(
        (handler, sender, s) -> {
          if (handler.player instanceof TrainingBot) return;
          restore(handler.player);
          ChestRoleSync.forget(handler.player.getUuid());
          syncCosmetics();
          Arena.updateRulesLabel(handler.player.getServerWorld(), options);
          Arena.ensureCpsControl(handler.player.getServerWorld(), options);
          if (options.autoBuildOnJoin && !options.built && !Arena.building()) {
            options.x = Options.ARENA_X;
            options.y = Options.ARENA_Y;
            options.z = Options.ARENA_Z;
            options.dimension = "minecraft:overworld";
            options.initialized = true;
            Arena.create(handler.player, options);
          }
        });
    ServerPlayConnectionEvents.DISCONNECT.register(
        (handler, s) -> {
          KitEditor.closeFor(handler.player);
          FixedHolograms.forget(handler.player.getUuid());
          if (session != null && session.owner == handler.player) stop("Jogador saiu.");
        });
    PlayerBlockBreakEvents.BEFORE.register(
        (w, p, pos, state, entity) ->
            session == null
                || p != session.owner
                || w != world()
                || state.isOf(net.minecraft.block.Blocks.COBWEB)
                || (pos.getY() > options.y
                    && pos.getY() < options.y + Arena.HEIGHT
                    && (session.isTrainingBlock(pos)
                        || state.isIn(net.minecraft.registry.tag.BlockTags.WOOL)))
                || Math.abs(pos.getX() - options.x) > options.size / 2
                || Math.abs(pos.getZ() - options.z) > options.size / 2
                || pos.getY() < options.y
                || pos.getY() > options.y + 10);
    PlayerBlockBreakEvents.AFTER.register(
        (world, player, pos, state, entity) -> {
          if (world instanceof ServerWorld serverWorld) FixedHolograms.removeAt(serverWorld, pos);
        });
    ServerLivingEntityEvents.ALLOW_DAMAGE.register(
        (entity, source, amount) -> allowTrainingDamage(entity, source));
    ServerLivingEntityEvents.ALLOW_DEATH.register(DuckBox::allowTrainingDeath);
    ServerLivingEntityEvents.AFTER_DAMAGE.register(
        (entity, source, base, taken, blocked) -> {
          if (!blocked && taken > 0) shortenTrainingHitWindow(entity, source);
        });
    UseBlockCallback.EVENT.register(
        (p, w, hand, hit) -> {
          if (session != null && session.countingDown() && (p == session.owner || p == session.bot))
            return ActionResult.FAIL;
          ActionResult rocketUse = useFlyingRocket(p, hand);
          if (rocketUse.isAccepted()) return rocketUse;
          if (w.isClient() || hand != Hand.MAIN_HAND || p instanceof TrainingBot)
            return ActionResult.PASS;
          if (p instanceof ServerPlayerEntity real && FixedHolograms.click(real, hit))
            return ActionResult.SUCCESS;
          ActionResult trainerChest = TrainerChests.open(p, (ServerWorld) w, hand, hit);
          if (trainerChest.isAccepted()) return trainerChest;
          if (Arena.isKitChest(hit.getBlockPos(), (ServerWorld) w, options)) {
            if (!p.hasPermissionLevel(2)) return ActionResult.FAIL;
            try {
              KitEditor.open((ServerPlayerEntity) p);
            } catch (Exception e) {
              say((ServerPlayerEntity) p, e.getMessage());
            }
            return ActionResult.SUCCESS;
          }
          String key = Arena.control(hit.getBlockPos(), (ServerWorld) w, options);
          if (key == null) return ActionResult.PASS;
          if (!p.hasPermissionLevel(2)) return ActionResult.FAIL;
          long now = w.getTime();
          if (clicks.getOrDefault(p.getUuid(), -20L) + 5 > now) return ActionResult.SUCCESS;
          clicks.put(p.getUuid(), now);
          try {
            control((ServerPlayerEntity) p, key);
          } catch (Exception e) {
            say((ServerPlayerEntity) p, e.getMessage());
          }
          return ActionResult.SUCCESS;
        });
    CommandRegistrationCallback.EVENT.register(
        (dispatcher, registry, environment) -> registerCommands(dispatcher));
  }

  public static void registerCommands(
      com.mojang.brigadier.CommandDispatcher<ServerCommandSource> dispatcher) {
    dispatcher.register(literal("spawn").executes(c -> run(c.getSource(), SpawnControl::command)));
    dispatcher.register(
        literal("box")
            .requires(x -> x.hasPermissionLevel(2))
            .then(
                literal("moveholo")
                    .executes(c -> run(c.getSource(), FixedHolograms::moveCommand))));
    dispatcher.register(
        literal("box")
            .requires(x -> x.hasPermissionLevel(2))
            .then(literal("setspawn").executes(c -> run(c.getSource(), SpawnControl::set)))
            .then(literal("spawnbot").executes(c -> run(c.getSource(), LobbyBot::place)))
            .then(
                literal("skull")
                    .then(
                        argument("jogador", StringArgumentType.word())
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p ->
                                            SkullCommand.give(
                                                p, StringArgumentType.getString(c, "jogador"))))))
            .then(
                literal("blocos")
                    .executes(c -> run(c.getSource(), dev.duckbox.panels.PanelMenu::open)))
            .then(
                literal("bloco")
                    .then(
                        argument("nome", StringArgumentType.word())
                            .suggests(
                                (c, b) ->
                                    CommandSource.suggestMatching(
                                        dev.duckbox.panels.MapPanels.NAMES, b))
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p ->
                                            dev.duckbox.panels.MapPanels.give(
                                                p, StringArgumentType.getString(c, "nome"))))))
            .then(
                literal("holo")
                    .then(
                        literal("cancelar")
                            .executes(c -> run(c.getSource(), FixedHolograms::cancel)))
                    .then(
                        literal("remover")
                            .executes(c -> run(c.getSource(), FixedHolograms::remove)))
                    .then(
                        argument("texto", StringArgumentType.greedyString())
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p ->
                                            FixedHolograms.command(
                                                p, StringArgumentType.getString(c, "texto"))))))
            .then(literal("configurar").executes(c -> run(c.getSource(), ConfigMenu::open)))
            .then(
                literal("profile")
                    .executes(c -> run(c.getSource(), p -> control(p, "profile")))
                    .then(
                        argument("numero", IntegerArgumentType.integer(1, 4))
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p ->
                                            setProfile(
                                                p, IntegerArgumentType.getInteger(c, "numero"))))))
            .then(
                literal("rename")
                    .then(
                        literal("profile")
                            .then(
                                argument("numero", IntegerArgumentType.integer(1, 4))
                                    .then(
                                        argument("nome", StringArgumentType.greedyString())
                                            .executes(
                                                c ->
                                                    run(
                                                        c.getSource(),
                                                        p ->
                                                            renameProfile(
                                                                p,
                                                                IntegerArgumentType.getInteger(
                                                                    c, "numero"),
                                                                StringArgumentType.getString(
                                                                    c, "nome")))))))
                    .then(
                        argument("nome", StringArgumentType.greedyString())
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p ->
                                            renameItem(
                                                p, StringArgumentType.getString(c, "nome"))))))
            .then(
                literal("chest")
                    .then(
                        literal("profile")
                            .then(
                                argument("numero", IntegerArgumentType.integer(1, 4))
                                    .executes(
                                        c ->
                                            run(
                                                c.getSource(),
                                                p ->
                                                    TrainerChests.give(
                                                        p,
                                                        IntegerArgumentType.getInteger(
                                                            c, "numero"))))))
                    .then(
                        literal("stock")
                            .executes(c -> run(c.getSource(), p -> TrainerChests.give(p, 0))))
                    .then(
                        literal("cofre")
                            .executes(c -> run(c.getSource(), p -> TrainerChests.give(p, 0)))))
            .then(
                literal("golpes")
                    .executes(
                        c ->
                            run(
                                c.getSource(),
                                p -> {
                                  if (session == null || session.owner != p)
                                    throw new IllegalArgumentException(
                                        "Inicie seu treino primeiro.");
                                  say(p, session.bot.hitReport());
                                })))
            .then(
                literal("regras")
                    .executes(c -> run(c.getSource(), p -> control(p, "regras")))
                    .then(
                        argument("tipo", StringArgumentType.word())
                            .suggests(
                                (c, b) ->
                                    CommandSource.suggestMatching(
                                        List.of("SPAM", "SEMI_INSTA", "INSTA_KILL"), b))
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p -> {
                                          requireStopped();
                                          options.rules =
                                              Options.Rules.parse(
                                                  StringArgumentType.getString(c, "tipo")
                                                      .toUpperCase(Locale.ROOT));
                                          Arena.updateRulesLabel(p.getServerWorld(), options);
                                          Arena.applyTheme(p.getServerWorld(), options);
                                          save();
                                          setting(p, "Regras: " + options.rules);
                                        }))))
            .then(
                literal("cps")
                    .executes(c -> run(c.getSource(), p -> control(p, "cps")))
                    .then(
                        argument("valor", IntegerArgumentType.integer(10, 20))
                            .suggests(
                                (c, b) ->
                                    CommandSource.suggestMatching(
                                        List.of("10", "13", "15", "20"), b))
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p ->
                                            setBotCps(
                                                p, IntegerArgumentType.getInteger(c, "valor"))))))
            .then(
                literal("giro")
                    .executes(c -> run(c.getSource(), p -> control(p, "giro_nivel")))
                    .then(
                        argument("nivel", StringArgumentType.word())
                            .suggests(
                                (c, b) ->
                                    CommandSource.suggestMatching(
                                        List.of("BAIXO", "MEDIO", "ALTO", "EXTREMO"), b))
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p -> {
                                          options.spin =
                                              Options.SpinLevel.valueOf(
                                                  StringArgumentType.getString(c, "nivel")
                                                      .toUpperCase(Locale.ROOT));
                                          save();
                                          Arena.updateSpinLabel(world(), options);
                                          setting(p, "Giro: " + options.spin);
                                        }))))
            .then(
                literal("cosmetico")
                    .then(
                        argument("nome", StringArgumentType.word())
                            .suggests(
                                (c, b) ->
                                    CommandSource.suggestMatching(
                                        List.of("blood", "money", "oculos", "sapo"), b))
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p -> {
                                          switch (StringArgumentType.getString(c, "nome")) {
                                            case "blood" -> options.blood = !options.blood;
                                            case "money" -> options.money = !options.money;
                                            case "oculos" -> options.glasses = !options.glasses;
                                            case "sapo" -> options.frog = !options.frog;
                                            default ->
                                                throw new IllegalArgumentException(
                                                    "Use blood, money, oculos ou sapo");
                                          }
                                          syncCosmetics();
                                          save();
                                          String name = StringArgumentType.getString(c, "nome");
                                          toggleSetting(p, name, cosmeticEnabled(name));
                                        })))));
    dispatcher.register(
        literal("box")
            .requires(s -> s.hasPermissionLevel(2))
            .executes(
                c ->
                    run(
                        c.getSource(),
                        p -> {
                          say(
                              p,
                              "/box configurar | criar [9/13/17] | usar | iniciar | parar | cps"
                                  + " 10/13/15/20 | dificuldade LOW/MEDIUM/HIGH/EXPERT | habilidade"
                                  + " nome | modo DUEL/TANK | kit salvar/padrao | atributo"
                                  + " minecraft:max_health 100 HEAD | profile 1..4 | chest profile"
                                  + " 1..4 | chest stock | rename nome | rename profile numero nome"
                                  + " | habilidade nao_correr_retotem/teia_pe");
                        }))
            .then(literal("usar").executes(c -> run(c.getSource(), DuckBox::useCustomMap)))
            .then(
                literal("limparpainel")
                    .executes(
                        c ->
                            run(
                                c.getSource(),
                                p -> {
                                  requireStopped();
                                  Arena.clearOldPanel(p.getServerWorld(), options);
                                  setting(p, "Painel antigo removido. Use /box configurar.");
                                })))
            .then(
                literal("criar")
                    .executes(c -> run(c.getSource(), p -> Arena.create(p, options)))
                    .then(
                        argument("tamanho", IntegerArgumentType.integer(9, 17))
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p -> {
                                          requireStopped();
                                          int size = IntegerArgumentType.getInteger(c, "tamanho");
                                          if (size != 9 && size != 13 && size != 17)
                                            throw new IllegalArgumentException(
                                                "Tamanhos: 9, 13 ou 17.");
                                          options.size = size;
                                          Arena.create(p, options);
                                        }))))
            .then(literal("tamanho").executes(c -> run(c.getSource(), p -> control(p, "tamanho"))))
            .then(literal("iniciar").executes(c -> run(c.getSource(), DuckBox::start)))
            .then(
                literal("parar").executes(c -> run(c.getSource(), p -> stop("Treino encerrado."))))
            .then(
                literal("dificuldade")
                    .then(
                        argument("nivel", StringArgumentType.word())
                            .suggests(
                                (c, b) ->
                                    CommandSource.suggestMatching(
                                        List.of("LOW", "MEDIUM", "HIGH", "EXPERT"), b))
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p -> {
                                          options.difficulty =
                                              Options.Difficulty.valueOf(
                                                  StringArgumentType.getString(c, "nivel")
                                                      .toUpperCase(Locale.ROOT));
                                          save();
                                          setting(p, "Dificuldade: " + options.difficulty);
                                        }))))
            .then(
                literal("habilidade")
                    .then(
                        argument("nome", StringArgumentType.word())
                            .suggests(
                                (c, b) ->
                                    CommandSource.suggestMatching(
                                        List.of(
                                            "giro",
                                            "gap",
                                            "retotem",
                                            "teia",
                                            "wtap",
                                            "strafe",
                                            "foguete_teia",
                                            "nao_correr_retotem",
                                            "teia_pe",
                                            "resistencia2"),
                                        b))
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p -> {
                                          String key = StringArgumentType.getString(c, "nome");
                                          toggleSetting(p, key, options.toggle(key));
                                          save();
                                        }))))
            .then(
                literal("modo")
                    .executes(c -> run(c.getSource(), p -> control(p, "modo")))
                    .then(
                        argument("tipo", StringArgumentType.word())
                            .suggests(
                                (c, b) -> CommandSource.suggestMatching(List.of("DUEL", "TANK"), b))
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p -> {
                                          requireStopped();
                                          String mode = StringArgumentType.getString(c, "tipo");
                                          if (!mode.equalsIgnoreCase("TANK")
                                              && !mode.equalsIgnoreCase("DUEL"))
                                            throw new IllegalArgumentException("Use DUEL ou TANK.");
                                          options.tank = mode.equalsIgnoreCase("TANK");
                                          save();
                                          setting(p, "Modo: " + mode);
                                        }))))
            .then(
                literal("kit")
                    .then(literal("abrir").executes(c -> run(c.getSource(), KitEditor::open)))
                    .then(
                        literal("salvar")
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p -> {
                                          requireStopped();
                                          storeKit(p, Kits.capture(p));
                                          save();
                                          say(
                                              p,
                                              "Kit salvo. Jogador e bot receberao copias"
                                                  + " iguais.");
                                        })))
                    .then(
                        literal("padrao")
                            .executes(
                                c ->
                                    run(
                                        c.getSource(),
                                        p -> {
                                          requireStopped();
                                          resetKit(p);
                                          say(p, "Kit padrao selecionado.");
                                        }))))
            .then(
                literal("atributo")
                    .then(
                        argument("atributo", IdentifierArgumentType.identifier())
                            .then(
                                argument("valor", DoubleArgumentType.doubleArg(-1024, 1024))
                                    .then(
                                        argument("slot", StringArgumentType.word())
                                            .suggests(
                                                (c, b) ->
                                                    CommandSource.suggestMatching(
                                                        List.of(
                                                            "HEAD",
                                                            "CHEST",
                                                            "LEGS",
                                                            "FEET",
                                                            "MAINHAND",
                                                            "OFFHAND",
                                                            "ANY"),
                                                        b))
                                            .executes(
                                                c ->
                                                    run(
                                                        c.getSource(),
                                                        p -> {
                                                          requireStopped();
                                                          Kits.attribute(
                                                              p,
                                                              IdentifierArgumentType.getIdentifier(
                                                                      c, "atributo")
                                                                  .toString(),
                                                              DoubleArgumentType.getDouble(
                                                                  c, "valor"),
                                                              AttributeModifierSlot.valueOf(
                                                                  StringArgumentType.getString(
                                                                          c, "slot")
                                                                      .toUpperCase(Locale.ROOT)));
                                                          say(
                                                              p,
                                                              "Item alterado. Use /box kit"
                                                                  + " salvar para atualizar"
                                                                  + " o kit.");
                                                        })))))));
  }

  public static ServerPlayerEntity resolveCommandPlayer(ServerCommandSource source) {
    if (source.getEntity() instanceof ServerPlayerEntity p && !(p instanceof TrainingBot)) return p;
    return source.getWorld().getPlayers().stream()
        .filter(
            p ->
                !(p instanceof TrainingBot)
                    && p.isAlive()
                    && !p.isDisconnected()
                    && !p.isSpectator())
        .min(
            java.util.Comparator.comparingDouble(
                p -> p.getPos().squaredDistanceTo(source.getPosition())))
        .orElseThrow(
            () ->
                new IllegalArgumentException(
                    "Nenhum jogador real neste mundo. Use execute as @p at @s run box ..."));
  }

  private interface Task {
    void run(ServerPlayerEntity p) throws Exception;
  }

  private static int run(ServerCommandSource s, Task task) {
    try {
      task.run(resolveCommandPlayer(s));
      return 1;
    } catch (Exception e) {
      s.sendError(Text.literal("DuckBox: " + e.getMessage()));
      return 0;
    }
  }

  private static Text feedback(String message, Formatting color) {
    return Text.empty()
        .append(Text.literal("Duck").formatted(Formatting.YELLOW, Formatting.BOLD))
        .append(Text.literal("Box ").formatted(Formatting.GOLD, Formatting.BOLD))
        .append(Text.literal("» ").formatted(Formatting.DARK_GRAY))
        .append(Text.literal(message).formatted(color));
  }

  public static void say(ServerPlayerEntity p, String message) {
    p.sendMessage(feedback(message, Formatting.GRAY), false);
  }

  public static void setting(ServerPlayerEntity p, String message) {
    showSetting(p, message, Formatting.AQUA);
  }

  private static void showSetting(ServerPlayerEntity p, String message, Formatting color) {
    p.sendMessage(feedback(message, color), true);
    if (session != null && session.owner == p) session.holdSettingMessage();
  }

  public static boolean cosmeticEnabled(String key) {
    return switch (key) {
      case "blood" -> options.blood;
      case "money" -> options.money;
      case "oculos" -> options.glasses;
      case "sapo" -> options.frog;
      default -> false;
    };
  }

  public static void toggleSetting(ServerPlayerEntity p, String key, boolean value) {
    String name =
        switch (key) {
          case "giro" -> "Giro";
          case "retotem" -> "Retotem";
          case "gap" -> "Gap";
          case "nao_correr_retotem" -> "Nao correr no retotem";
          case "teia_pe" -> "Teia no pe";
          case "resistencia2" -> "Resistencia II (Spam)";
          case "teia" -> "Teia";
          case "wtap" -> "W-tap";
          case "strafe" -> "Strafe";
          case "foguete_teia" -> "Foguete na teia";
          case "blood" -> "Punho Blood";
          case "money" -> "Aura Money";
          case "oculos" -> "Oculos gamer";
          case "sapo" -> "Chapeu de sapo";
          default -> key;
        };
    showSetting(p, name + " " + (value ? "ON" : "OFF"), value ? Formatting.GREEN : Formatting.RED);
  }

  public static void checkProfile(int id) {
    if (id < 1 || id > 4) throw new IllegalArgumentException("Perfil deve ser1,2,3 ou4.");
  }

  private static JsonObject profileKits(ServerPlayerEntity p, int id) {
    checkProfile(id);
    if (!disk.has("kits")) disk.add("kits", new JsonObject());
    if (disk.has("kit")) {
      var old = Kits.decode(p, disk.getAsJsonArray("kit"));
      for (int i = 0; i < old.size(); i++)
        if (old.get(i).isOf(net.minecraft.item.Items.YELLOW_DYE) && Kits.isTotem(old.get(i)))
          old.set(
              i,
              i == 40
                  ? Kits.duckCharm()
                  : new ItemStack(net.minecraft.item.Items.TOTEM_OF_UNDYING));
      disk.getAsJsonObject("kits").add(Options.Rules.INSTA_KILL.name(), Kits.encode(p, old));
      disk.remove("kit");
    }
    if (!disk.has("kitProfiles")) disk.add("kitProfiles", new JsonObject());
    var profiles = disk.getAsJsonObject("kitProfiles");
    if (!profiles.has("1")) profiles.add("1", new JsonObject());
    var legacy = disk.getAsJsonObject("kits");
    if (legacy.size() > 0) {
      var first = profiles.getAsJsonObject("1");
      for (var entry : legacy.entrySet())
        if (!first.has(entry.getKey())) first.add(entry.getKey(), entry.getValue());
      disk.remove("kits");
      save();
    } else disk.remove("kits");
    String key = Integer.toString(id);
    if (!profiles.has(key)) profiles.add(key, new JsonObject());
    return profiles.getAsJsonObject(key);
  }

  public static List<ItemStack> currentKit(ServerPlayerEntity p) {
    return currentKit(p, options.profile);
  }

  public static List<ItemStack> currentKit(ServerPlayerEntity p, int profile) {
    var kits = profileKits(p, profile);
    boolean migrated = !kits.has("inventory");
    var data = kits.getAsJsonArray("inventory");
    if (data == null) {
      String previousMode =
          kits.has(options.rules.name())
              ? options.rules.name()
              : kits.has(Options.Rules.NORMAL_SPAM.name())
                  ? Options.Rules.NORMAL_SPAM.name()
                  : Options.Rules.INSTA_KILL.name();
      if (kits.has(previousMode)) data = kits.getAsJsonArray(previousMode);
    }
    var kit =
        data != null
            ? Kits.decode(p, data)
            : Kits.defaults(p.getRegistryManager(), Options.Rules.NORMAL_SPAM);
    boolean repaired =
        migrated && options.rules == Options.Rules.NORMAL_SPAM && Kits.repairNormalKit(kit);
    repaired |= Kits.protectEquipment(p.getRegistryManager(), kit);
    repaired |= Kits.upgradeTrainingSword(p.getRegistryManager(), kit);
    if (migrated || repaired) storeKit(p, kit, profile, options.rules);
    return kit;
  }

  public static void storeKit(ServerPlayerEntity p, List<ItemStack> kit) {
    storeKit(p, kit, options.profile, options.rules);
  }

  public static void storeKit(
      ServerPlayerEntity p, List<ItemStack> kit, int profile, Options.Rules rules) {
    // Rules are combat behavior; the profile owns one inventory for both modes.
    // Legacy mode-specific keys are retained as a backup, but no longer selected.
    profileKits(p, profile).add("inventory", Kits.encode(p, kit));
    save();
  }

  public static void resetKit(ServerPlayerEntity p) {
    storeKit(p, Kits.defaults(p.getRegistryManager(), Options.Rules.NORMAL_SPAM));
  }

  public static Text profileName(int profile) {
    checkProfile(profile);
    if (disk.has("profileNames")
        && disk.getAsJsonObject("profileNames").has(Integer.toString(profile)))
      return RichNames.parse(
          disk.getAsJsonObject("profileNames").get(Integer.toString(profile)).getAsString());
    return Text.literal("Perfil " + profile).formatted(Formatting.AQUA);
  }

  public static void renameProfile(ServerPlayerEntity p, int id, String raw) {
    checkProfile(id);
    RichNames.parse(raw);
    if (!disk.has("profileNames")) disk.add("profileNames", new JsonObject());
    disk.getAsJsonObject("profileNames").addProperty(Integer.toString(id), raw);
    save();
    settingRich(p, Text.literal("Kit renomeado: ").append(profileName(id)));
  }

  public static void setProfile(ServerPlayerEntity p, int id) {
    checkProfile(id);
    requireStopped();
    options.profile = id;
    save();
    settingRich(p, Text.literal("Perfil selecionado: ").append(profileName(id)));
  }

  public static void settingRich(ServerPlayerEntity p, Text text) {
    p.sendMessage(
        Text.empty().append(Text.literal("DuckBox » ").formatted(Formatting.GOLD)).append(text),
        true);
    if (session != null && session.owner == p) session.holdSettingMessage();
  }

  public static void renameItem(ServerPlayerEntity p, String raw) {
    var held = p.getMainHandStack();
    if (held.isEmpty()) throw new IllegalArgumentException("Segure o item para renomear.");
    held.set(net.minecraft.component.DataComponentTypes.CUSTOM_NAME, RichNames.parse(raw));
    p.getInventory().markDirty();
    p.currentScreenHandler.sendContentUpdates();
    settingRich(p, Text.literal("Item renomeado: ").append(held.getName()));
  }

  public static boolean allowTrainingDeath(
      net.minecraft.entity.LivingEntity entity,
      net.minecraft.entity.damage.DamageSource source,
      float amount) {
    if (session == null || (entity != session.owner && entity != session.bot)) return true;
    if (session.finish != null) return false;
    // Fabric asks BEFORE vanilla tries death protection, not after the totem.
    if (!source.isIn(net.minecraft.registry.tag.DamageTypeTags.BYPASSES_INVULNERABILITY))
      for (Hand hand : Hand.values())
        if (entity
            .getStackInHand(hand)
            .contains(net.minecraft.component.DataComponentTypes.DEATH_PROTECTION)) return true;
    session.owner.sendMessage(
        Text.literal("DuckBot » " + session.roundMessage(entity == session.bot))
            .formatted(Formatting.AQUA),
        false);
    entity.setHealth(1);
    session.finish = entity == session.bot ? "Voce venceu!" : "O bot venceu. Tente novamente!";
    return false;
  }

  public static void shortenTrainingHitWindow(
      net.minecraft.entity.LivingEntity target, net.minecraft.entity.damage.DamageSource source) {
    if (session == null
        || session.closed
        || session.countingDown()
        || session.o.rules != Options.Rules.INSTA_KILL) return;
    if ((target == session.owner && source.getAttacker() == session.bot)
        || (target == session.bot && source.getAttacker() == session.owner))
      target.timeUntilRegen = Math.min(target.timeUntilRegen, 15);
  }

  public static boolean allowTrainingDamage(
      net.minecraft.entity.LivingEntity entity, net.minecraft.entity.damage.DamageSource source) {
    return session == null
        || (entity != session.owner && entity != session.bot)
        || (!session.countingDown()
            && !source.isOf(net.minecraft.entity.damage.DamageTypes.FALL)
            && !source.isOf(net.minecraft.entity.damage.DamageTypes.FLY_INTO_WALL));
  }

  public static boolean opponents(
      net.minecraft.entity.player.PlayerEntity a, net.minecraft.entity.player.PlayerEntity b) {
    Session active = session;
    return active != null
        && !active.closed
        && ((a == active.owner && b == active.bot) || (b == active.owner && a == active.bot));
  }

  public static void requireStopped() {
    if (session != null || Arena.building() || KitEditor.editing())
      throw new IllegalArgumentException("Encerre o treino e aguarde a construcao.");
  }

  public static void control(ServerPlayerEntity p, String key) {
    switch (key) {
      case "iniciar" -> start(p);
      case "parar" -> stop("Treino encerrado.");
      case "dificuldade" -> {
        options.difficulty = Options.Difficulty.values()[(options.difficulty.ordinal() + 1) % 4];
        setting(p, "Dificuldade: " + options.difficulty);
        save();
      }
      case "modo" -> {
        requireStopped();
        options.tank = !options.tank;
        Arena.updateModeLabel(p.getServerWorld(), options);
        save();
        setting(p, "Modo: " + (options.tank ? "Tank" : "Duel"));
      }
      case "cps" -> setBotCps(p, Options.nextCps(options.cps));
      case "profile" -> setProfile(p, options.profile % 4 + 1);
      case "giro_nivel" -> {
        options.spin = Options.SpinLevel.values()[(options.spin.ordinal() + 1) % 4];
        save();
        Arena.updateSpinLabel(world(), options);
        setting(p, "Giro: " + options.spin);
      }
      case "regras" -> {
        requireStopped();
        options.rules =
            options.rules == Options.Rules.NORMAL_SPAM
                ? Options.Rules.INSTA_KILL
                : Options.Rules.NORMAL_SPAM;
        Arena.updateRulesLabel(p.getServerWorld(), options);
        Arena.applyTheme(p.getServerWorld(), options);
        save();
        setting(p, "Regras: " + options.rules);
      }
      case "tamanho" -> {
        requireStopped();
        options.size = Options.nextSize(options.size);
        if (options.customMap) {
          save();
          setting(p, "Limites da arena: " + options.size + "x" + options.size);
          break;
        }
        Arena.create(p, options);
      }
      default -> {
        boolean active = options.toggle(key);
        var pos = p.getServerWorld();
        for (var entry : Arena.controls.entrySet())
          if (entry.getValue().equals(key)) {
            var state = pos.getBlockState(entry.getKey());
            if (state.contains(net.minecraft.block.LeverBlock.POWERED))
              pos.setBlockState(
                  entry.getKey(), state.with(net.minecraft.block.LeverBlock.POWERED, active), 3);
          }
        save();
        toggleSetting(p, key, active);
      }
    }
  }

  public static ServerWorld world() {
    return server.getWorld(RegistryKey.of(RegistryKeys.WORLD, Identifier.of(options.dimension)));
  }

  public static void setBotCps(ServerPlayerEntity p, int cps) {
    if (!Options.allowedCps(cps))
      throw new IllegalArgumentException("Escolha 10, 13, 15 ou 20 CPS.");
    options.cps = cps;
    Arena.updateCpsLabel(p.getServerWorld(), options);
    save();
    setting(p, "CPS do bot: " + cps);
  }

  public static void useCustomMap(ServerPlayerEntity p) {
    requireStopped();
    options.x = Options.ARENA_X;
    options.y = Options.ARENA_Y;
    options.z = Options.ARENA_Z;
    options.dimension = p.getServerWorld().getRegistryKey().getValue().toString();
    options.initialized = true;
    options.built = true;
    options.customMap = true;
    options.autoBuildOnJoin = false;
    Arena.controls.clear();
    disk.addProperty("arenaPositionRevision", 1);
    save();
    say(
        p,
        "Mapa vinculado: centro do piso -5 78 111. Construcoes preservadas; use comandos ate"
            + " vincular seus botoes.");
  }

  public static void start(ServerPlayerEntity p) {
    KitEditor.closeFor(p);
    requireStopped();
    if (!options.built)
      throw new IllegalArgumentException(
          "Use /box criar para gerar ou /box usar para vincular seu mapa.");
    if (p.getServerWorld() != world())
      throw new IllegalArgumentException("Entre na dimensao da arena.");
    if (p.isSpectator()) throw new IllegalArgumentException("Saia do modo espectador.");
    if (p.hasVehicle()) throw new IllegalArgumentException("Desmonte antes de iniciar.");
    if (p.isUsingItem()) p.stopUsingItem();
    List<ItemStack> kit = currentKit(p);
    boolean sword = kit.stream().anyMatch(i -> i.isIn(net.minecraft.registry.tag.ItemTags.SWORDS));
    if (!sword) throw new IllegalArgumentException("O kit precisa de uma espada.");
    backup(p);
    TrainingBot bot = new TrainingBot(server, world());
    try {
      server
          .getPlayerManager()
          .onPlayerConnect(
              new TrainingBot.LocalConnection(),
              bot,
              ConnectedClientData.createDefault(bot.getGameProfile(), false));
      bot.changeGameMode(GameMode.SURVIVAL);
      Kits.give(bot, kit);
      Kits.give(p, kit);
      p.changeGameMode(GameMode.SURVIVAL);
      p.clearStatusEffects();
      bot.clearStatusEffects();
      p.getHungerManager().setFoodLevel(20);
      Arena.clearWebs(world(), options);
      bot.teleport(
          world(), options.x + 2.5, options.y + 1, options.z + 0.5, Set.of(), 90, 0, false);
      p.teleport(world(), options.x - 2.5, options.y + 1, options.z + 0.5, Set.of(), -90, 0, false);
      bot.setLoaded(true);
      bot.onTeleportationDone();
      session = new Session(p, bot, options);
      session.beginCountdown();
      syncCosmetics();
      sync();
      say(
          p,
          "Treino iniciado: "
              + options.difficulty
              + " / "
              + (options.tank ? "TANK" : "DUEL")
              + ". /box parar para sair.");
    } catch (Exception error) {
      if (server.getPlayerManager().getPlayer(bot.getUuid()) != null)
        server.getPlayerManager().remove(bot);
      restore(p);
      throw error;
    }
  }

  public static void stop(String reason) {
    Session s = session;
    if (s == null) return;
    s.closed = true;
    if (canSendTraining(s.owner))
      ServerPlayNetworking.send(
          s.owner, new TrainingPayload(s.owner.getUuid(), new UUID(0, 0), false));
    session = null;
    syncCosmetics();
    s.cleanupBuilding();
    s.bot.stopUsingItem();
    s.bot.getInventory().clear();
    server.getPlayerManager().remove(s.bot);
    rockets.clear();
    if (!s.owner.isDisconnected()) {
      restore(s.owner);
      SpawnControl.move(s.owner, s.bot.getServerWorld());
      s.owner.sendMessage(Text.literal(reason).formatted(Formatting.GOLD), false);
    }
    Arena.clearWebs(s.bot.getServerWorld(), options);
  }

  private static void load() {
    options = new Options();
    disk = new JsonObject();
    if (!Files.exists(file)) return;
    try {
      disk = JsonParser.parseString(Files.readString(file)).getAsJsonObject();
      if (disk.has("options")) options = JSON.fromJson(disk.get("options"), Options.class);
      if (options == null) options = new Options();
      int revision = disk.has("arenaRevision") ? disk.get("arenaRevision").getAsInt() : 0;
      if (revision < 3) {
        if (revision < 2) {
          if (options.size == 25) options.size = 13;
          options.tank = false;
        }
        options.built = false;
        disk.addProperty("arenaRevision", 3);
      }
      if (options.rules == null) options.rules = Options.Rules.NORMAL_SPAM;
      if (options.spin == null) options.spin = Options.SpinLevel.MEDIO;
      options.size = Options.allowedSize(options.size);
      if (!Options.allowedCps(options.cps)) options.cps = 15;
      if (options.profile < 1 || options.profile > 4) options.profile = 1;
      if (!disk.has("arenaPositionRevision")) {
        if (options.x != Options.ARENA_X
            || options.y != Options.ARENA_Y
            || options.z != Options.ARENA_Z) options.built = false;
        options.x = Options.ARENA_X;
        options.y = Options.ARENA_Y;
        options.z = Options.ARENA_Z;
        disk.addProperty("arenaPositionRevision", 1);
      }
    } catch (Exception e) {
      throw new IllegalStateException(
          "Nao foi possivel ler duckbox-training.json; arquivo preservado.", e);
    }
  }

  public static void syncCosmetics() {
    if (server == null
        || !net.fabricmc.loader.api.FabricLoader.getInstance()
            .isModLoaded("fabric-networking-api-v1")) return;
    int mask =
        (options.blood ? 1 : 0)
            | (options.money ? 2 : 0)
            | (options.glasses ? 4 : 0)
            | (options.frog ? 8 : 0);
    for (var p : server.getPlayerManager().getPlayerList())
      if (!(p instanceof TrainingBot) && ServerPlayNetworking.canSend(p, CosmeticPayload.ID)) {
        LobbyBot.sync(p, mask);
        ServerPlayNetworking.send(
            p,
            new CosmeticPayload(
                p.getUuid(), session != null ? session.bot.getUuid() : new UUID(0, 0), mask));
      }
  }

  public static boolean canSendTraining(ServerPlayerEntity player) {
    return net.fabricmc.loader.api.FabricLoader.getInstance()
            .isModLoaded("fabric-networking-api-v1")
        && ServerPlayNetworking.canSend(player, TrainingPayload.ID);
  }

  public static void sync() {
    if (session != null && !session.owner.isDisconnected() && canSendTraining(session.owner))
      ServerPlayNetworking.send(
          session.owner,
          new TrainingPayload(
              session.owner.getUuid(),
              session.bot.getUuid(),
              options.webRocket,
              options.rules == Options.Rules.INSTA_KILL));
  }

  public static void save() {
    sync();
    syncCosmetics();
    if (file == null) return;
    try {
      disk.addProperty("arenaRevision", 3);
      disk.add("options", JSON.toJsonTree(options));
      Path temp = file.resolveSibling(file.getFileName() + ".tmp");
      Files.writeString(temp, JSON.toJson(disk));
      try {
        Files.move(temp, file, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
      } catch (AtomicMoveNotSupportedException e) {
        Files.move(temp, file, StandardCopyOption.REPLACE_EXISTING);
      }
    } catch (IOException e) {
      throw new IllegalStateException("Nao foi possivel salvar o treino.", e);
    }
  }

  private static void backup(ServerPlayerEntity p) {
    if (!disk.has("backups")) disk.add("backups", new JsonObject());
    JsonObject b = new JsonObject();
    b.add("inventory", Kits.encode(p, Kits.capture(p)));
    JsonArray effects = new JsonArray();
    var ops = RegistryOps.of(com.mojang.serialization.JsonOps.INSTANCE, p.getRegistryManager());
    for (var effect : p.getStatusEffects())
      effects.add(
          net.minecraft.entity.effect.StatusEffectInstance.CODEC
              .encodeStart(ops, effect)
              .getOrThrow());
    b.add("effects", effects);
    b.addProperty("selectedSlot", p.getInventory().selectedSlot);
    b.addProperty("health", p.getHealth());
    b.addProperty("food", p.getHungerManager().getFoodLevel());
    b.addProperty("saturation", p.getHungerManager().getSaturationLevel());
    b.addProperty("mode", p.interactionManager.getGameMode().getName());
    b.addProperty("x", p.getX());
    b.addProperty("y", p.getY());
    b.addProperty("z", p.getZ());
    b.addProperty("yaw", p.getYaw());
    b.addProperty("pitch", p.getPitch());
    b.addProperty("dimension", p.getServerWorld().getRegistryKey().getValue().toString());
    disk.getAsJsonObject("backups").add(p.getUuidAsString(), b);
    save();
  }

  private static void restore(ServerPlayerEntity p) {
    if (!disk.has("backups") || !disk.getAsJsonObject("backups").has(p.getUuidAsString())) return;
    JsonObject b = disk.getAsJsonObject("backups").getAsJsonObject(p.getUuidAsString());
    Kits.give(p, Kits.decode(p, b.getAsJsonArray("inventory")));
    p.clearStatusEffects();
    if (b.has("effects")) {
      var ops = RegistryOps.of(com.mojang.serialization.JsonOps.INSTANCE, p.getRegistryManager());
      for (var effect : b.getAsJsonArray("effects"))
        p.addStatusEffect(
            net.minecraft.entity.effect.StatusEffectInstance.CODEC.parse(ops, effect).getOrThrow());
    }
    if (b.has("selectedSlot")) p.getInventory().selectedSlot = b.get("selectedSlot").getAsInt();
    p.networkHandler.sendPacket(
        new net.minecraft.network.packet.s2c.play.UpdateSelectedSlotS2CPacket(
            p.getInventory().selectedSlot));
    p.changeGameMode(GameMode.byName(b.get("mode").getAsString(), GameMode.SURVIVAL));
    p.setHealth(Math.max(1, Math.min(p.getMaxHealth(), b.get("health").getAsFloat())));
    p.getHungerManager().setFoodLevel(b.get("food").getAsInt());
    p.getHungerManager().setSaturationLevel(b.get("saturation").getAsFloat());
    ServerWorld w =
        server.getWorld(
            RegistryKey.of(RegistryKeys.WORLD, Identifier.of(b.get("dimension").getAsString())));
    if (w != null)
      p.teleport(
          w,
          b.get("x").getAsDouble(),
          b.get("y").getAsDouble(),
          b.get("z").getAsDouble(),
          Set.of(),
          b.get("yaw").getAsFloat(),
          b.get("pitch").getAsFloat(),
          false);
    disk.getAsJsonObject("backups").remove(p.getUuidAsString());
    save();
  }

  public static ActionResult useFlyingRocket(
      net.minecraft.entity.player.PlayerEntity p, Hand hand) {
    if (!p.isGliding() || !p.getStackInHand(hand).isOf(net.minecraft.item.Items.FIREWORK_ROCKET))
      return ActionResult.PASS;
    boolean training =
        p.getWorld().isClient()
            ? ClientTrainingState.participant(p)
            : session != null && (p == session.owner || p == session.bot);
    if (!training) return ActionResult.PASS;
    if (!p.getWorld().isClient()) p.getStackInHand(hand).use(p.getWorld(), p, hand);
    return ActionResult.SUCCESS;
  }

  public static void rocket(LivingEntity entity) {
    if (entity.getWorld().isClient()) {
      ClientTrainingState.boost(entity);
      return;
    }
    if (session != null && (entity == session.bot || entity == session.owner))
      rockets.put(entity.getUuid(), entity.getWorld().getTime() + 3);
  }

  public static final net.minecraft.util.math.Vec3d WEB_SLOWDOWN =
      new net.minecraft.util.math.Vec3d(0.45, 0.35, 0.45);

  public static boolean ignoreWeb(Entity entity) {
    if (entity.getWorld().isClient()) return ClientTrainingState.ignore(entity);
    return session != null
        && options.webRocket
        && (entity == session.bot || entity == session.owner)
        && entity instanceof LivingEntity living
        && living.isGliding();
  }
}
