package dev.duckbox;

import net.minecraft.block.entity.ChestBlockEntity;
import net.minecraft.entity.player.*;
import net.minecraft.item.ItemStack;
import net.minecraft.screen.*;
import net.minecraft.screen.slot.*;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;

/** Supply templates never leave the real chest; players receive independent copies. */
public final class StockChestMenu extends GenericContainerScreenHandler {
  private final ChestBlockEntity chest;

  public static void open(ServerPlayerEntity p, ChestBlockEntity chest) {
    p.openHandledScreen(
        new SimpleNamedScreenHandlerFactory(
            (id, inventory, who) -> new StockChestMenu(id, inventory, chest),
            Text.literal("Cofre de suprimentos")));
  }

  private StockChestMenu(int id, PlayerInventory inventory, ChestBlockEntity chest) {
    super(ScreenHandlerType.GENERIC_9X3, id, inventory, chest, 3);
    this.chest = chest;
    for (int i = 0; i < 27; i++) {
      Slot old = slots.get(i);
      var locked =
          new Slot(chest, i, old.x, old.y) {
            @Override
            public boolean canTakeItems(PlayerEntity p) {
              return false;
            }

            @Override
            public boolean canInsert(ItemStack stack) {
              return false;
            }
          };
      locked.id = old.id;
      slots.set(i, locked);
    }
  }

  @Override
  public ItemStack quickMove(PlayerEntity p, int slot) {
    if (slot < 0 || slot >= 27 || !canUse(p)) return ItemStack.EMPTY;
    var copy = chest.getStack(slot).copy();
    if (copy.isEmpty()) return ItemStack.EMPTY;
    var original = copy.copy();
    if (!insertItem(copy, 27, slots.size(), true)) return ItemStack.EMPTY;
    sendContentUpdates();
    return original;
  }

  @Override
  public void onSlotClick(int slot, int button, SlotActionType action, PlayerEntity p) {
    if (!canUse(p)) return;
    if (slot < 0 || slot >= 27) {
      super.onSlotClick(slot, button, action, p);
      return;
    }
    var template = chest.getStack(slot);
    if (template.isEmpty()) return;
    if (action == SlotActionType.QUICK_MOVE) {
      quickMove(p, slot);
      return;
    }
    if (action == SlotActionType.PICKUP || (action == SlotActionType.CLONE && p.isCreative())) {
      var cursor = getCursorStack();
      int amount = button == 1 ? 1 : template.getCount();
      if (cursor.isEmpty()) {
        var copy = template.copy();
        copy.setCount(amount);
        setCursorStack(copy);
      } else if (ItemStack.areItemsAndComponentsEqual(cursor, template))
        cursor.increment(Math.min(amount, cursor.getMaxCount() - cursor.getCount()));
      sendContentUpdates();
    }
  }
}
