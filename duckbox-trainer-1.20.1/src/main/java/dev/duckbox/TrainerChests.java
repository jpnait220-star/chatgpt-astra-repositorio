package dev.duckbox;

import net.minecraft.block.entity.ChestBlockEntity;
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
    stack.getOrCreateNbt().putInt(KEY, profile);
    stack.getOrCreateSubNbt("BlockEntityTag").putInt("duckbox_visual_role",profile);

    stack.setCustomName(profile == 0
            ? Text.literal("Cofre de suprimentos").formatted(Formatting.LIGHT_PURPLE)
            : Text.literal("Bau do kit • ").append(DuckBox.profileName(profile)));
    return stack;
  }

  public static int profile(ChestBlockEntity chest) {
    int synced = ChestRoleSync.clientRole(chest);
    if (synced >= 0) return synced;
    if(chest instanceof dev.duckbox.chests.DuckChestEntity c && c.profileRole>=0)return c.profileRole;
    return chest.getCachedState().getBlock() instanceof dev.duckbox.chests.DuckChestBlock block?block.baseRole:-1;
  }
  public static net.minecraft.nbt.NbtCompound visualData(ChestBlockEntity chest,net.minecraft.registry.DynamicRegistryManager registries,net.minecraft.nbt.NbtCompound original){var result=original.copy();result.putInt("duckbox_visual_role",profile(chest));return result;}

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
