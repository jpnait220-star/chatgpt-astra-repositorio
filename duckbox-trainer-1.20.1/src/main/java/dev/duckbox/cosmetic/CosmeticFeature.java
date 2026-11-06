package dev.duckbox.cosmetic;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.client.render.entity.PlayerEntityRenderer;
import net.minecraft.client.render.entity.feature.FeatureRenderer;
import net.minecraft.client.render.entity.model.PlayerEntityModel;
import net.minecraft.client.network.AbstractClientPlayerEntity;
import net.minecraft.client.util.math.MatrixStack;

public final class CosmeticFeature
    extends FeatureRenderer<AbstractClientPlayerEntity, PlayerEntityModel<AbstractClientPlayerEntity>> {
  private static final class Models {
    static final BedrockCosmetic[] ALL = {
      new BedrockCosmetic("demon2024bloodfists"),
      new BedrockCosmetic("theobaldmoneyaura"),
      new BedrockCosmetic("gamergamerglasses"),
      new BedrockCosmetic("spring2025froghat")
    };
  }

  public CosmeticFeature(PlayerEntityRenderer renderer) {
    super(renderer);
  }

  @Override
  public void render(
      MatrixStack matrices,
      VertexConsumerProvider vertices,
      int light,
      AbstractClientPlayerEntity entity,
      float limb, float angle, float delta, float progress, float yaw, float pitch) {
    var client = MinecraftClient.getInstance();
    if (client.world == null || entity.isInvisible()) return;
    if (entity == null) return;
    float time =
        ((client.world.getTime() % 100000) + client.getTickDelta())
            / 20f;
    for (int i = 0; i < 4; i++)
      if (CosmeticState.enabled(entity.getUuid(), 1 << i))
        Models.ALL[i].draw(getContextModel(), matrices, vertices, light, time);
  }

  public static void firstPerson(
      PlayerEntityModel model,
      MatrixStack matrices,
      VertexConsumerProvider vertices,
      int light,
      boolean left) {
    var client = MinecraftClient.getInstance();
    if (client.player == null
        || client.world == null
        || !CosmeticState.enabled(client.player.getUuid(), 1)) return;
    boolean main =
        client.player.getMainArm()
            == (left ? net.minecraft.util.Arm.LEFT : net.minecraft.util.Arm.RIGHT);
    if (!(main ? client.player.getMainHandStack() : client.player.getOffHandStack()).isEmpty())
      return;
    Models.ALL[0].draw(
        model,
        matrices,
        vertices,
        light,
        ((client.world.getTime() % 100000) + client.getTickDelta())
            / 20f,
        left);
  }
}
