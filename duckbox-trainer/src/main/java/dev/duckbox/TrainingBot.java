package dev.duckbox;

import com.mojang.authlib.GameProfile;
import java.net.*;
import java.util.UUID;
import net.minecraft.network.*;
import net.minecraft.network.packet.Packet;
import net.minecraft.network.packet.c2s.common.SyncedClientOptions;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.*;
import net.minecraft.server.world.ServerWorld;

/** A real survival ServerPlayerEntity; inventory, damage and movement stay vanilla. */
public final class TrainingBot extends ServerPlayerEntity {
  public Session session;
  private int lastServerTick = Integer.MIN_VALUE;

  public TrainingBot(MinecraftServer server, ServerWorld world) {
    this(
        server,
        world,
        new GameProfile(
            UUID.nameUUIDFromBytes(
                ("DuckBox:" + server.getSaveProperties().getLevelName())
                    .getBytes(java.nio.charset.StandardCharsets.UTF_8)),
            "DuckBot"));
  }

  public TrainingBot(MinecraftServer server, ServerWorld world, GameProfile profile) {
    super(server, world, profile, SyncedClientOptions.createDefault());
  }

  private long incomingHits,
      registeredHits,
      cooldownRejections,
      protectionRejections,
      otherRejections;

  @Override
  public boolean damage(
      ServerWorld world, net.minecraft.entity.damage.DamageSource source, float amount) {
    boolean tracked = session != null && !session.closed && source.getAttacker() == session.owner;
    boolean protectedHit = tracked && (session.countingDown() || isInvulnerableTo(world, source));
    boolean cooldown = tracked && timeUntilRegen > 10;
    boolean accepted = super.damage(world, source, amount);
    if (tracked) {
      incomingHits++;
      if (accepted) registeredHits++;
      else if (protectedHit) protectionRejections++;
      else if (cooldown) cooldownRejections++;
      else otherRejections++;
    }
    return accepted;
  }

  public String hitReport() {
    return "Dano recebido pelo servidor: "
        + incomingHits
        + " | Registrados: "
        + registeredHits
        + " | Intervalo vanilla: "
        + cooldownRejections
        + " | Protecao/contagem: "
        + protectionRejections
        + " | Outros: "
        + otherRejections;
  }

  @Override
  public void tick() {
    int now = getServer().getTicks();
    if (now == lastServerTick) return;
    lastServerTick = now;
    // A server-controlled player has no client to acknowledge world loading/teleports.
    // Do this before AI/damage checks rather than waiting for vanilla's 60-tick timeout.
    setLoaded(true);
    if (isInTeleportationState()) onTeleportationDone();
    if (session != null && !session.closed) session.control();
    super.tick();
    playerTick();
    if (isInTeleportationState()) onTeleportationDone();
    if (age % 10 == 0) {
      networkHandler.syncWithPlayerPosition();
      getServerWorld().getChunkManager().updatePosition(this);
    }
  }

  public static class LocalConnection extends ClientConnection {
    private net.minecraft.network.listener.PacketListener listener;

    public LocalConnection() {
      super(NetworkSide.SERVERBOUND);
    }

    @Override
    public <T extends net.minecraft.network.listener.PacketListener> void transitionInbound(
        NetworkState<T> state, T handler) {
      listener = handler;
    }

    @Override
    public void transitionOutbound(NetworkState<?> state) {}

    @Override
    public net.minecraft.network.listener.PacketListener getPacketListener() {
      return listener;
    }

    @Override
    public String getAddressAsString(boolean logIps) {
      return "DuckBox-local";
    }

    @Override
    public void submit(java.util.function.Consumer<ClientConnection> task) {
      task.accept(this);
    }

    @Override
    public void flush() {}

    @Override
    public boolean isOpen() {
      return true;
    }

    @Override
    public boolean isLocal() {
      return true;
    }

    @Override
    public SocketAddress getAddress() {
      return new InetSocketAddress("127.0.0.1", 0);
    }

    @Override
    public void send(Packet<?> packet) {}

    @Override
    public void send(Packet<?> packet, PacketCallbacks callbacks) {}

    @Override
    public void send(Packet<?> packet, PacketCallbacks callbacks, boolean flush) {}
  }
}
