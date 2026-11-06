package dev.duckbox;
public record ChestRolePayload(net.minecraft.util.Identifier dimension,net.minecraft.util.math.BlockPos pos,int role) implements LegacyPayload {
 public static final net.minecraft.util.Identifier ID=new net.minecraft.util.Identifier("duckbox","chest_role");
 public net.minecraft.util.Identifier id(){return ID;}
 public void write(net.minecraft.network.PacketByteBuf b){b.writeIdentifier(dimension);b.writeBlockPos(pos);b.writeVarInt(role);}
 public static ChestRolePayload read(net.minecraft.network.PacketByteBuf b){return new ChestRolePayload(b.readIdentifier(),b.readBlockPos(),b.readVarInt());}
}
