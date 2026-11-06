import java.util.*;
import com.mojang.authlib.GameProfile;
import dev.duckbox.cosmetic.*;
import dev.duckbox.LobbyBotPayload;
import net.minecraft.client.network.PlayerListEntry;
import net.minecraft.world.GameMode;
public final class SkinEntryRegression {
 public static void main(String[] args)throws Exception{
  net.minecraft.SharedConstants.createGameVersion();net.minecraft.Bootstrap.initialize();
  UUID id=UUID.randomUUID();CosmeticState.setLobby(new LobbyBotPayload(id,15));var entry=new PlayerListEntry(new GameProfile(id,"DuckBot"),false);
  var mode=Arrays.stream(PlayerListEntry.class.getDeclaredFields()).filter(f->f.getType()==GameMode.class).findFirst().orElseThrow();mode.setAccessible(true);
  for(var value:GameMode.values()){mode.set(entry,value);if(entry.getGameMode()!=value)throw new AssertionError("Cape must never replace game mode");}
  if(!entry.getSkinTexture().equals(BotSkin.TEXTURE)||!entry.getCapeTexture().equals(BotSkin.CAPE)||!entry.getElytraTexture().equals(BotSkin.CAPE))throw new AssertionError("Native skin/cape/elytra texture getters");
  var latency=Arrays.stream(PlayerListEntry.class.getDeclaredMethods()).filter(m->m.getReturnType()==void.class&&Arrays.equals(m.getParameterTypes(),new Class<?>[]{int.class})).findFirst().orElseThrow();latency.setAccessible(true);latency.invoke(entry,37);
  if(entry.getLatency()!=37)throw new AssertionError("Cape must not intercept latency updates");
  System.out.println("PASS REAL WOVEN BOT ENTRY: all4game modes, latency update and skin/cape/elytra getters executed without ClassCastException");
 }
}
