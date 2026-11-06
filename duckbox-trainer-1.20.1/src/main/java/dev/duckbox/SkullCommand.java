package dev.duckbox;

import com.google.gson.*;
import com.mojang.authlib.GameProfile;
import com.mojang.authlib.properties.Property;
import java.net.URI;
import java.net.http.*;
import java.time.Duration;
import java.util.UUID;
import java.util.concurrent.*;
import net.minecraft.entity.attribute.*;
import net.minecraft.item.*;
import net.minecraft.server.network.ServerPlayerEntity;

public final class SkullCommand {
  private static final HttpClient HTTP =
      HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();

  private static CompletableFuture<JsonObject> json(String url) {
    var request =
        HttpRequest.newBuilder(URI.create(url))
            .timeout(Duration.ofSeconds(8))
            .header("User-Agent", "DuckBoxTrainer")
            .GET()
            .build();
    return HTTP.sendAsync(request, HttpResponse.BodyHandlers.ofString())
        .thenApply(
            r -> {
              if (r.statusCode() != 200)
                throw new IllegalArgumentException(
                    "Jogador original nao encontrado ou Mojang indisponivel.");
              return JsonParser.parseString(r.body()).getAsJsonObject();
            });
  }

  public static ItemStack head(
      net.minecraft.registry.DynamicRegistryManager registries, GameProfile profile) {
    var head = new ItemStack(Items.PLAYER_HEAD);
    head.getOrCreateNbt().put("SkullOwner",net.minecraft.nbt.NbtHelper.writeGameProfile(new net.minecraft.nbt.NbtCompound(),profile));
    Kits.add(head,net.minecraft.entity.attribute.EntityAttributes.GENERIC_MAX_HEALTH,"head/max_health",60,net.minecraft.entity.EquipmentSlot.HEAD);
    head.addEnchantment(net.minecraft.enchantment.Enchantments.PROTECTION,60);
    return head;
  }

  public static void give(ServerPlayerEntity p, String name) {
    if (!name.matches("[A-Za-z0-9_]{3,16}"))
      throw new IllegalArgumentException("Use um nick original de3 a16 caracteres.");
    var server = p.getServer();
    var actor = p.getUuid();
    DuckBox.setting(p, "Buscando a skin original de " + name + "...");
    json("https://api.mojang.com/users/profiles/minecraft/" + name)
        .thenCompose(
            entry ->
                json(
                    "https://sessionserver.mojang.com/session/minecraft/profile/"
                        + entry.get("id").getAsString()
                        + "?unsigned=false"))
        .whenComplete(
            (entry, error) ->
                server.execute(
                    () -> {
                      var target = server.getPlayerManager().getPlayer(actor);
                      if (target == null) return;
                      if (error != null) {
                        DuckBox.say(
                            target,
                            "Nao foi possivel buscar esse jogador original. Confira o nick e a"
                                + " conexao com a Mojang.");
                        return;
                      }
                      try {
                        String raw = entry.get("id").getAsString();
                        UUID uuid =
                            UUID.fromString(
                                raw.substring(0, 8)
                                    + "-"
                                    + raw.substring(8, 12)
                                    + "-"
                                    + raw.substring(12, 16)
                                    + "-"
                                    + raw.substring(16, 20)
                                    + "-"
                                    + raw.substring(20));
                        var profile = new GameProfile(uuid, entry.get("name").getAsString());
                        for (var property : entry.getAsJsonArray("properties")) {
                          var value = property.getAsJsonObject();
                          profile
                              .getProperties()
                              .put(
                                  value.get("name").getAsString(),
                                  new Property(
                                      value.get("name").getAsString(),
                                      value.get("value").getAsString(),
                                      value.has("signature")
                                          ? value.get("signature").getAsString()
                                          : null));
                        }
                        target
                            .getInventory()
                            .offerOrDrop(head(target.getServerWorld().getRegistryManager(), profile));
                        DuckBox.setting(
                            target,
                            "Cabeca entregue: " + profile.getName() + " / Vida+60 / Protecao60");
                      } catch (Exception bad) {
                        DuckBox.say(
                            target, "Resposta de perfil invalida; tente novamente mais tarde.");
                      }
                    }));
  }
}
