package dev.duckbox;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.networking.v1.*;

public final class DuckBoxClient implements ClientModInitializer {
  @Override
  public void onInitializeClient() {
    DuckWorldScreen.register();
    dev.duckbox.panels.PanelItemRenderer.register();
    net.fabricmc.fabric.api.client.rendering.v1.BlockEntityRendererRegistry.register(
        dev.duckbox.chests.MapChests.TYPE, context -> new dev.duckbox.chests.DuckChestRenderer());
    net.fabricmc.fabric.api.client.rendering.v1.BlockEntityRendererRegistry.register(
        dev.duckbox.panels.MapPanels.TYPE, context -> new dev.duckbox.panels.PanelBlockRenderer());
    net.fabricmc.fabric.api.client.rendering.v1.LivingEntityFeatureRendererRegistrationCallback
        .EVENT
        .register(
            (type, renderer, helper, context) -> {
              if (renderer
                  instanceof net.minecraft.client.render.entity.PlayerEntityRenderer player)
                helper.register(new dev.duckbox.cosmetic.CosmeticFeature(player));
            });
    ClientPlayNetworking.registerGlobalReceiver(
        LobbyBotPayload.ID,
        (payload, context) ->
            context.client().execute(() -> dev.duckbox.cosmetic.CosmeticState.setLobby(payload)));
    ClientPlayNetworking.registerGlobalReceiver(
        CosmeticPayload.ID,
        (payload, context) ->
            context.client().execute(() -> dev.duckbox.cosmetic.CosmeticState.set(payload)));
    ClientPlayNetworking.registerGlobalReceiver(
        ChestRolePayload.ID,
        (payload, context) -> context.client().execute(() -> ChestRoleSync.receive(payload)));
    ClientPlayNetworking.registerGlobalReceiver(
        TrainingPayload.ID,
        (payload, context) -> context.client().execute(() -> ClientTrainingState.set(payload)));
    ClientPlayConnectionEvents.DISCONNECT.register(
        (handler, client) -> {
          ClientTrainingState.clear();
          ChestRoleSync.clearClient();
          dev.duckbox.cosmetic.CosmeticState.clear();
        });
  }
}
