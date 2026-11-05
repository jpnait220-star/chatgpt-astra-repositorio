package dev.duckbox;

import net.minecraft.component.DataComponentTypes;
import net.minecraft.entity.player.*;
import net.minecraft.inventory.SimpleInventory;
import net.minecraft.item.*;
import net.minecraft.screen.*;
import net.minecraft.screen.slot.*;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;

/** Vanilla inventory menu: no custom client screen and no transferable display items. */
public final class ConfigMenu extends GenericContainerScreenHandler {
  private static final String[] KEYS = {
    "iniciar",
    "parar",
    "dificuldade",
    "modo",
    "regras",
    "cps",
    "giro_nivel",
    "tamanho",
    "kit",
    "retotem",
    "gap",
    "teia",
    "wtap",
    "strafe",
    "giro",
    "foguete_teia",
    "blood",
    "money",
    "oculos",
    "sapo",
    "profile",
    "nao_correr_retotem",
    "teia_pe"
  };
  private static final Item[] ICONS = {
    Items.LIME_DYE,
    Items.RED_DYE,
    Items.DIAMOND_SWORD,
    Items.SHIELD,
    Items.GOLDEN_SWORD,
    Items.CLOCK,
    Items.FIREWORK_ROCKET,
    Items.BRICKS,
    Items.CHEST,
    Items.TOTEM_OF_UNDYING,
    Items.ENCHANTED_GOLDEN_APPLE,
    Items.COBWEB,
    Items.FEATHER,
    Items.LEATHER_BOOTS,
    Items.ELYTRA,
    Items.FIREWORK_ROCKET,
    Items.REDSTONE,
    Items.EMERALD,
    Items.SPYGLASS,
    Items.LILY_PAD,
    Items.WRITABLE_BOOK,
    Items.TOTEM_OF_UNDYING,
    Items.COBWEB
  };
  private static final String[] LABELS = {
    "Iniciar treino",
    "Parar treino",
    "Dificuldade",
    "Treino",
    "Regras",
    "CPS do bot",
    "Nivel do giro",
    "Tamanho",
    "Editar kit dos dois",
    "Retotem",
    "Gap",
    "Teia",
    "W-tap",
    "Strafe",
    "Giro",
    "Foguete na teia",
    "Punho Blood",
    "Aura Money",
    "Oculos gamer",
    "Chapeu de sapo",
    "Perfil do kit",
    "Nao correr no retotem",
    "Teia no pe"
  };
  private final ServerPlayerEntity owner;
  private final SimpleInventory contents;
  private final net.minecraft.world.World openingWorld;
  private final net.minecraft.util.math.Vec3d openingPosition;

  private ConfigMenu(
      int id, PlayerInventory inventory, ServerPlayerEntity p, SimpleInventory contents) {
    super(ScreenHandlerType.GENERIC_9X3, id, inventory, contents, 3);
    owner = p;
    this.contents = contents;
    openingWorld = p.getWorld();
    openingPosition = p.getPos();
    for (int i = 0; i < 27; i++) {
      Slot old = slots.get(i);
      Slot locked =
          new Slot(contents, i, old.x, old.y) {
            @Override
            public boolean canInsert(ItemStack stack) {
              return false;
            }

            @Override
            public boolean canTakeItems(PlayerEntity who) {
              return false;
            }
          };
      locked.id = old.id;
      slots.set(i, locked);
    }
    refresh();
  }

  public static void open(ServerPlayerEntity p) {
    p.openHandledScreen(
        new SimpleNamedScreenHandlerFactory(
            (id, inventory, who) -> new ConfigMenu(id, inventory, p, new SimpleInventory(27)),
            Text.literal("Configurar DuckBox").formatted(Formatting.GOLD)));
  }

  private void refresh() {
    Options o = DuckBox.options;
    String[] values = {
      "",
      "",
      o.difficulty.toString(),
      o.tank ? "Tank" : "Duel",
      o.rules.toString(),
      o.cps + "",
      o.spin.toString(),
      o.size + "x" + o.size,
      "",
      on(o.retotem),
      on(o.gap),
      on(o.teia),
      on(o.wtap),
      on(o.strafe),
      on(o.giro),
      on(o.webRocket),
      on(o.blood),
      on(o.money),
      on(o.glasses),
      on(o.frog),
      Integer.toString(o.profile),
      on(o.noRetreatRetotem),
      on(o.footWeb)
    };
    for (int i = 0; i < 27; i++) {
      var stack = new ItemStack(i < KEYS.length ? ICONS[i] : Items.GRAY_STAINED_GLASS_PANE);
      stack.set(
          DataComponentTypes.CUSTOM_NAME,
          Text.literal(
                  i < KEYS.length
                      ? LABELS[i] + (values[i].isEmpty() ? "" : " » " + values[i])
                      : " ")
              .formatted(
                  (i >= 9 && i < 20) || i >= 21 && i < KEYS.length
                      ? values[i].equals("Ligado") ? Formatting.GREEN : Formatting.RED
                      : Formatting.YELLOW));
      contents.setStack(i, stack);
    }
    contents.markDirty();
    sendContentUpdates();
  }

  private static String on(boolean value) {
    return value ? "Ligado" : "Desligado";
  }

  @Override
  public boolean canUse(PlayerEntity p) {
    return p == owner
        && p.getWorld() == openingWorld
        && p.getPos().squaredDistanceTo(openingPosition) < 100;
  }

  @Override
  public ItemStack quickMove(PlayerEntity p, int index) {
    return ItemStack.EMPTY;
  }

  @Override
  public void onSlotClick(int index, int button, SlotActionType action, PlayerEntity p) {
    if (p != owner
        || !canUse(p)
        || index < 0
        || index >= KEYS.length
        || action != SlotActionType.PICKUP) return;
    String key = KEYS[index];
    try {
      if (key.equals("kit")) {
        owner.closeHandledScreen();
        KitEditor.open(owner);
        return;
      }
      if (key.equals("iniciar") || key.equals("parar")) owner.closeHandledScreen();
      if (index >= 16 && index < 20) {
        switch (key) {
          case "blood" -> DuckBox.options.blood = !DuckBox.options.blood;
          case "money" -> DuckBox.options.money = !DuckBox.options.money;
          case "oculos" -> DuckBox.options.glasses = !DuckBox.options.glasses;
          case "sapo" -> DuckBox.options.frog = !DuckBox.options.frog;
        }
        DuckBox.save();
        DuckBox.toggleSetting(owner, key, DuckBox.cosmeticEnabled(key));
      } else DuckBox.control(owner, key);
      if (owner.currentScreenHandler == this) refresh();
    } catch (Exception e) {
      DuckBox.say(owner, e.getMessage());
    }
  }
}
