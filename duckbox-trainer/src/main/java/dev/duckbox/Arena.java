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
  private static final String[] KEYS = {
    "iniciar",
    "parar",
    "dificuldade",
    "tank",
    "giro",
    "retotem",
    "gap",
    "teia",
    "wtap",
    "strafe",
    "foguete_teia",
    "tamanho"
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

  public static void create(ServerPlayerEntity player, Options o) {
    DuckBox.requireStopped();
    if (building()) throw new IllegalArgumentException("Aguarde a arena terminar.");
    if (o.initialized
        && !player.getServerWorld().getRegistryKey().getValue().toString().equals(o.dimension))
      throw new IllegalArgumentException("Volte para a dimensao da arena.");
    if (!o.initialized) {
      o.initialized = true;
      o.x = player.getBlockX();
      o.y = MathHelper.clamp(player.getBlockY() - 1, 10, 240);
      o.z = player.getBlockZ() + 32;
      o.dimension = player.getServerWorld().getRegistryKey().getValue().toString();
    }
    buildingWorld = player.getServerWorld();
    options = o;
    o.built = false;
    DuckBox.save();
    controls.clear();
    int h = o.size / 2;
    // Only the dedicated arena volume is edited. The lobby stays outside the largest box.
    for (int x = -20; x <= 20; x++)
      for (int z = -20; z <= 20; z++)
        for (int y = 0; y <= 10; y++) {
          boolean inside = Math.abs(x) <= h && Math.abs(z) <= h;
          BlockState block = Blocks.AIR.getDefaultState();
          if (inside && (y == 0 || y == 10 || Math.abs(x) == h || Math.abs(z) == h))
            block = (y == 0 ? Blocks.SMOOTH_STONE : Blocks.GLASS).getDefaultState();
          pending.add(new Edit(new BlockPos(o.x + x, o.y + y, o.z + z), block));
        }
    for (int x = -33; x <= -21; x++)
      for (int z = -10; z <= 10; z++)
        for (int y = 0; y <= 3; y++)
          pending.add(
              new Edit(
                  new BlockPos(o.x + x, o.y + y, o.z + z),
                  y == 0 ? Blocks.SMOOTH_QUARTZ.getDefaultState() : Blocks.AIR.getDefaultState()));
    player.teleport(buildingWorld, o.x - 27.5, o.y + 1, o.z + 9.5, Set.of(), 180, 0, false);
    DuckBox.say(player, "Montando arena em lotes. Aguarde alguns segundos.");
  }

  public static void tick() {
    for (int i = 0; i < 1200 && !pending.isEmpty(); i++) {
      Edit e = pending.removeFirst();
      if (!buildingWorld.getBlockState(e.pos).equals(e.state))
        buildingWorld.setBlockState(e.pos, e.state, 3);
    }
    if (pending.isEmpty() && buildingWorld != null) {
      panel();
      options.built = true;
      DuckBox.save();
      buildingWorld = null;
      options = null;
    }
  }

  private static void panel() {
    Options o = options;
    for (int i = 0; i < KEYS.length; i++) {
      int col = i % 3, row = i / 3;
      BlockPos p = new BlockPos(o.x - 31 + col * 4, o.y + 1, o.z - 8 + row * 4);
      boolean toggle = i >= 3 && i <= 10;
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
    if (!o.built || !w.getRegistryKey().getValue().toString().equals(o.dimension)) return null;
    for (int i = 0; i < KEYS.length; i++)
      if (p.equals(new BlockPos(o.x - 31 + i % 3 * 4, o.y + 1, o.z - 8 + i / 3 * 4))) {
        controls.put(p, KEYS[i]);
        return KEYS[i];
      }
    return null;
  }

  public static void clearWebs(ServerWorld w, Options o) {
    int h = o.size / 2;
    for (int x = -h + 1; x < h; x++)
      for (int z = -h + 1; z < h; z++)
        for (int y = 1; y < 10; y++) {
          BlockPos p = new BlockPos(o.x + x, o.y + y, o.z + z);
          if (w.getBlockState(p).isOf(Blocks.COBWEB))
            w.setBlockState(p, Blocks.AIR.getDefaultState(), 3);
        }
  }
}
