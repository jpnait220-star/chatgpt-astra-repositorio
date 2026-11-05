package dev.duckbox;

import net.minecraft.entity.*;
import net.minecraft.entity.decoration.DisplayEntity;
import net.minecraft.nbt.*;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.hit.*;
import net.minecraft.util.math.*;

public final class FixedHolograms {
  private static String anchor(BlockPos pos, Direction face) {
    return "duckbox_holo_" + pos.asLong() + "_" + face.getName();
  }

  public static DisplayEntity.TextDisplayEntity put(
      ServerWorld world, BlockPos pos, Direction face, float yaw, String raw) {
    var tag = anchor(pos, face);
    DisplayEntity.TextDisplayEntity display = null;
    boolean existed = false;
    for (var old :
        world.getEntitiesByType(
            EntityType.TEXT_DISPLAY,
            new Box(pos).expand(2),
            e -> e.getCommandTags().contains(tag))) {
      display = old;
      existed = true;
      break;
    }
    if (display == null) {
      display = EntityType.TEXT_DISPLAY.create(world, SpawnReason.COMMAND);
      if (display == null) throw new IllegalStateException("Text display indisponivel.");
    }
    var data = display.writeNbt(new NbtCompound());
    data.putString(
        "text",
        Text.Serialization.toJsonString(
            RichNames.parse(raw.replace("\\n", "\n")), world.getRegistryManager()));
    data.putString("billboard", "fixed");
    data.putInt("line_width", 80);
    data.putInt("background", 0);
    data.putByte("text_opacity", (byte) -1);
    data.putBoolean("shadow", false);
    data.putBoolean("see_through", false);
    data.putInt("interpolation_duration", 0);
    data.putInt("teleport_duration", 0);
    data.putFloat("view_range", 2);
    var transform = new NbtCompound();
    var scale = new NbtList();
    for (int i = 0; i < 3; i++) scale.add(NbtFloat.of(.5f));
    transform.put("scale", scale);
    var translation = new NbtList();
    for (int i = 0; i < 3; i++) translation.add(NbtFloat.of(0));
    var rotation = new NbtList();
    for (int i = 0; i < 3; i++) rotation.add(NbtFloat.of(0));
    rotation.add(NbtFloat.of(1));
    transform.put("translation", translation);
    transform.put("left_rotation", rotation);
    transform.put("right_rotation", rotation.copy());
    data.put("transformation", transform);
    display.readNbt(data);
    double x = pos.getX() + .5 + face.getOffsetX() * .502,
        y = pos.getY() + .5 + face.getOffsetY() * .502,
        z = pos.getZ() + .5 + face.getOffsetZ() * .502;
    display.refreshPositionAndAngles(x, y, z, yaw, 0);
    display.addCommandTag("duckbox_holo");
    display.addCommandTag(tag);
    display.setNoGravity(true);
    if (!existed) world.spawnEntity(display);
    return display;
  }

  private record Edit(
      String text, java.util.UUID source, boolean moving, boolean deleting, int until) {}

  private static final java.util.Map<java.util.UUID, Edit> pending = new java.util.HashMap<>();

  public static void forget(java.util.UUID id) {
    pending.remove(id);
  }

  public static void clear() {
    pending.clear();
  }

  public static void cancel(ServerPlayerEntity p) {
    pending.remove(p.getUuid());
    DuckBox.setting(p, "Edicao de holograma cancelada.");
  }

  public static void command(ServerPlayerEntity p, String raw) {
    RichNames.parse(raw.replace("\\n", "\n"));
    pending.put(p.getUuid(), new Edit(raw, null, false, false, p.getServer().getTicks() + 1200));
    DuckBox.setting(p, "Clique com botao direito no bloco para fixar o texto.");
  }

  public static void moveCommand(ServerPlayerEntity p) {
    pending.put(p.getUuid(), new Edit(null, null, true, false, p.getServer().getTicks() + 1200));
    DuckBox.setting(p, "Clique no bloco do holograma; depois no bloco de destino.");
  }

  public static void remove(ServerPlayerEntity p) {
    pending.put(p.getUuid(), new Edit(null, null, false, true, p.getServer().getTicks() + 1200));
    DuckBox.setting(p, "Clique no bloco do holograma para remover.");
  }

  private static DisplayEntity.TextDisplayEntity find(
      ServerWorld world, BlockPos pos, Direction face) {
    String exact = anchor(pos, face), prefix = "duckbox_holo_" + pos.asLong() + "_";
    DisplayEntity.TextDisplayEntity fallback = null;
    for (var e :
        world.getEntitiesByType(
            EntityType.TEXT_DISPLAY,
            new Box(pos).expand(2),
            entity -> entity.getCommandTags().contains("duckbox_holo"))) {
      if (e.getCommandTags().contains(exact)) return e;
      if (e.getCommandTags().stream().anyMatch(tag -> tag.startsWith(prefix))) fallback = e;
    }
    return fallback;
  }

  public static boolean click(ServerPlayerEntity p, BlockHitResult hit) {
    var edit = pending.get(p.getUuid());
    if (edit == null) return false;
    if (p.getServer().getTicks() > edit.until()) {
      pending.remove(p.getUuid());
      return false;
    }
    var world = p.getServerWorld();
    var pos = hit.getBlockPos();
    var face = hit.getSide();
    var facing = face.getAxis().isHorizontal() ? face : p.getHorizontalFacing().getOpposite();
    if (edit.deleting()) {
      var old = find(world, pos, face);
      if (old != null) old.discard();
      pending.remove(p.getUuid());
      DuckBox.setting(p, old == null ? "Nenhum holograma nesse bloco." : "Holograma removido.");
      return true;
    }
    if (edit.moving()) {
      if (edit.source() == null) {
        var old = find(world, pos, face);
        if (old == null) {
          DuckBox.setting(p, "Esse bloco nao tem holograma. Clique no bloco correto.");
          return true;
        }
        pending.put(p.getUuid(), new Edit(null, old.getUuid(), true, false, edit.until()));
        DuckBox.setting(p, "Agora clique no bloco de destino.");
        return true;
      }
      var entity = world.getEntity(edit.source());
      if (!(entity instanceof DisplayEntity.TextDisplayEntity display)) {
        pending.remove(p.getUuid());
        DuckBox.setting(p, "Holograma nao encontrado nesta dimensao.");
        return true;
      }
      var previous = find(world, pos, face);
      if (previous != null && previous != display) previous.discard();
      display.getCommandTags().removeIf(tag -> tag.startsWith("duckbox_holo_"));
      display.addCommandTag(anchor(pos, face));
      display.refreshPositionAndAngles(
          pos.getX() + .5 + face.getOffsetX() * .502,
          pos.getY() + .5 + face.getOffsetY() * .502,
          pos.getZ() + .5 + face.getOffsetZ() * .502,
          facing.getPositiveHorizontalDegrees(),
          0);
      display.resetLerp();
      pending.remove(p.getUuid());
      DuckBox.setting(p, "Holograma movido e fixado.");
      return true;
    }
    put(world, pos, face, facing.getPositiveHorizontalDegrees(), edit.text());
    pending.remove(p.getUuid());
    DuckBox.setting(p, "Texto fixado no bloco.");
    return true;
  }

  public static void removeAt(ServerWorld world, BlockPos pos) {
    String prefix = "duckbox_holo_" + pos.asLong() + "_";
    for (var e :
        world.getEntitiesByType(
            EntityType.TEXT_DISPLAY,
            new Box(pos).expand(2),
            entity -> entity.getCommandTags().stream().anyMatch(tag -> tag.startsWith(prefix))))
      e.discard();
  }
}
