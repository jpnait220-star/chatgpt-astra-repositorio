package dev.duckbox;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.networking.v1.*;

public final class DuckBoxClient implements ClientModInitializer {
  @Override
  public void onInitializeClient() {
    ClientPlayNetworking.registerGlobalReceiver(
        TrainingPayload.ID,
        (payload, context) -> context.client().execute(() -> ClientTrainingState.set(payload)));
    ClientPlayConnectionEvents.DISCONNECT.register(
        (handler, client) -> ClientTrainingState.clear());
  }
}
