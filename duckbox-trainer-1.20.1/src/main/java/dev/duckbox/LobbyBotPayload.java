package dev.duckbox;
public record LobbyBotPayload(java.util.UUID bot,int mask) implements LegacyPayload {
 public static final net.minecraft.util.Identifier ID=new net.minecraft.util.Identifier("duckbox","lobby_bot");
 public net.minecraft.util.Identifier id(){return ID;}
 public void write(net.minecraft.network.PacketByteBuf b){b.writeUuid(bot);b.writeVarInt(mask);}
 public static LobbyBotPayload read(net.minecraft.network.PacketByteBuf b){return new LobbyBotPayload(b.readUuid(),b.readVarInt());}
}
