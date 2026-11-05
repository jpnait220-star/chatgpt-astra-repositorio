package dev.duckbox.cosmetic;

import java.util.UUID;
import net.minecraft.client.render.entity.state.PlayerEntityRenderState;
import net.minecraft.client.util.SkinTextures;
import net.minecraft.util.Identifier;

/** Local packaged skin, independent of remote skin services and cosmetic toggles. */
public final class BotSkin {
  public static final Identifier TEXTURE =
      Identifier.of("duckbox", "textures/entity/robot_duck.png");
  public static final Identifier CAPE = Identifier.of("duckbox", "textures/entity/yellow_cape.png");
  public static final SkinTextures ROBOT =
      new SkinTextures(TEXTURE, null, CAPE, CAPE, SkinTextures.Model.WIDE, false);

  public static SkinTextures resolve(UUID profile, SkinTextures original) {
    return CosmeticState.isBot(profile) ? ROBOT : original;
  }

  public static void apply(UUID profile, PlayerEntityRenderState state) {
    if (!CosmeticState.isBot(profile)) return;
    state.skinTextures = ROBOT;
    state.capeVisible = true;
    state.wearingSkullType = null;
    state.wearingSkullProfile = null;
    state.headItemRenderState.clear();
    state.hatVisible = true;
    state.jacketVisible = true;
    state.leftPantsLegVisible = true;
    state.rightPantsLegVisible = true;
    state.leftSleeveVisible = true;
    state.rightSleeveVisible = true;
  }
}
