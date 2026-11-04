package dev.duckbox;

import java.util.*;
import net.minecraft.component.DataComponentTypes;
import net.minecraft.entity.player.*;
import net.minecraft.inventory.SimpleInventory;
import net.minecraft.item.*;
import net.minecraft.screen.*;
import net.minecraft.screen.slot.Slot;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;

public final class KitEditor extends GenericContainerScreenHandler {
  private static KitEditor active;
  private final ServerPlayerEntity owner;
  private final SimpleInventory contents;
  private boolean committed;

  public static int logicalSlot(int chestSlot) {
    if (chestSlot >= 0 && chestSlot < 27) return chestSlot + 9;
    if (chestSlot >= 27 && chestSlot < 36) return chestSlot - 27;
    return switch (chestSlot) {
      case 36 -> 39;
      case 37 -> 38;
      case 38 -> 37;
      case 39 -> 36;
      case 40 -> 40;
      default -> -1;
    };
  }

  private KitEditor(
      int syncId,
      PlayerInventory playerInventory,
      ServerPlayerEntity owner,
      SimpleInventory contents) {
    super(ScreenHandlerType.GENERIC_9X6, syncId, playerInventory, contents, 6);
    this.owner = owner;
    this.contents = contents;
    for (int i = 0; i < 54; i++)
      if (logicalSlot(i) < 0) {
        Slot old = slots.get(i);
        Slot locked =
            new Slot(contents, i, old.x, old.y) {
              public boolean canInsert(ItemStack stack) {
                return false;
              }

              public boolean canTakeItems(PlayerEntity p) {
                return false;
              }
            };
        locked.id = old.id;
        slots.set(i, locked);
      }
  }

  public static boolean editing() {
    return active != null;
  }

  public static void closeFor(ServerPlayerEntity p) {
    if (active != null && active.owner == p) p.closeHandledScreen();
  }

  public static void flush() {
    if (active != null) active.owner.closeHandledScreen();
  }

  public static void reset() {
    active = null;
  }

  public static void open(ServerPlayerEntity p) {
    DuckBox.requireStopped();
    SimpleInventory contents = new SimpleInventory(54);
    List<ItemStack> kit = DuckBox.currentKit(p);
    String[] labels = {
      "Cabeca acima",
      "Elytra acima",
      "Calcas acima",
      "Botas acima",
      "Offhand acima",
      "Salva ao fechar",
      "Mesma copia para os 2",
      "3 linhas: inventario",
      "4a linha: hotbar"
    };
    for (int i = 0; i < 54; i++) {
      int logical = logicalSlot(i);
      if (logical >= 0) contents.setStack(i, kit.get(logical).copy());
      else {
        ItemStack note = new ItemStack(Items.GRAY_STAINED_GLASS_PANE);
        note.set(
            DataComponentTypes.CUSTOM_NAME, Text.literal(i >= 45 ? labels[i - 45] : "Reservado"));
        contents.setStack(i, note);
      }
    }
    p.openHandledScreen(
        new SimpleNamedScreenHandlerFactory(
            (id, inventory, who) -> {
              active = new KitEditor(id, inventory, p, contents);
              return active;
            },
            Text.literal("Kit dos dois: " + DuckBox.options.rules)));
  }

  @Override
  public boolean canUse(PlayerEntity p) {
    return p == owner
        && DuckBox.session == null
        && p.getWorld() == DuckBox.world()
        && p.squaredDistanceTo(
                net.minecraft.util.math.Vec3d.ofCenter(Arena.kitChest(DuckBox.options)))
            < 100;
  }

  private void commit() {
    if (committed) return;
    List<ItemStack> kit = new ArrayList<>(Collections.nCopies(41, ItemStack.EMPTY));
    for (int i = 0; i < 54; i++) {
      int logical = logicalSlot(i);
      if (logical >= 0) kit.set(logical, contents.getStack(i).copy());
    }
    DuckBox.storeKit(owner, kit);
    committed = true;
    if (active == this) active = null;
  }

  @Override
  public void onClosed(PlayerEntity player) {
    super.onClosed(player);
    commit();
    DuckBox.say(owner, "Kit salvo: os dois receberao esse inventario e equipamento.");
  }
}
