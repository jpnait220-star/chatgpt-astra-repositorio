package dev.duckbox;

import net.minecraft.block.entity.ChestBlockEntity;
import net.minecraft.component.DataComponentTypes;
import net.minecraft.component.type.NbtComponent;
import net.minecraft.item.*;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.screen.*;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.*;
import net.minecraft.util.hit.BlockHitResult;

/** Vanilla chest component markers survive world saves; no new block registry is needed. */
public final class TrainerChests {
  private static final String KEY = "duckbox_chest_profile";

  public static ItemStack item(int profile) {
    if (profile < 0 || profile > 4)
      throw new IllegalArgumentException("Bau: stock ou profile1..4.");
    var stack =
        new ItemStack(
            profile == 0
                ? dev.duckbox.chests.MapChests.STOCK
                : dev.duckbox.chests.MapChests.PROFILE);
    var data = new NbtCompound();
    data.putInt(KEY, profile);
    stack.set(DataComponentTypes.CUSTOM_DATA, NbtComponent.of(data));

    stack.set(
        DataComponentTypes.CUSTOM_NAME,
        profile == 0
            ? Text.literal("Cofre de suprimentos").formatted(Formatting.LIGHT_PURPLE)
            : Text.literal("Bau do kit • ").append(DuckBox.profileName(profile)));
    return stack;
  }

  public static int profile(ChestBlockEntity chest) {
    int synced = ChestRoleSync.clientRole(chest);
    if (synced >= 0) return synced;
    var data = chest.getComponents().get(DataComponentTypes.CUSTOM_DATA);
    if (data == null || !data.contains(KEY))
      return chest.getCachedState().getBlock() instanceof dev.duckbox.chests.DuckChestBlock block
          ? block.baseRole
          : -1;
    int id = data.copyNbt().getInt(KEY);
    return id >= 0 && id <= 4 ? id : -1;
  }

  public static net.minecraft.nbt.NbtCompound visualData(
      ChestBlockEntity chest,
      net.minecraft.registry.RegistryWrapper.WrapperLookup registries,
      net.minecraft.nbt.NbtCompound base) {
    var result = base.copy();
    if (profile(chest) < 0) return result;
    var roleData = new NbtCompound();
    roleData.putInt(KEY, profile(chest));
    var components =
        net.minecraft.component.ComponentMap.builder()
            .add(DataComponentTypes.CUSTOM_DATA, NbtComponent.of(roleData))
            .build();
    net.minecraft.component.ComponentMap.CODEC
        .encodeStart(registries.getOps(net.minecraft.nbt.NbtOps.INSTANCE), components)
        .result()
        .ifPresent(value -> result.put("components", value));
    result.putInt("duckbox_visual_role", profile(chest));
    return result;
  }

  public static void give(ServerPlayerEntity p, int profile) {
    p.getInventory().offerOrDrop(item(profile));
    DuckBox.setting(
        p,
        profile == 0
            ? "Cofre entregue. Shift+clique para editar estoque."
            : "Bau do perfil " + profile + " entregue.");
  }

  public static ActionResult open(
      net.minecraft.entity.player.PlayerEntity who,
      ServerWorld world,
      Hand hand,
      BlockHitResult hit) {
    if (!(who instanceof ServerPlayerEntity p)
        || hand != Hand.MAIN_HAND
        || !(world.getBlockEntity(hit.getBlockPos()) instanceof ChestBlockEntity chest))
      return ActionResult.PASS;
    int profile = profile(chest);
    if (profile < 0) return ActionResult.PASS;
    if (profile > 0) KitEditor.open(p, profile);
    else if (p.isSneaking() && p.hasPermissionLevel(2))
      p.openHandledScreen(
          new SimpleNamedScreenHandlerFactory(
              (id, inventory, player) ->
                  GenericContainerScreenHandler.createGeneric9x3(id, inventory, chest),
              Text.literal("Editar estoque do cofre")));
    else StockChestMenu.open(p, chest);
    return ActionResult.SUCCESS;
  }
}
