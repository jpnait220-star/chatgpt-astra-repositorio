package dev.duckbox;
public record TrainingPayload(java.util.UUID owner,java.util.UUID bot,boolean enabled,boolean instaKill) implements LegacyPayload {
 public static final net.minecraft.util.Identifier ID=new net.minecraft.util.Identifier("duckbox","training");
 public net.minecraft.util.Identifier id(){return ID;}
 public void write(net.minecraft.network.PacketByteBuf b){b.writeUuid(owner);b.writeUuid(bot);b.writeBoolean(enabled);b.writeBoolean(instaKill);}
 public static TrainingPayload read(net.minecraft.network.PacketByteBuf b){return new TrainingPayload(b.readUuid(),b.readUuid(),b.readBoolean(),b.readBoolean());}
public TrainingPayload(java.util.UUID owner,java.util.UUID bot,boolean enabled){this(owner,bot,enabled,false);}
}
