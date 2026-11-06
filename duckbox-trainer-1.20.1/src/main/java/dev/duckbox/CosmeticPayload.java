package dev.duckbox;
public record CosmeticPayload(java.util.UUID owner,java.util.UUID bot,int mask) implements LegacyPayload {
 public static final net.minecraft.util.Identifier ID=new net.minecraft.util.Identifier("duckbox","cosmetics");
 public net.minecraft.util.Identifier id(){return ID;}
 public void write(net.minecraft.network.PacketByteBuf b){b.writeUuid(owner);b.writeUuid(bot);b.writeVarInt(mask);}
 public static CosmeticPayload read(net.minecraft.network.PacketByteBuf b){return new CosmeticPayload(b.readUuid(),b.readUuid(),b.readVarInt());}
}
