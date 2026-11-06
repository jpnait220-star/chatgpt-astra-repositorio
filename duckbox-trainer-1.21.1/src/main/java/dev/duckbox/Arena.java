package dev.duckbox;

import java.util.*;
import net.minecraft.block.*;
import net.minecraft.block.entity.SignBlockEntity;
import net.minecraft.block.enums.*;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.math.*;

public final class Arena {
  public record Edit(BlockPos pos, BlockState state) {}

  public static final Map<BlockPos, String> controls = new HashMap<>();
  public static final ArrayDeque<Edit> pending = new ArrayDeque<>();
  private static ServerWorld buildingWorld;
  private static Options options;
  public static final int HEIGHT = 8;
  private static final String[] KEYS = {
    "iniciar",
    "parar",
    "dificuldade",
    "modo",
    "giro",
    "retotem",
    "gap",
    "teia",
    "wtap",
    "strafe",
    "foguete_teia",
    "tamanho",
    "giro_nivel",
    "regras",
    "cps"
  };

  public static void reset() {
    pending.clear();
    controls.clear();
    buildingWorld = null;
    options = null;
  }

  public static boolean building() {
    return !pending.isEmpty();
  }

  public static boolean hasGeneratedShell(ServerWorld world, Options o) {
    if (!world.getBlockState(new BlockPos(o.x, o.y, o.z)).isOf(Blocks.YELLOW_TERRACOTTA)
        || !world.getBlockState(new BlockPos(o.x, o.y + HEIGHT, o.z)).isOf(Blocks.GLASS)) return false;
    for (int size : new int[] {9, 13, 17}) {
      int h = size / 2;
      boolean corners = true;
      for (int x : new int[] {-h, h}) for (int z : new int[] {-h, h})
        corners &= world.getBlockState(new BlockPos(o.x + x, o.y + 1, o.z + z)).isOf(Blocks.CHISELED_POLISHED_BLACKSTONE);
      if (corners) return true;
    }
    return false;
  }

  public static void create(ServerPlayerEntity player, Options o) {
    DuckBox.requireStopped();
    if (building()) throw new IllegalArgumentException("Aguarde a arena terminar.");
    if (o.initialized
        && !player.getServerWorld().getRegistryKey().getValue().toString().equals(o.dimension))
      throw new IllegalArgumentException("Volte para a dimensao da arena.");
    if (!o.initialized) {
      o.initialized = true;
      o.x = Options.ARENA_X;
      o.y = Options.ARENA_Y;
      o.z = Options.ARENA_Z;
      o.dimension = player.getServerWorld().getRegistryKey().getValue().toString();
    }
    o.customMap = false;
    o.arenaOnly = true;
    o.size = Options.allowedSize(o.size);
    buildingWorld = player.getServerWorld();
    options = o;
    o.built = false;
    DuckBox.save();
    controls.clear();
    int h = o.size / 2;
    // Only the dedicated arena volume is edited. The lobby stays outside the largest box.
    for (int x = -8; x <= 8; x++)
      for (int z = -8; z <= 8; z++)
        for (int y = 0; y <= 10; y++) {
          boolean inside = Math.abs(x) <= h && Math.abs(z) <= h;
          BlockState block = Blocks.AIR.getDefaultState();
          boolean edge = Math.abs(x) == h || Math.abs(z) == h;
          boolean corner = Math.abs(x) == h && Math.abs(z) == h;
          if (inside && y <= HEIGHT) {
            if (y == 0)
              block =
                  (edge
                          ? (o.rules == Options.Rules.INSTA_KILL
                              ? Blocks.RED_CONCRETE
                              : Blocks.BLUE_CONCRETE)
                          : (Math.abs(x) <= 1 || Math.abs(z) <= 1)
                              ? Blocks.YELLOW_TERRACOTTA
                              : (Math.floorMod(x + z, 2) == 0
                                  ? Blocks.SMOOTH_QUARTZ
                                  : Blocks.QUARTZ_BRICKS))
                      .getDefaultState();
            else if (corner)
              block =
                  (y == 3 || y == 6 ? Blocks.SEA_LANTERN : Blocks.CHISELED_POLISHED_BLACKSTONE)
                      .getDefaultState();
            else if (edge)
              block =
                  (y == HEIGHT
                          ? Blocks.POLISHED_BLACKSTONE_BRICKS
                          : (o.rules == Options.Rules.INSTA_KILL
                              ? Blocks.RED_STAINED_GLASS
                              : Blocks.BLUE_STAINED_GLASS))
                      .getDefaultState();
            else if (y == HEIGHT) block = Blocks.GLASS.getDefaultState();
          }
          pending.add(new Edit(new BlockPos(o.x + x, o.y + y, o.z + z), block));
        }
    player.teleport(buildingWorld, o.x, o.y + HEIGHT + 1, o.z, Set.of(), 180, 0);
    SpawnControl.later(player);
    DuckBox.say(player, "Montando arena em lotes. Aguarde alguns segundos.");
  }

  public static void tick() {
    for (int i = 0; i < 1200 && !pending.isEmpty(); i++) {
      Edit e = pending.removeFirst();
      if (!buildingWorld.getBlockState(e.pos).equals(e.state))
        buildingWorld.setBlockState(e.pos, e.state, 3);
    }
    if (pending.isEmpty() && buildingWorld != null) {
      controls.clear();
      options.built = true;
      DuckBox.save();
      buildingWorld = null;
      options = null;
    }
  }

  private static void panel() {
    Options o = options;
    // Small duck statue, light posts and kit station, with no extra ticking entities.
    for (int x = -2; x <= 2; x++)
      for (int z = -1; z <= 1; z++)
        for (int y = 1; y <= 4; y++)
          buildingWorld.setBlockState(
              new BlockPos(o.x - 27 + x, o.y + y, o.z - 13 + z),
              Blocks.YELLOW_CONCRETE.getDefaultState(),
              3);
    for (int x = -2; x <= 2; x++)
      buildingWorld.setBlockState(
          new BlockPos(o.x - 27 + x, o.y + 2, o.z - 11),
          Blocks.ORANGE_CONCRETE.getDefaultState(),
          3);
    for (int x : new int[] {-1, 1})
      buildingWorld.setBlockState(
          new BlockPos(o.x - 27 + x, o.y + 4, o.z - 12),
          Blocks.BLACK_CONCRETE.getDefaultState(),
          3);
    for (int x : new int[] {-33, -21})
      for (int z : new int[] {-15, 10}) {
        for (int y = 1; y <= 3; y++)
          buildingWorld.setBlockState(
              new BlockPos(o.x + x, o.y + y, o.z + z),
              Blocks.POLISHED_BLACKSTONE_WALL.getDefaultState(),
              3);
        buildingWorld.setBlockState(
            new BlockPos(o.x + x, o.y + 4, o.z + z), Blocks.SEA_LANTERN.getDefaultState(), 3);
      }
    BlockPos chest = kitChest(o);
    buildingWorld.setBlockState(
        chest, Blocks.CHEST.getDefaultState().with(ChestBlock.FACING, Direction.SOUTH), 3);
    sign(
        buildingWorld,
        chest.south(),
        "KIT DOS DOIS",
        "Abra o bau",
        "Edite e feche",
        "Salva ao fechar");
    sign(
        buildingWorld,
        new BlockPos(o.x - 29, o.y + 1, o.z + 10),
        "DUCK BOX",
        "Treino PvP",
        o.size + " x " + o.size,
        "Escolha e inicie");
    for (int i = 0; i < KEYS.length; i++) {
      int col = i % 3, row = i / 3;
      BlockPos p = new BlockPos(o.x - 31 + col * 4, o.y + 1, o.z - 8 + row * 4);
      boolean toggle = i >= 4 && i <= 10;
      BlockState state =
          toggle
              ? Blocks.LEVER
                  .getDefaultState()
                  .with(LeverBlock.FACE, BlockFace.FLOOR)
                  .with(LeverBlock.FACING, Direction.SOUTH)
                  .with(LeverBlock.POWERED, enabled(KEYS[i], o))
              : Blocks.STONE_BUTTON.getDefaultState().with(ButtonBlock.FACE, BlockFace.FLOOR);
      buildingWorld.setBlockState(p, state, 3);
      controls.put(p, KEYS[i]);
      BlockPos sign = p.south();
      buildingWorld.setBlockState(sign, Blocks.OAK_SIGN.getDefaultState(), 3);
      if (buildingWorld.getBlockEntity(sign) instanceof SignBlockEntity s) {
        s.setText(
            s.getFrontText()
                .withMessage(0, Text.literal("DuckBox"))
                .withMessage(1, Text.literal(KEYS[i]))
                .withMessage(2, Text.literal(toggle ? "Ligar / desligar" : "Clique no controle")),
            true);
        s.markDirty();
      }
    }
    updateModeLabel(buildingWorld, o);
    updateRulesLabel(buildingWorld, o);
    updateSpinLabel(buildingWorld, o);
    updateCpsLabel(buildingWorld, o);
  }

  public static void updateCpsLabel(ServerWorld w, Options o) {
    if (o.arenaOnly
        || w == null
        || o.customMap
        || !w.getRegistryKey().getValue().toString().equals(o.dimension)
        || (!o.built && w != buildingWorld)) return;
    sign(
        w,
        new BlockPos(o.x - 23, o.y + 1, o.z + 9),
        "CPS DO BOT",
        Integer.toString(o.cps),
        "10/13/15/20",
        "Clique no botao");
  }

  public static void ensureCpsControl(ServerWorld w, Options o) {
    if (o.arenaOnly
        || w == null
        || o.customMap
        || !o.built
        || !w.getRegistryKey().getValue().toString().equals(o.dimension)) return;
    BlockPos button = new BlockPos(o.x - 23, o.y + 1, o.z + 8), label = button.south();
    if (w.getBlockState(button).isAir()
        && w.getBlockState(label).isAir()
        && w.getBlockState(button.down()).isSolidBlock(w, button.down())) {
      w.setBlockState(
          button, Blocks.STONE_BUTTON.getDefaultState().with(ButtonBlock.FACE, BlockFace.FLOOR), 3);
      controls.put(button, "cps");
      updateCpsLabel(w, o);
    }
  }

  public static void updateSpinLabel(ServerWorld w, Options o) {
    if (o.arenaOnly
        || w == null
        || !w.getRegistryKey().getValue().toString().equals(o.dimension)
        || (!o.built && w != buildingWorld)) return;
    sign(
        w,
        new BlockPos(o.x - 31, o.y + 1, o.z + 9),
        "NIVEL DO GIRO",
        o.spin.name(),
        "Clique no botao",
        "Mira independente");
  }

  public static void updateRulesLabel(ServerWorld w, Options o) {
    if (o.arenaOnly
        || w == null
        || !w.getRegistryKey().getValue().toString().equals(o.dimension)
        || (!o.built && w != buildingWorld)) return;
    sign(
        w,
        new BlockPos(o.x - 27, o.y + 1, o.z + 9),
        "REGRAS",
        o.rules.toString(),
        "Clique no botao",
        "Kit por modo");
  }

  public static void updateModeLabel(ServerWorld w, Options o) {
    if (o.arenaOnly) return;
    sign(
        w,
        new BlockPos(o.x - 31, o.y + 1, o.z - 3),
        "MODO DE TREINO",
        o.tank ? "TANK" : "DUEL",
        "Clique no botao",
        "Tank nao ataca");
  }

  private static void sign(ServerWorld w, BlockPos pos, String... lines) {
    if (DuckBox.options != null && (DuckBox.options.customMap || DuckBox.options.arenaOnly)) return;
    w.setBlockState(pos, Blocks.OAK_SIGN.getDefaultState(), 3);
    if (w.getBlockEntity(pos) instanceof SignBlockEntity sign) {
      var text = sign.getFrontText();
      for (int i = 0; i < Math.min(4, lines.length); i++)
        text = text.withMessage(i, Text.literal(lines[i]));
      sign.setText(text, true);
      sign.markDirty();
    }
  }

  public static BlockPos kitChest(Options o) {
    return new BlockPos(o.x - 22, o.y + 1, o.z + 8);
  }

  public static boolean isKitChest(BlockPos pos, ServerWorld w, Options o) {
    return !o.arenaOnly
        && o.built
        && !o.customMap
        && w.getRegistryKey().getValue().toString().equals(o.dimension)
        && pos.equals(kitChest(o));
  }

  private static boolean enabled(String key, Options o) {
    return switch (key) {
      case "tank" -> o.tank;
      case "giro" -> o.giro;
      case "gap" -> o.gap;
      case "teia" -> o.teia;
      case "retotem" -> o.retotem;
      case "wtap" -> o.wtap;
      case "strafe" -> o.strafe;
      case "foguete_teia" -> o.webRocket;
      default -> false;
    };
  }

  public static String control(BlockPos p, ServerWorld w, Options o) {
    if (o.arenaOnly
        || o.customMap
        || !o.built
        || !w.getRegistryKey().getValue().toString().equals(o.dimension)) return null;
    for (int i = 0; i < KEYS.length; i++)
      if (p.equals(new BlockPos(o.x - 31 + i % 3 * 4, o.y + 1, o.z - 8 + i / 3 * 4))) {
        controls.put(p, KEYS[i]);
        return KEYS[i];
      }
    return null;
  }

  public static void applyTheme(ServerWorld w, Options o) {
    if (w == null || !o.built || !w.getRegistryKey().getValue().toString().equals(o.dimension))
      return;
    boolean red = o.rules == Options.Rules.INSTA_KILL;
    int h = o.size / 2;
    for (int x = -h; x <= h; x++)
      for (int z = -h; z <= h; z++) {
        if (Math.abs(x) != h && Math.abs(z) != h) continue;
        for (int y = 0; y <= HEIGHT; y++) {
          var pos = new BlockPos(o.x + x, o.y + y, o.z + z);
          var state = w.getBlockState(pos);
          if (state.isOf(Blocks.LIGHT_BLUE_STAINED_GLASS)
              || state.isOf(Blocks.BLUE_STAINED_GLASS)
              || state.isOf(Blocks.RED_STAINED_GLASS))
            w.setBlockState(
                pos,
                (red ? Blocks.RED_STAINED_GLASS : Blocks.BLUE_STAINED_GLASS).getDefaultState(),
                3);
          else if (y == 0
              && (state.isOf(Blocks.BLUE_CONCRETE)
                  || state.isOf(Blocks.RED_CONCRETE)
                  || state.isOf(Blocks.POLISHED_BLACKSTONE_BRICKS)))
            w.setBlockState(
                pos, (red ? Blocks.RED_CONCRETE : Blocks.BLUE_CONCRETE).getDefaultState(), 3);
        }
      }
  }

  public static void clearOldPanel(ServerWorld w, Options o) {
    if (!w.getRegistryKey().getValue().toString().equals(o.dimension))
      throw new IllegalArgumentException("Volte para a dimensao da arena.");
    for (int x = -34; x <= -20; x++)
      for (int z = -16; z <= 12; z++)
        for (int y = 0; y <= 7; y++) {
          BlockPos pos = new BlockPos(o.x + x, o.y + y, o.z + z);
          var block = w.getBlockState(pos).getBlock();
          if (Set.of(
                  Blocks.POLISHED_BLACKSTONE_BRICKS,
                  Blocks.SMOOTH_QUARTZ,
                  Blocks.QUARTZ_BRICKS,
                  Blocks.YELLOW_CONCRETE,
                  Blocks.ORANGE_CONCRETE,
                  Blocks.BLACK_CONCRETE,
                  Blocks.POLISHED_BLACKSTONE_WALL,
                  Blocks.SEA_LANTERN,
                  Blocks.OAK_SIGN,
                  Blocks.LEVER,
                  Blocks.STONE_BUTTON,
                  Blocks.CHEST)
              .contains(block)) w.setBlockState(pos, Blocks.AIR.getDefaultState(), 3);
        }
    controls.clear();
    o.arenaOnly = true;
    DuckBox.save();
  }

  public static void clearWebs(ServerWorld w, Options o) {
    int h = o.size / 2;
    for (int x = -h + 1; x < h; x++)
      for (int z = -h + 1; z < h; z++)
        for (int y = 1; y < HEIGHT; y++) {
          BlockPos p = new BlockPos(o.x + x, o.y + y, o.z + z);
          if (w.getBlockState(p).isOf(Blocks.COBWEB)
              || w.getBlockState(p).isIn(net.minecraft.registry.tag.BlockTags.WOOL))
            w.setBlockState(p, Blocks.AIR.getDefaultState(), 3);
        }
  }
}
