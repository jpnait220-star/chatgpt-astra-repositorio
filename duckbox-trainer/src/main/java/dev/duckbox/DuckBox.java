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
    PayloadTypeRegistry.playS2C().register(TrainingPayload.ID, TrainingPayload.CODEC);
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
          if (session != null) stop("Servidor encerrado.");
        });
    ServerLifecycleEvents.SERVER_STOPPED.register(
        s -> {
          server = null;
          session = null;
          rockets.clear();
          clicks.clear();
          Arena.reset();
          KitEditor.reset();
        });
    ServerTickEvents.END_SERVER_TICK.register(
        s -> {
          Arena.tick();
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
          syncCosmetics();
          if (s.getSaveProperties().getLevelName().equals("DuckBoxTreino")
              && !options.built
              && !Arena.building()) {
            options.x = 0;
            options.y = 64;
            options.z = 0;
            options.dimension = "minecraft:overworld";
            options.initialized = true;
            Arena.create(handler.player, options);
          }
        });
    ServerPlayConnectionEvents.DISCONNECT.register(
        (handler, s) -> {
          KitEditor.closeFor(handler.player);
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
    ServerLivingEntityEvents.ALLOW_DAMAGE.register(
        (entity, source, amount) -> allowTrainingDamage(entity, source));
    ServerLivingEntityEvents.ALLOW_DEATH.register(DuckBox::allowTrainingDeath);
    UseBlockCallback.EVENT.register(
        (p, w, hand, hit) -> {
          if (session != null && session.countingDown() && (p == session.owner || p == session.bot))
            return ActionResult.FAIL;
          ActionResult rocketUse = useFlyingRocket(p, hand);
          if (rocketUse.isAccepted()) return rocketUse;
          if (w.isClient() || hand != Hand.MAIN_HAND || p instanceof TrainingBot)
            return ActionResult.PASS;
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
        (dispatcher, registry, environment) ->
            dispatcher.register(
                literal("box")
                    .requires(x -> x.hasPermissionLevel(2))
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
                            .then(
                                argument("tipo", StringArgumentType.word())
                                    .suggests(
                                        (c, b) ->
                                            CommandSource.suggestMatching(
                                                List.of("NORMAL_SPAM", "INSTA_KILL"), b))
                                    .executes(
                                        c ->
                                            run(
                                                c.getSource(),
                                                p -> {
                                                  requireStopped();
                                                  options.rules =
                                                      Options.Rules.valueOf(
                                                          StringArgumentType.getString(c, "tipo")
                                                              .toUpperCase(Locale.ROOT));
                                                  Arena.updateRulesLabel(
                                                      p.getServerWorld(), options);
                                                  save();
                                                  say(p, "Regras: " + options.rules);
                                                }))))
                    .then(
                        literal("giro")
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
                                                  say(p, "Giro: " + options.spin);
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
                                                    case "oculos" ->
                                                        options.glasses = !options.glasses;
                                                    case "sapo" -> options.frog = !options.frog;
                                                    default ->
                                                        throw new IllegalArgumentException(
                                                            "Use blood, money, oculos ou sapo");
                                                  }
                                                  syncCosmetics();
                                                  save();
                                                  say(p, "Cosmetico atualizado.");
                                                }))))));
    CommandRegistrationCallback.EVENT.register(
        (dispatcher, registry, environment) ->
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
                                      "/box criar [9..41] | iniciar | parar | dificuldade"
                                          + " LOW/MEDIUM/HIGH/EXPERT | habilidade nome | modo"
                                          + " DUEL/TANK | kit salvar/padrao | atributo"
                                          + " minecraft:max_health 100 HEAD");
                                }))
                    .then(
                        literal("criar")
                            .executes(c -> run(c.getSource(), p -> Arena.create(p, options)))
                            .then(
                                argument("tamanho", IntegerArgumentType.integer(9, 41))
                                    .executes(
                                        c ->
                                            run(
                                                c.getSource(),
                                                p -> {
                                                  requireStopped();
                                                  options.size =
                                                      IntegerArgumentType.getInteger(c, "tamanho")
                                                          | 1;
                                                  Arena.create(p, options);
                                                }))))
                    .then(literal("iniciar").executes(c -> run(c.getSource(), DuckBox::start)))
                    .then(
                        literal("parar")
                            .executes(c -> run(c.getSource(), p -> stop("Treino encerrado."))))
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
                                                  say(p, "Dificuldade: " + options.difficulty);
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
                                                    "foguete_teia"),
                                                b))
                                    .executes(
                                        c ->
                                            run(
                                                c.getSource(),
                                                p -> {
                                                  String key =
                                                      StringArgumentType.getString(c, "nome");
                                                  say(p, key + ": " + options.toggle(key));
                                                  save();
                                                }))))
                    .then(
                        literal("modo")
                            .then(
                                argument("tipo", StringArgumentType.word())
                                    .suggests(
                                        (c, b) ->
                                            CommandSource.suggestMatching(
                                                List.of("DUEL", "TANK"), b))
                                    .executes(
                                        c ->
                                            run(
                                                c.getSource(),
                                                p -> {
                                                  String mode =
                                                      StringArgumentType.getString(c, "tipo");
                                                  if (!mode.equalsIgnoreCase("TANK")
                                                      && !mode.equalsIgnoreCase("DUEL"))
                                                    throw new IllegalArgumentException(
                                                        "Use DUEL ou TANK.");
                                                  options.tank = mode.equalsIgnoreCase("TANK");
                                                  save();
                                                  say(p, "Modo: " + mode);
                                                }))))
                    .then(
                        literal("kit")
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
                                                  if (disk.has("kits"))
                                                    disk.getAsJsonObject("kits")
                                                        .remove(options.rules.name());
                                                  disk.remove("kit");
                                                  save();
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
                                                                      IdentifierArgumentType
                                                                          .getIdentifier(
                                                                              c, "atributo")
                                                                          .toString(),
                                                                      DoubleArgumentType.getDouble(
                                                                          c, "valor"),
                                                                      AttributeModifierSlot.valueOf(
                                                                          StringArgumentType
                                                                              .getString(c, "slot")
                                                                              .toUpperCase(
                                                                                  Locale.ROOT)));
                                                                  say(
                                                                      p,
                                                                      "Item alterado. Use /box kit"
                                                                          + " salvar para atualizar"
                                                                          + " o kit.");
                                                                }))))))));
  }

  private interface Task {
    void run(ServerPlayerEntity p) throws Exception;
  }

  private static int run(ServerCommandSource s, Task task) {
    try {
      task.run(s.getPlayerOrThrow());
      return 1;
    } catch (Exception e) {
      s.sendError(Text.literal("DuckBox: " + e.getMessage()));
      return 0;
    }
  }

  public static void say(ServerPlayerEntity p, String message) {
    p.sendMessage(
        Text.empty()
            .append(Text.literal("Duck").formatted(Formatting.YELLOW, Formatting.BOLD))
            .append(Text.literal("Box ").formatted(Formatting.GOLD, Formatting.BOLD))
            .append(Text.literal("» ").formatted(Formatting.DARK_GRAY))
            .append(Text.literal(message).formatted(Formatting.GRAY)),
        false);
  }

  public static List<ItemStack> currentKit(ServerPlayerEntity p) {
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
      save();
    }
    var kits = disk.getAsJsonObject("kits");
    var kit =
        kits.has(options.rules.name())
            ? Kits.decode(p, kits.getAsJsonArray(options.rules.name()))
            : Kits.defaults(p.getRegistryManager(), options.rules);
    if (options.rules == Options.Rules.NORMAL_SPAM && Kits.repairNormalKit(kit)) storeKit(p, kit);
    return kit;
  }

  public static void storeKit(ServerPlayerEntity p, List<ItemStack> kit) {
    if (!disk.has("kits")) disk.add("kits", new JsonObject());
    disk.getAsJsonObject("kits").add(options.rules.name(), Kits.encode(p, kit));
    save();
  }

  public static boolean allowTrainingDeath(
      net.minecraft.entity.LivingEntity entity,
      net.minecraft.entity.damage.DamageSource source,
      float amount) {
    if (session == null || (entity != session.owner && entity != session.bot)) return true;
    // Fabric asks BEFORE vanilla tries death protection, not after the totem.
    if (!source.isIn(net.minecraft.registry.tag.DamageTypeTags.BYPASSES_INVULNERABILITY))
      for (Hand hand : Hand.values())
        if (entity
            .getStackInHand(hand)
            .contains(net.minecraft.component.DataComponentTypes.DEATH_PROTECTION)) return true;
    entity.setHealth(1);
    session.finish = entity == session.bot ? "Voce venceu!" : "O bot venceu. Tente novamente!";
    return false;
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
        say(p, "Dificuldade: " + options.difficulty);
        save();
      }
      case "modo" -> {
        requireStopped();
        options.tank = !options.tank;
        Arena.updateModeLabel(p.getServerWorld(), options);
        save();
        say(p, "Modo: " + (options.tank ? "TANK (o bot so tanka)" : "DUEL (combate)"));
      }
      case "giro_nivel" -> {
        options.spin = Options.SpinLevel.values()[(options.spin.ordinal() + 1) % 4];
        save();
        Arena.updateSpinLabel(world(), options);
        say(p, "Giro: " + options.spin);
      }
      case "regras" -> {
        requireStopped();
        options.rules =
            options.rules == Options.Rules.NORMAL_SPAM
                ? Options.Rules.INSTA_KILL
                : Options.Rules.NORMAL_SPAM;
        Arena.updateRulesLabel(p.getServerWorld(), options);
        save();
        say(p, "Regras: " + options.rules);
      }
      case "tamanho" -> {
        requireStopped();
        options.size =
            options.size < 13
                ? 13
                : options.size < 17
                    ? 17
                    : options.size < 21
                        ? 21
                        : options.size < 25
                            ? 25
                            : options.size < 33 ? 33 : options.size < 41 ? 41 : 9;
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
        say(p, key + ": " + active);
      }
    }
  }

  public static ServerWorld world() {
    return server.getWorld(RegistryKey.of(RegistryKeys.WORLD, Identifier.of(options.dimension)));
  }

  public static void start(ServerPlayerEntity p) {
    KitEditor.closeFor(p);
    requireStopped();
    if (!options.built) throw new IllegalArgumentException("Use /box criar primeiro.");
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
    if (ServerPlayNetworking.canSend(s.owner, TrainingPayload.ID))
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
      say(s.owner, reason);
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
      options.size = MathHelper.clamp(options.size, 9, 41) | 1;
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
      if (!(p instanceof TrainingBot) && ServerPlayNetworking.canSend(p, CosmeticPayload.ID))
        ServerPlayNetworking.send(
            p,
            new CosmeticPayload(
                p.getUuid(), session != null ? session.bot.getUuid() : new UUID(0, 0), mask));
  }

  public static void sync() {
    if (session != null
        && !session.owner.isDisconnected()
        && ServerPlayNetworking.canSend(session.owner, TrainingPayload.ID))
      ServerPlayNetworking.send(
          session.owner,
          new TrainingPayload(session.owner.getUuid(), session.bot.getUuid(), options.webRocket));
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

  public static boolean ignoreWeb(Entity entity) {
    if (entity.getWorld().isClient()) return ClientTrainingState.ignore(entity);
    return session != null
        && options.webRocket
        && (entity == session.bot || entity == session.owner)
        && entity instanceof LivingEntity living
        && living.isGliding()
        && rockets.getOrDefault(entity.getUuid(), -1L) >= entity.getWorld().getTime();
  }
}
