package dev.duckbox;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.networking.v1.*;

public final class DuckBoxClient implements ClientModInitializer {
  @Override
  public void onInitializeClient() {
    net.fabricmc.fabric.api.client.rendering.v1.LivingEntityFeatureRendererRegistrationCallback
        .EVENT
        .register(
            (type, renderer, helper, context) -> {
              if (renderer
                  instanceof net.minecraft.client.render.entity.PlayerEntityRenderer player)
                helper.register(new dev.duckbox.cosmetic.CosmeticFeature(player));
            });
    ClientPlayNetworking.registerGlobalReceiver(
        CosmeticPayload.ID,
        (payload, context) ->
            context.client().execute(() -> dev.duckbox.cosmetic.CosmeticState.set(payload)));
    ClientPlayNetworking.registerGlobalReceiver(
        TrainingPayload.ID,
        (payload, context) -> context.client().execute(() -> ClientTrainingState.set(payload)));
    ClientPlayConnectionEvents.DISCONNECT.register(
        (handler, client) -> {
          ClientTrainingState.clear();
          dev.duckbox.cosmetic.CosmeticState.clear();
        });
  }
}
