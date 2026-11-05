package dev.duckbox.panels;

import net.minecraft.entity.player.*;
import net.minecraft.inventory.SimpleInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.screen.*;
import net.minecraft.screen.slot.*;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;

public final class PanelMenu extends GenericContainerScreenHandler {
  private PanelMenu(int id, PlayerInventory inv, SimpleInventory contents) {
    super(ScreenHandlerType.GENERIC_9X3, id, inv, contents, 3);
    for (int i = 0; i < 27; i++) {
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

  public static void open(ServerPlayerEntity p) {
    var contents = new SimpleInventory(27);
    for (int i = 0; i < MapPanels.NAMES.size(); i++)
      contents.setStack(i, new ItemStack(MapPanels.BLOCKS.get(MapPanels.NAMES.get(i))));
    p.openHandledScreen(
        new SimpleNamedScreenHandlerFactory(
            (id, inv, who) -> new PanelMenu(id, inv, contents), Text.literal("Blocos do mapa")));
  }

  public ItemStack quickMove(PlayerEntity p, int slot) {
    return ItemStack.EMPTY;
  }

  public void onSlotClick(int slot, int button, SlotActionType action, PlayerEntity p) {
    if (!(p instanceof ServerPlayerEntity player)
        || slot < 0
        || slot >= MapPanels.NAMES.size()
        || !canUse(p)) return;
    if (action == SlotActionType.PICKUP || action == SlotActionType.QUICK_MOVE)
      MapPanels.give(player, MapPanels.NAMES.get(slot));
  }
}
