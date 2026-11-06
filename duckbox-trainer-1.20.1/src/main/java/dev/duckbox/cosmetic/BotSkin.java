package dev.duckbox.cosmetic;

import java.util.UUID;
import net.minecraft.util.Identifier;

/** Local packaged skin, independent of remote skin services and cosmetic toggles. */
public final class BotSkin {
  public static final Identifier TEXTURE =
      new Identifier("duckbox", "textures/entity/robot_duck.png");
  public static final Identifier CAPE = new Identifier("duckbox", "textures/entity/yellow_cape.png");
  public static net.minecraft.util.Identifier resolve(java.util.UUID id,net.minecraft.util.Identifier original){return CosmeticState.isBot(id)?TEXTURE:original;}
}
