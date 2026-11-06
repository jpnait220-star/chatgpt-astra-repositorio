package dev.duckbox;

import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.*;
import net.minecraft.client.gui.screen.world.CreateWorldScreen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.text.Text;

/** A clear world choice instead of overlaying buttons over vanilla's existing settings. */
public final class DuckWorldScreen extends Screen {
  private final CreateWorldScreen normal;
  private final String error;
  private static CreateWorldScreen pending;
  private static final java.util.Set<Screen> offered = java.util.Collections.newSetFromMap(new java.util.WeakHashMap<>());

  private DuckWorldScreen(CreateWorldScreen normal, String error) {
    super(Text.literal("Criar mundo"));
    this.normal = normal;
    this.error = error;
  }

  public static void register() {
    ScreenEvents.AFTER_INIT.register((client, screen, width, height) -> {
      if (screen instanceof CreateWorldScreen create && offered.add(screen))
        pending = create;
    });
    net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents.END_CLIENT_TICK.register(client -> {
      var next = pending;
      pending = null;
      if (next != null && client.currentScreen == next)
        client.setScreen(new DuckWorldScreen(next, null));
    });
  }

  protected void init() {
    int x = width / 2 - 110, y = height / 2 - 12;
    addDrawableChild(ButtonWidget.builder(Text.literal("Mundo de Duckzin"), b -> create())
        .dimensions(x, y, 220, 20).build());
    addDrawableChild(ButtonWidget.builder(Text.literal("Gerar mundo normal"), b -> client.setScreen(normal))
        .dimensions(x, y + 25, 220, 20).build());
    addDrawableChild(ButtonWidget.builder(Text.literal("Voltar"), b -> close())
        .dimensions(x, y + 50, 220, 20).build());
  }

  private void create() {
    var minecraft = client;
    var saves = minecraft.getLevelStorage().getSavesDirectory();
    minecraft.setScreen(new MessageScreen(Text.literal("Preparando o Mundo de Duckzin...")));
    java.util.concurrent.CompletableFuture.supplyAsync(() -> {
      try { return WorldTemplate.create(saves); }
      catch (java.io.IOException e) { throw new java.util.concurrent.CompletionException(e); }
    }).whenComplete((folder, failure) -> minecraft.execute(() -> {
      if (failure != null) {
        minecraft.setScreen(new DuckWorldScreen(normal, "Nao foi possivel copiar o mapa. Tente novamente."));
      } else minecraft.createIntegratedServerLoader().start(folder.getFileName().toString(),
          () -> minecraft.setScreen(new DuckWorldScreen(normal, null)));
    }));
  }

  public void close() { normal.close(); }

  public void render(DrawContext context, int mouseX, int mouseY, float delta) {
    super.render(context, mouseX, mouseY, delta);
    context.drawCenteredTextWithShadow(textRenderer, title, width / 2, height / 2 - 65, 0xffffff);
    context.drawCenteredTextWithShadow(textRenderer,
        Text.literal(error == null ? "Mapa pronto, arena e perfis configurados." : error),
        width / 2, height / 2 - 42, error == null ? 0xcccccc : 0xff7777);
  }
}
