package dev.duckbox;

import java.util.*;
import net.minecraft.entity.*;
import net.minecraft.entity.effect.*;
import net.minecraft.item.*;
import net.minecraft.server.network.*;
import net.minecraft.text.Text;
import net.minecraft.util.*;
import net.minecraft.util.hit.*;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;

public final class Session {
  public final ServerPlayerEntity owner;
  public final TrainingBot bot;
  public final Options o;
  public boolean closed;
  public String finish;
  private final Random random = new Random();
  private long clock;
  private CpsCadence clicks;
  private int clickRate;
  private int settingsVisibleUntil;

  public void holdSettingMessage() {
    settingsVisibleUntil = bot.getServer().getTicks() + 40;
  }

  private int buildAt;
  private BlockPos breakingWeb;
  private float webBreakProgress;
  private int breakStartedAt, mineReadyAt;
  private boolean mineStopSent;
  private BlockPos minePrepared;
  private int minePrepareAt;
  private final Map<BlockPos, net.minecraft.block.BlockState> builtBlocks = new HashMap<>();
  private int rocketAt,
      webAt,
      jumpAt,
      maneuverUntil,
      maneuverAt = 30,
      swapAt = -1,
      pendingSlot = -1,
      refillAt = -1,
      gapWait,
      heldUntil;
  private int retotemRetryAt;
  private int refillCount;

  public int refillCount() {
    return refillCount;
  }

  private int side = 1, damageCount, gapsLeft, healingStartedAt, appleCountBefore, escapeUntil;
  private float lastHealth, fullHealth;
  private boolean healing, escaping, airGap, strafeActive, finishAppleThenFight;
  private boolean groundRecovery, landingForGap;
  private int tankGroundAt = 160, landingUntil;

  private enum WebRoute {
    NONE,
    AIR,
    TOWER
  }

  private WebRoute webRoute = WebRoute.NONE;
  private BlockPos routeTarget, trappedHead, towerColumn;
  private int routeUntil, headWebSince, cageIndex, cageAt;
  private int towerProgressAt, webRouteAttempts;
  private Vec3d recoveryLastPos;
  private int recoveryStuckTicks;
  private int webEscapeSince = -1;
  private BlockPos plantedFootWeb;
  private boolean leavingFootWeb;
  private int footRetryAt, footAttackWebAt;
  private int ownerTotemUses, botTotemUses;
  private int lastOwnerPopAt = -10000, lastBotPopAt = -10000;

  /** In this aggressive mode recovery is allowed only when the opponent retreats to eat. */
  private int recoveryEpisodeAt, attackCommitUntil, gapResponseAt, lowSupplyAppleAt;

  private int recoveryChoiceAt;

  private boolean recoveryChoice;

  public boolean mayRecover(boolean opponentEating, double squaredDistance) {
    if (!o.noRetreatRetotem || (opponentEating && squaredDistance > 9)) return true;
    boolean losing =
        Aim.fraction(bot.getHealth(), bot.getMaxHealth()) + .04
            < Aim.fraction(owner.getHealth(), owner.getMaxHealth());
    if (!losing) return false;
    // One 50% decision per opportunity, held for ten seconds (never rolled every tick).
    if (clock >= recoveryChoiceAt) {
      recoveryChoice = random.nextBoolean();
      recoveryChoiceAt = (int) clock + 200;
    }
    return recoveryChoice;
  }

  private String phase = "Preparando";
  private Vec3d recoveryPoint;
  private double aimX, aimY, aimZ;

  public Session(ServerPlayerEntity p, TrainingBot b, Options options) {
    owner = p;
    bot = b;
    o = options;
    clickRate = Options.allowedCps(options.cps) ? options.cps : 15;
    clicks = new CpsCadence(clickRate);
    b.session = this;
    ownerTotemUses = p.getStatHandler().getStat(net.minecraft.stat.Stats.USED, Items.TOTEM_OF_UNDYING);
    botTotemUses = b.getStatHandler().getStat(net.minecraft.stat.Stats.USED, Items.TOTEM_OF_UNDYING);
    lastHealth = b.getHealth() + b.getAbsorptionAmount();
    aimX = p.getX();
    aimY = p.getEyeY();
    aimZ = p.getZ();
  }

  private int countdownTicks;
  private Vec3d ownerCorner, botCorner;

  public boolean countingDown() {
    return countdownTicks > 0;
  }

  public void beginCountdown() {
    countdownTicks = 100;
    double offset = o.size / 2.0 - 2.5;
    ownerCorner = new Vec3d(o.x - offset, o.y + 1, o.z + 0.5);
    botCorner = new Vec3d(o.x + offset, o.y + 1, o.z + 0.5);
    moveToCorner(owner, ownerCorner, -90);
    moveToCorner(bot, botCorner, 90);

    bot.onTeleportationDone();
    for (var p : List.of(owner, bot)) p.setHealth(p.getMaxHealth());
    showCount("5");
  }

  private void moveToCorner(ServerPlayerEntity p, Vec3d corner, float yaw) {
    p.stopUsingItem();
    p.stopFallFlying();
    p.setSneaking(false);
    p.setSprinting(false);
    p.forwardSpeed = 0;
    p.sidewaysSpeed = 0;
    p.setVelocity(Vec3d.ZERO);
    p.teleport(p.getServerWorld(), corner.x, corner.y, corner.z, Set.of(), yaw, 0);
    p.setHeadYaw(yaw);
    p.setBodyYaw(yaw);
  }

  private void holdCorner(ServerPlayerEntity p, Vec3d corner) {
    p.stopFallFlying();
    p.stopUsingItem();
    p.forwardSpeed = 0;
    p.sidewaysSpeed = 0;
    p.setVelocity(Vec3d.ZERO);
    if (p.getPos().squaredDistanceTo(corner) > 0.0001)
      p.teleport(
          p.getServerWorld(),
          corner.x,
          corner.y,
          corner.z,
          Set.of(),
          p.getYaw(),
          p.getPitch());
  }

  private void showCount(String value) {
    for (var p : List.of(owner, bot)) {
      p.networkHandler.sendPacket(
          new net.minecraft.network.packet.s2c.play.TitleFadeS2CPacket(0, 22, 0));
      p.networkHandler.sendPacket(
          new net.minecraft.network.packet.s2c.play.TitleS2CPacket(
              Text.literal(value)
                  .formatted(value.equals("VAI!") ? Formatting.GREEN : Formatting.YELLOW)));
    }
  }

  private void tickCountdown() {
    if (owner.getServerWorld() != bot.getServerWorld() || owner.isDisconnected()) {
      finish = "Treino encerrado: jogador saiu.";
      return;
    }
    holdCorner(owner, ownerCorner);
    holdCorner(bot, botCorner);
    phase = "Comeca em " + (countdownTicks + 19) / 20;
    countdownTicks--;
    if (countdownTicks == 0) {
      startingBuffs();
      for (var p : List.of(owner, bot)) {
        p.timeUntilRegen = 0;
        p.setHealth(p.getMaxHealth());
      }
      lastHealth = bot.getHealth() + bot.getAbsorptionAmount();
      showCount("VAI!");
    } else if (countdownTicks % 20 == 0) showCount(Integer.toString(countdownTicks / 20));
  }

  private boolean committedApple() {
    if (!healing || !bot.isUsingItem()) return false;
    var item = bot.getActiveItem();
    if (!item.isOf(Items.GOLDEN_APPLE) && !item.isOf(Items.ENCHANTED_GOLDEN_APPLE)) return false;
    int used = bot.getItemUseTime(), total = used + bot.getItemUseTimeLeft();
    return total > 0 && used * 5 >= total * 3;
  }

  private boolean scarceAirTracking() {
    return countTotems() <= 4 && (owner.isFallFlying() || !owner.isOnGround());
  }

  private float combatAimSpeed() {
    return o.difficulty.aimSpeed * (scarceAirTracking() ? 1.36f : countTotems() <= 2 ? 1.1f : 1);
  }

  private double combatAimErrorScale() {
    return scarceAirTracking() ? 1.0 / 1.36 : countTotems() <= 2 ? .9 : 1;
  }

  private int speedPotionAt, potionCrouchUntil;
  private boolean initialPotionChecked;

  private boolean useSpeedPotion(int t) {
    return useSpeedPotion(t, false);
  }

  private boolean useSpeedPotion(int t, boolean preparingGap) {
    boolean initial = !initialPotionChecked && t <= 20;
    initialPotionChecked = true;
    if (committedApple() || t < speedPotionAt || bot.hasStatusEffect(StatusEffects.SPEED)) return false;
    double distance = bot.squaredDistanceTo(owner);
    boolean opponentRecovering = owner.isUsingItem() && distance > 9
        && (owner.getActiveItem().isOf(Items.GOLDEN_APPLE)
            || owner.getActiveItem().isOf(Items.ENCHANTED_GOLDEN_APPLE));
    if (!initial && !preparingGap && !healing && !escaping && !landingForGap
        && distance <= 25 && !opponentRecovering) return false;
    int chosen = -1, bestPower = -1, bestDuration = -1;
    for (int i = 0; i < 36; i++) {
      var stack = bot.getInventory().getStack(i);
      if (!stack.isOf(Items.SPLASH_POTION) && !stack.isOf(Items.LINGERING_POTION)
          && !stack.isOf(Items.POTION)) continue;
      var contents = net.minecraft.potion.PotionUtil.getPotionEffects(stack);

      for (var effect : contents) {
        if (!effect.getEffectType().equals(StatusEffects.SPEED)) continue;
        if (effect.getAmplifier() > bestPower
            || effect.getAmplifier() == bestPower && effect.getDuration() > bestDuration) {
          chosen = i;
          bestPower = effect.getAmplifier();
          bestDuration = effect.getDuration();
        }
      }
    }
    speedPotionAt = t + 20;
    if (chosen < 0) return false;
    boolean resumeGap = healing || escaping || landingForGap || preparingGap;
    if (healing || escaping || landingForGap) endRecovery(t, 3);
    if (chosen >= 9) {
      var displaced = bot.getInventory().getStack(4);
      bot.getInventory().setStack(4, bot.getInventory().getStack(chosen));
      bot.getInventory().setStack(chosen, displaced);
      chosen = 4;
    }
    bot.getInventory().selectedSlot = chosen;
    boolean drinking = bot.getMainHandStack().isOf(Items.POTION);
    bot.setPitch(90);
    bot.forwardSpeed = bot.sidewaysSpeed = 0;
    var result = bot.getMainHandStack().use(bot.getServerWorld(), bot, Hand.MAIN_HAND);
    if (!result.getResult().isAccepted()) {
      selectSword();
      return false;
    }
    speedPotionAt = t + 40 * 20;
    bot.swingHand(Hand.MAIN_HAND);
    potionCrouchUntil = t + 3;
    bot.setSneaking(true);
    heldUntil = t + (drinking ? Math.max(3, bot.getItemUseTimeLeft() + 1) : 3);
    phase = drinking ? "Bebendo Speed" : "Potando Speed";
    if (!drinking) selectSword();
    if (resumeGap) { gapWait = t + 3; attackCommitUntil = t + 3; }
    return true;
  }

  public void maintainRules() {
    int amplifier = o.rules == Options.Rules.NORMAL_SPAM && o.resistance2 ? 1 : 0;
    for (var p : List.of(owner, bot)) {
      var effect = p.getStatusEffect(StatusEffects.RESISTANCE);
      if (o.fastTotemPop) {
        // Keep finite gap buffs, but stop maintaining our infinite resistance.
        if (effect != null && effect.isInfinite()) p.removeStatusEffect(StatusEffects.RESISTANCE);
        continue;
      }
      if (effect == null || effect.getAmplifier() != amplifier || !effect.isInfinite()) {
        p.removeStatusEffect(StatusEffects.RESISTANCE);
        p.addStatusEffect(
            new StatusEffectInstance(StatusEffects.RESISTANCE, -1, amplifier, false, false, true));
      }
    }
  }

  public void startingBuffs() {
    maintainRules();
    for (var p : List.of(owner, bot)) {
      if (o.fastTotemPop)
        p.addStatusEffect(
            new StatusEffectInstance(StatusEffects.RESISTANCE, 6000, 0, false, false, true));
      p.addStatusEffect(
          new StatusEffectInstance(StatusEffects.REGENERATION, 400, 1, false, false, true));
      p.addStatusEffect(
          new StatusEffectInstance(StatusEffects.ABSORPTION, 2400, 3, false, false, true));
      p.addStatusEffect(
          new StatusEffectInstance(StatusEffects.FIRE_RESISTANCE, 6000, 0, false, false, true));
    }
  }

  public void control() {
    if (closed || finish != null) return;
    if (countingDown()) {
      tickCountdown();
      return;
    }
    int t = (int) ++clock;
    trackTotemPops(t);
    var d = o.difficulty;
    if (!owner.isAlive()
        || owner.isDisconnected()
        || owner.getServerWorld() != bot.getServerWorld()) {
      finish = "Treino encerrado: jogador saiu.";
      return;
    }
    maintainRules();
    bot.forwardSpeed = 0;
    bot.sidewaysSpeed = 0;
    bot.setSneaking(bot.isFallFlying() || t < potionCrouchUntil);
    fullHealth = Math.max(fullHealth, bot.getMaxHealth());
    double dist = bot.squaredDistanceTo(owner);
    float health = bot.getHealth();
    if (countTotems() <= 2) {
      gapWait = Math.min(gapWait, t + 77);
      attackCommitUntil = Math.min(attackCommitUntil, t + 62);
    }
    if (t % 30 == 0 && random.nextBoolean()) side = -side;
    if (t % d.reaction == 0) strafeActive = random.nextDouble() < d.strafe;
    float vitality = health + bot.getAbsorptionAmount();
    if (vitality < lastHealth) {
      damageCount++;
      if (committedApple()) finishAppleThenFight = true;
      if ((healing || escaping) && damageCount >= 2 && !committedApple()) endRecovery(t, 45);
    } else if (t % 40 == 0) damageCount = 0;
    lastHealth = vitality;
    if (!o.tank
        && recoveryEpisodeAt > 0
        && (healing || escaping || landingForGap)
        && t - recoveryEpisodeAt >= 100 && !committedApple()) endRecovery(t, 100);

    if (!healing && !escaping && !landingForGap && pendingSlot < 0 && heldUntil <= t)
      ensureSwordInHotbar();
    if (o.retotem && !committedApple() && retotem(t)) return;
    if (heldUntil > t) {
      phase = "Trocando item";
      return;
    }
    if (heldUntil != 0) {
      heldUntil = 0;
      selectSword();
    }
    if (useSpeedPotion(t)) return;
    if (Math.abs(owner.getX() - o.x) > o.size / 2.0 + 3
        || Math.abs(owner.getZ() - o.z) > o.size / 2.0 + 3
        || owner.getY() < o.y - 3
        || owner.getY() > o.y + Arena.HEIGHT + 3) {
      finish = "Voce saiu da arena.";
      return;
    }
    boolean opponentEatingNow =
        owner.isUsingItem()
            && owner.getActiveItem().isFood();
    if (committedApple() && !mayRecover(opponentEatingNow, dist)) finishAppleThenFight = true;
    if (!committedApple() && !mayRecover(opponentEatingNow, dist) && (healing || escaping || landingForGap))
      endRecovery(t, 10);
    boolean retreatForHealth =
        o.noRetreatRetotem
            && mayRecover(opponentEatingNow, dist)
            && bot.getHealth() < bot.getMaxHealth() - 4
            && apples() > 0
            && o.gap;
    if (retreatForHealth && plantedFootWeb != null) leavingFootWeb = true;
    boolean ownFaceWeb =
        bot.getServerWorld()
            .getBlockState(BlockPos.ofFloored(bot.getEyePos()))
            .isOf(net.minecraft.block.Blocks.COBWEB);
    if (ownFaceWeb && !committedApple() && (healing || escaping || landingForGap)) endRecovery(t, 100);
    if (ownFaceWeb && !committedApple() && bot.isFallFlying()) escapeOwnWeb(t);
    if (ownFaceWeb && !committedApple() && bot.isOnGround() && !bot.isFallFlying()) {
      plantedFootWeb = null;
      leavingFootWeb = false;
      footRetryAt = t + 60;
      if (escapeOwnWeb(t)) return;
    }
    if (!healing && !escaping && !o.tank && standingDoubleWebFeet() != null
        && Math.abs(bot.getY() - owner.getY()) <= 1.2) {
      bot.stopFallFlying(); bot.setSneaking(false); bot.setSprinting(false); brakeIntoWeb();
      if (breakTargetWeb()) return;
    }
    if (!committedApple() && (!retreatForHealth || plantedFootWeb != null) && footWebFight(t, dist)) return;
    if (!healing && !escaping && !landingForGap && escapeOwnWeb(t)) return;
    // A consumed apple decreases the real inventory count; interruption does not.
    if (healing && !bot.isUsingItem()) {
      if (apples() < appleCountBefore) {
        gapsLeft--;
        if (countTotems() < 2) { lowSupplyAppleAt = t + 60; gapsLeft = 0; }
        if (finishAppleThenFight) gapsLeft = 0;
      }
      if (gapsLeft > 0 && health < recoveryHealthTarget() - 2) startApple(t);
      else endRecovery(t, 30);
    }
    if (healing && t - healingStartedAt > 45) endRecovery(t, 35);
    boolean scarceTotems = countTotems() <= 2;
    boolean behind =
        Aim.fraction(health, bot.getMaxHealth()) + 0.12
            < Aim.fraction(owner.getHealth(), owner.getMaxHealth());
    boolean otherEating =
        owner.isUsingItem()
            && owner.getActiveItem().isFood();
    boolean respondingToGap = otherEating && dist > 9 && t >= gapResponseAt
        && (owner.getActiveItem().isOf(Items.GOLDEN_APPLE)
            || owner.getActiveItem().isOf(Items.ENCHANTED_GOLDEN_APPLE));
    boolean tankGroundDue = o.tank && t >= tankGroundAt;
    if (!healing
        && !escaping
        && !landingForGap
        && gapsLeft == 0
        && o.gap
        && (countTotems() >= 2 || t >= lowSupplyAppleAt)
        && mayRecover(otherEating, dist)
        && (respondingToGap || t > gapWait && t >= attackCommitUntil)
        && (health < recoveryHealthTarget() - 4 || tankGroundDue)
        && (behind || otherEating || o.tank || health < bot.getMaxHealth() * 0.55)
        && apples() > 0) {
      if (useSpeedPotion(t, true)) return;
      recoveryEpisodeAt = t;
      if (respondingToGap) gapResponseAt = t + 20;
      groundRecovery = o.tank && (tankGroundDue || random.nextDouble() < 0.40);
      gapsLeft = groundRecovery || countTotems() < 2 ? 1 : health < bot.getMaxHealth() * 0.65 ? 2 : 1;
      damageCount = 0;
      airGap = !groundRecovery && o.giro && random.nextDouble() < 0.65;
      double radius = o.size / 2.0 - 1.8;
      recoveryPoint =
          new Vec3d(
              o.x + (random.nextBoolean() ? radius : -radius),
              o.y + (airGap ? Arena.HEIGHT - 1.6 : 1.2),
              o.z + (random.nextBoolean() ? radius : -radius));
      if (sustainedAirGap()) recoveryPoint = flightGapPoint();
      escaping = airGap;
      escapeUntil = t + (sustainedAirGap() ? 40 : 26);
      landingForGap = groundRecovery;
      landingUntil = t + 100;
      if (!escaping && !landingForGap) startApple(t);
    }
    if (landingForGap) {
      bot.stopFallFlying();
      bot.setSneaking(false);
      if (bot.isOnGround()) {
        landingForGap = false;
        startApple(t);
      } else if (t >= landingUntil) endRecovery(t, 40);
    }
    if ((healing || escaping || landingForGap) && recoveryPoint != null) {
      if (recoveryLastPos != null
          && bot.getPos().subtract(recoveryLastPos).horizontalLengthSquared() < 0.0001)
        recoveryStuckTicks++;
      else recoveryStuckTicks = 0;
      recoveryLastPos = bot.getPos();
      double edge = o.size / 2.0 - 1.8;
      if (recoveryStuckTicks > 12
          || Math.abs(bot.getX() - o.x) > edge
          || Math.abs(bot.getZ() - o.z) > edge) {
        // Move across the box instead of repeatedly staring into a corner/ceiling.
        recoveryPoint =
            new Vec3d(
                o.x - Math.signum(bot.getX() - o.x) * Math.max(1, edge - 1.0),
                groundRecovery ? o.y + 1.2 : Math.min(bot.getY() + 0.4, o.y + Arena.HEIGHT - 2),
                o.z - Math.signum(bot.getZ() - o.z) * Math.max(1, edge - 1.0));
        recoveryStuckTicks = 0;
        if (escaping && t >= escapeUntil) {
          escaping = false;
          startApple(t);
        }
      }
    } else {
      recoveryLastPos = null;
      recoveryStuckTicks = 0;
    }
    if (escaping && ((sustainedAirGap() ? bot.isFallFlying() : bot.getY() > o.y + 2.8)
        || t >= escapeUntil)) {
      escaping = false;
      startApple(t);
    }
    settleGroundGap();
    if (sustainedAirGap() && (healing || escaping) && t % 16 == 0)
      recoveryPoint = flightGapPoint();
    if (t % d.reaction == 0) {
      Vec3d point =
          owner
              .getEyePos()
              .subtract(0, owner.getHeight() * 0.12, 0)
              .add(owner.getVelocity().multiply(owner.isFallFlying() ? 1 : 0));
      double error =
          switch (d) {
            case LOW -> 0.20;
            case MEDIUM -> 0.15;
            case HIGH -> 0.09;
            case EXPERT -> 0.035;
          };
      error *= combatAimErrorScale();
      aimX = point.x + random.nextGaussian() * error;
      aimY = point.y + random.nextGaussian() * error;
      aimZ = point.z + random.nextGaussian() * error;
    }
    Vec3d aim = new Vec3d(aimX, aimY, aimZ);
    if (healing || escaping || landingForGap) {
      phase =
          landingForGap
              ? "Tank / descendo para gap"
              : escaping
                  ? "Buscando quina no alto"
                  : groundRecovery ? "Tank / gap no chao" : "Recuperando: " + gapsLeft + " gap";
      aim = recoveryPoint;
    } else if (o.tank) {
      phase = "Tank / evasao";
      double angle = Math.atan2(bot.getZ() - o.z, bot.getX() - o.x) + side * 0.6;
      double radius = o.size / 2.0 - 2;
      aim =
          new Vec3d(
              o.x + Math.cos(angle) * radius,
              o.y + Arena.HEIGHT - 2,
              o.z + Math.sin(angle) * radius);
    } else {
      phase = "Combate";
      if (webAtOwner() == null && t < maneuverUntil && dist > 9 && dist < 25) {
        Vec3d relative = bot.getPos().subtract(owner.getPos());
        double angle = Math.atan2(relative.z, relative.x) + side * 0.65;
        aim =
            clamp(
                new Vec3d(
                    owner.getX() + Math.cos(angle) * 2.2,
                    owner.getY() + 0.5,
                    owner.getZ() + Math.sin(angle) * 2.2));
        phase = "Reposicionando perto do alvo";
      }
    }

    BlockPos trapped = webAtOwner();
    // Low web traps are reachable at the feet from the floor; do not climb the cage.
    boolean lowWebTrap = trapped != null && owner.getY() <= o.y + 4;
    boolean elevatedWeb = !lowWebTrap && owner.getY() > o.y + 2.5
        && (trapped != null || owner.isOnGround());
    BlockPos elevatedTarget = trapped != null ? trapped : owner.getBlockPos();
    boolean feetTrappedTarget =
        trapped != null && !elevatedWeb && trapped.getY() <= owner.getBlockPos().getY();
    boolean headTrappedTarget = headWeb() != null && !elevatedWeb
        && bot.getY() <= owner.getY() + .5;
    boolean safeWebCombat = feetTrappedTarget || headTrappedTarget;
    if (headTrappedTarget && !healing && !escaping && !o.tank) {
      maneuverUntil = 0;
      bot.stopFallFlying();
      bot.setSneaking(false);
      if (bot.getPos().subtract(owner.getPos()).horizontalLengthSquared() < 4)
        brakeIntoWeb();
    }
    if (feetTrappedTarget && !healing && !escaping && !o.tank) {
      maneuverUntil = 0;
      aim = owner.getPos().add(0, owner.getHeight() * .65, 0);
      if (dist < 12 && bot.isFallFlying()) {
        bot.stopFallFlying();
        bot.setSneaking(false);
      }
    }

    if (!elevatedWeb) {
      webRoute = WebRoute.NONE;
      routeTarget = null;
      towerColumn = null;
    } else if (webRoute == WebRoute.NONE || !elevatedTarget.equals(routeTarget) || t >= routeUntil) {
      routeTarget = elevatedTarget;
      routeUntil = t + 140;
      webRoute = buildingSlot() < 0 || (trapped != null && (webRouteAttempts++ & 1) != 0)
          ? WebRoute.AIR : WebRoute.TOWER;
      towerColumn = webRoute == WebRoute.TOWER ? chooseTowerColumn() : null;
      if (webRoute == WebRoute.TOWER && towerColumn == null) webRoute = WebRoute.AIR;
      // Approaching the tower must not consume its placement timeout.
      towerProgressAt = 0;
    }
    if (!healing && !escaping && !o.tank) {
      if (!elevatedWeb && cageHead(t)) return;
      if (elevatedWeb) {
        if (webRoute == WebRoute.TOWER && !onTowerAtTarget()) {
          if (scaffold(t)) return;
          if (buildingSlot() < 0) webRoute = WebRoute.AIR;
        }
        if (webRoute == WebRoute.TOWER) {
          bot.stopFallFlying();
          bot.setSneaking(false);
          maneuverUntil = 0;
        }
        aim =
            webRoute == WebRoute.TOWER && bot.getY() < owner.getY() - 0.6
                ? new Vec3d(towerColumn == null ? owner.getX() : towerColumn.getX() + .5,
                    bot.getEyeY(), towerColumn == null ? owner.getZ() : towerColumn.getZ() + .5)
                : owner.getEyePos();
        phase = webRoute == WebRoute.TOWER ? "Aproximando para torre" : "Voando ate o alvo na teia";
      }
      if (breakTargetWeb() || (!(elevatedWeb && webRoute == WebRoute.TOWER) && breakBlockingWool())) return;
      if (headWeb() != null && !(elevatedWeb && webRoute == WebRoute.TOWER))
        aim = owner.getPos().add(0, Math.min(0.18, owner.getHeight() * 0.35), 0);
    }
    if (o.tank && !healing && !escaping && !landingForGap && breakBlockingWool()) return;
    look(aim, combatAimSpeed());
    bot.setHeadYaw(bot.getYaw());
    bot.setBodyYaw(bot.getYaw());
    bot.setSprinting(!healing);
    bot.forwardSpeed =
        healing && bot.isOnGround()
            ? 0.2f
            : healing || escaping || o.tank ? 1 : dist > 2.3 ? 1 : 0.15f;
    if (elevatedWeb && webRoute == WebRoute.TOWER && towerColumn != null) {
      double alignment = Math.hypot(bot.getX() - towerColumn.getX() - .5,
          bot.getZ() - towerColumn.getZ() - .5);
      bot.forwardSpeed = alignment < .8 ? .3f : 1;
    }
    if (o.strafe && !healing && !escaping && !elevatedWeb && !safeWebCombat && strafeActive)
      bot.sidewaysSpeed = side;
    if (o.wtap && !escaping && owner.getY() > bot.getY() + 1 && dist < 12 && t % 18 < 3)
      bot.forwardSpeed = 0;
    if (!groundRecovery && !headTrappedTarget && !(safeWebCombat && dist < 12)
        && !(elevatedWeb && webRoute == WebRoute.TOWER)
        && bot.isOnGround() && t >= jumpAt) {
      bot.jump();
      jumpAt = t + 8 + random.nextInt(4);
    } else if (!groundRecovery
        && !headTrappedTarget
        && !bot.isOnGround()
        && !bot.isFallFlying()
        && !(safeWebCombat && dist < 12)
        && !(elevatedWeb && webRoute == WebRoute.TOWER)
        && bot.getVelocity().y > -0.6
        && bot.getVelocity().y < 0.35) bot.checkFallFlying();
    if (headTrappedTarget && !healing && !escaping && !o.tank) {
      double horizontal = Math.sqrt(bot.getPos().subtract(owner.getPos()).horizontalLengthSquared());
      double upper = 1.9, lower = 1.5;
      if (owner.getY() - bot.getY() > 2.5) {
        double vertical = owner.getY() + Math.min(.18, owner.getHeight() * .35) - bot.getEyeY();
        upper = Math.min(upper, Math.max(.7, Math.sqrt(Math.max(0,
            attackReach() * attackReach() - vertical * vertical)) - .15));
        lower = Math.min(lower, Math.max(.5, upper - .25));
      }
      bot.forwardSpeed = horizontal < lower ? -.6f : horizontal > upper ? .7f : 0;
      bot.sidewaysSpeed = 0;
      bot.setSprinting(false);
      phase = "Mantendo distancia / atacando os pes";
    }
    // Match crouching to actual elytra flight, including the tick it starts.
    bot.setSneaking(bot.isFallFlying());
    if (escaping && bot.isFallFlying()) useRocket(t);
    if (healing && sustainedAirGap() && bot.isFallFlying()
        && bot.getRotationVec(1).dotProduct(recoveryPoint.subtract(bot.getEyePos()).normalize()) > .65
        && clearPath(recoveryPoint)) useRocket(t);
    if (elevatedWeb
        && webRoute == WebRoute.AIR
        && !healing
        && !escaping
        && !o.tank
        && bot.isFallFlying()
        && bot.getRotationVec(1).dotProduct(aim.subtract(bot.getEyePos()).normalize()) > 0.75)
      useRocket(t);
    boolean pursuit =
        (owner.isFallFlying() || owner.getY() > bot.getY() + 1.4 || otherEating)
            && dist > CombatPlan.meleeIntentRange(attackReach())
            && dist < 324;
    boolean near = dist >= 4 && dist < 30;
    if (o.giro
        && !safeWebCombat
        && bot.isFallFlying()
        && !healing
        && !escaping
        && !o.tank
        && t >= maneuverAt
        && (pursuit || near)
        && random.nextDouble() < o.spin.chance) {
      // Rocket follows the actual camera, so wait until it is facing the intended path.
      Vec3d path = aim.subtract(bot.getEyePos()).normalize();
      if (bot.getRotationVec(1).dotProduct(path) > 0.75 && clearPath(aim) && useRocket(t)) {
        maneuverUntil = t + 6;
        maneuverAt = t + o.spin.interval;
      }
    } else if (o.tank && o.giro && !healing && bot.isFallFlying()) useRocket(t);
    if (o.teia
        && !safeWebCombat
        && !(dist <= attackReach() * attackReach() && canHit())
        && t >= webAt
        && !healing
        && !escaping
        && placeWeb(BlockPos.ofFloored(owner.getEyePos()), t)) return;
    if (!o.tank && !healing && !escaping && heldUntil <= t) {
      int sword = selectSword();
      if (sword >= 0 && dist <= 36.0 && readyToAttack()) {
        bot.swingHand(Hand.MAIN_HAND);
        if (canHit()) attackOwner();
      }
    }
  }

  private Vec3d clamp(Vec3d p) {
    double h = o.size / 2.0 - 1.2;
    return new Vec3d(
        MathHelper.clamp(p.x, o.x - h, o.x + h),
        MathHelper.clamp(p.y, o.y + 0.7, o.y + Arena.HEIGHT - 1.2),
        MathHelper.clamp(p.z, o.z - h, o.z + h));
  }

  private boolean clearPath(Vec3d target) {
    return bot.getServerWorld()
            .raycast(
                new RaycastContext(
                    bot.getEyePos(),
                    target,
                    RaycastContext.ShapeType.COLLIDER,
                    RaycastContext.FluidHandling.NONE,
                    bot))
            .getType()
        == HitResult.Type.MISS;
  }

  private int apples() {
    int n = 0;
    for (int i = 0; i < 36; i++) {
      var s = bot.getInventory().getStack(i);
      if (s.isOf(Items.ENCHANTED_GOLDEN_APPLE) || s.isOf(Items.GOLDEN_APPLE)) n += s.getCount();
    }
    return n;
  }

  private boolean sustainedAirGap() {
    return airGap && !groundRecovery
        && (o.difficulty == Options.Difficulty.HIGH || o.difficulty == Options.Difficulty.EXPERT);
  }

  private Vec3d flightGapPoint() {
    Vec3d away = bot.getPos().subtract(owner.getPos());
    away = new Vec3d(away.x, 0, away.z);
    if (away.lengthSquared() < .01) away = new Vec3d(1, 0, 0);
    away = away.normalize();
    Vec3d tangent = new Vec3d(-away.z * side, 0, away.x * side);
    double height = MathHelper.clamp(bot.getY() + .8, o.y + 3.5, o.y + Arena.HEIGHT - 2);
    Vec3d target = clamp(bot.getPos().add(tangent.multiply(4)).add(away.multiply(1.5)));
    target = new Vec3d(target.x, height, target.z);
    if (target.subtract(bot.getPos()).horizontalLengthSquared() < 2 || !clearPath(target)) {
      side = -side;
      target = clamp(bot.getPos().subtract(tangent.multiply(4)).add(away));
      target = new Vec3d(target.x, height, target.z);
    }
    return target;
  }

  private void settleGroundGap() {
    if (!healing || !bot.isOnGround() || groundRecovery) return;
    if (sustainedAirGap() && clock < escapeUntil && !committedApple()) {
      bot.stopUsingItem();
      healing = false;
      escaping = true;
      return;
    }
    groundRecovery = true;
    airGap = false;
    escaping = false;
    double radius = Math.max(1, o.size / 2.0 - 2.0) * 0.7;
    recoveryPoint =
        new Vec3d(
            o.x + (bot.getX() >= o.x ? -radius : radius),
            o.y + 1.2,
            o.z + (bot.getZ() >= o.z ? -radius : radius));
  }

  private void startApple(int t) {
    if (sustainedAirGap() && !bot.isFallFlying()) {
      if (t < escapeUntil) {
        escaping = true;
        return;
      }
      // Missing/broken elytra or blocked takeoff must not leave the AI stuck.
      airGap = false;
      groundRecovery = true;
    }
    int slot = find(Items.ENCHANTED_GOLDEN_APPLE, true);
    if (slot < 0) slot = find(Items.GOLDEN_APPLE, true);
    if (slot < 0) {
      endRecovery(t, 40);
      return;
    }
    bot.getInventory().selectedSlot = slot;
    appleCountBefore = apples();
    bot.getMainHandStack().use(bot.getServerWorld(), bot, Hand.MAIN_HAND);
    healing = bot.isUsingItem();
    healingStartedAt = t;
    settleGroundGap();
    if (!healing) endRecovery(t, 30);
  }

  private void endRecovery(int t, int pause) {
    boolean wasRecovery = healing || escaping || landingForGap;
    if (wasRecovery && !o.tank) {
      attackCommitUntil = t + (countTotems() <= 2 ? 62 : 80);
      pause = Math.max(pause, countTotems() <= 2 ? 77 : 100);
    }
    bot.stopUsingItem();
    healing = false;
    escaping = false;
    landingForGap = false;
    if (groundRecovery && o.tank) tankGroundAt = t + 160 + random.nextInt(161);
    groundRecovery = false;
    gapsLeft = 0;
    finishAppleThenFight = false;
    gapWait = Math.max(gapWait, t + pause);
    selectSword();
  }

  private boolean retotem(int t) {
    if (swapAt >= 0) {
      phase = "Trocando offhand";
      if (t < swapAt) return true;
      ItemStack replacement = bot.getInventory().getStack(pendingSlot);
      boolean missed =
          replacement.isOf(Items.TOTEM_OF_UNDYING)
              && o.difficulty == Options.Difficulty.MEDIUM
              && random.nextDouble() < 0.20;
      if (replacement.isEmpty() || missed) {
        swapAt = -1;
        pendingSlot = -1;
        selectSword();
        retotemRetryAt = t + (missed ? o.difficulty.reaction : 1);
        if (missed) phase = "Retotem falhou / corrigindo";
        return true;
      }
      ItemStack off = bot.getOffHandStack();
      bot.getInventory().setStack(40, bot.getInventory().getStack(pendingSlot));
      bot.getInventory().setStack(pendingSlot, off);
      swapAt = -1;
      pendingSlot = -1;
      selectSword();
      bot.getInventory().markDirty();
      return true;
    }
    if (t < retotemRetryAt) return false;
    boolean protector = bot.getOffHandStack().isOf(Items.TOTEM_OF_UNDYING);
    boolean low = bot.getHealth() < Math.max(12, fullHealth * 0.45);
    boolean recovered = bot.getHealth() >= bot.getMaxHealth() * 0.82;
    int candidate = -1;
    if (countTotems() == 0 && !Kits.isCharm(bot.getOffHandStack())) {
      for (int i = 0; i < 36; i++) if (Kits.isCharm(bot.getInventory().getStack(i))) {
        candidate = i;
        break;
      }
    } else if (!protector && (low || bot.getOffHandStack().isEmpty()))
      candidate = find(Items.TOTEM_OF_UNDYING, false);
    else if (protector && recovered) {
      for (int i = 0; i < 36; i++)
        if (Kits.isCharm(bot.getInventory().getStack(i))) {
          candidate = i;
          break;
        }
    }
    if (candidate >= 0) {
      if (candidate >= 9) {
        int empty = -1;
        for (int i = 0; i < 9; i++)
          if (bot.getInventory().getStack(i).isEmpty()) {
            empty = i;
            break;
          }
        if (empty < 0) empty = 4;
        ItemStack old = bot.getInventory().getStack(empty);
        bot.getInventory().setStack(empty, bot.getInventory().getStack(candidate));
        bot.getInventory().setStack(candidate, old);
        candidate = empty;
      }
      endRecovery(t, 10);
      bot.getInventory().selectedSlot = candidate;
      pendingSlot = candidate;
      swapAt = t + o.difficulty.swapDelay;
      return true;
    }
    // Refill before losing the last offhand totem, not only after it pops.
    if (find(Items.TOTEM_OF_UNDYING, false) >= 0) {
      refillAt = -1;
      return false;
    }
    int reserve = -1;
    for (int i = 9; i < 36; i++)
      if (bot.getInventory().getStack(i).isOf(Items.TOTEM_OF_UNDYING)) {
        reserve = i;
        break;
      }
    if (reserve < 0) {
      refillAt = -1;
      return false;
    }
    phase = "Repondo 3 totens";
    bot.setSneaking(true);
    if (refillAt < 0) refillAt = t + o.difficulty.refillDelayTicks();
    if (t < refillAt) return true;
    int moved = 0;
    for (int target = 6; target <= 8; target++) {
      var displaced = bot.getInventory().getStack(target);
      if (displaced.isOf(Items.TOTEM_OF_UNDYING)) continue;
      int source = -1;
      for (int i = 9; i < 36; i++)
        if (bot.getInventory().getStack(i).isOf(Items.TOTEM_OF_UNDYING)) {
          source = i;
          break;
        }
      if (source < 0) break;
      // Swap rather than overwrite: even a full inventory keeps every displaced item.
      bot.getInventory().setStack(target, bot.getInventory().getStack(source));
      bot.getInventory().setStack(source, displaced);
      moved++;
    }
    refillAt = -1;
    if (moved > 0) {
      refillCount++;
      bot.getInventory().markDirty();
      return retotem(t);
    }
    return false;
  }

  private int find(Item item, boolean move) {
    for (int i = 0; i < 9; i++) if (bot.getInventory().getStack(i).isOf(item)) return i;
    if (move)
      for (int i = 9; i < 36; i++)
        if (bot.getInventory().getStack(i).isOf(item)) {
          int slot = 4;
          ItemStack previous = bot.getInventory().getStack(slot);
          bot.getInventory().setStack(slot, bot.getInventory().getStack(i));
          bot.getInventory().setStack(i, previous);
          return slot;
        }
    return -1;
  }

  private int selectSword() {
    for (int i = 0; i < 9; i++)
      if (bot.getInventory().getStack(i).isIn(net.minecraft.registry.tag.ItemTags.SWORDS)) {
        bot.getInventory().selectedSlot = i;
        return i;
      }
    return -1;
  }

  private void ensureSwordInHotbar() {
    if (selectSword() >= 0) return;
    for (int slot = 9; slot < 36; slot++)
      if (bot.getInventory().getStack(slot).isIn(net.minecraft.registry.tag.ItemTags.SWORDS)) {
        var previous = bot.getInventory().getStack(0);
        bot.getInventory().setStack(0, bot.getInventory().getStack(slot));
        bot.getInventory().setStack(slot, previous);
        bot.getInventory().selectedSlot = 0;
        return;
      }
  }

  private void look(Vec3d point, float max) {
    Vec3d delta = point.subtract(bot.getEyePos());
    float yaw = (float) Math.toDegrees(Math.atan2(-delta.x, delta.z));
    float pitch =
        (float)
            -Math.toDegrees(Math.atan2(delta.y, Math.sqrt(delta.x * delta.x + delta.z * delta.z)));
    bot.setYaw(Aim.approach(bot.getYaw(), yaw, max));
    bot.setPitch(MathHelper.clamp(Aim.approach(bot.getPitch(), pitch, max), -85, 85));
    bot.setHeadYaw(bot.getYaw());
    bot.setBodyYaw(bot.getYaw());
  }

  private boolean readyToAttack() {
    int selected = Options.allowedCps(o.cps) ? o.cps : 15;
    if (selected != clickRate) {
      clickRate = selected;
      clicks = new CpsCadence(clickRate);
    }
    return clicks.next()
        && (o.rules == Options.Rules.INSTA_KILL || bot.getAttackCooldownProgress(0.5f) >= 1.0f);
  }

  private void attackOwner() {
    bot.attack(owner);
  }

  public boolean opponentRecovering() {
    double distance = bot.squaredDistanceTo(owner);
    boolean gapping = owner.isUsingItem()
        && (owner.getActiveItem().isOf(Items.GOLDEN_APPLE)
            || owner.getActiveItem().isOf(Items.ENCHANTED_GOLDEN_APPLE));
    Vec3d away = owner.getPos().subtract(bot.getPos());
    return gapping && distance > 9 || distance > 25
        && owner.getVelocity().dotProduct(new Vec3d(away.x, 0, away.z).normalize()) > .03;
  }

  private float recoveryHealthTarget() {
    return countTotems() < 2 && !opponentRecovering() ? Math.min(25, bot.getMaxHealth()) : bot.getMaxHealth();
  }

  private double attackReach() {
    return Math.min(3.0, o.wtap ? 3.0 : 2.4);
  }

  private boolean canHit() {
    Vec3d start = bot.getEyePos(), end = start.add(bot.getRotationVec(1).multiply(attackReach()));
    var hit = owner.getBoundingBox().raycast(start, end);
    if (hit.isEmpty() && !owner.getBoundingBox().contains(start)) return false;
    Vec3d target = hit.orElse(start);
    return bot.getServerWorld()
            .raycast(
                new RaycastContext(
                    start,
                    target,
                    RaycastContext.ShapeType.OUTLINE,
                    RaycastContext.FluidHandling.NONE,
                    bot))
            .getType()
        == HitResult.Type.MISS;
  }

  private boolean useRocket(int t) {
    int slot = find(Items.FIREWORK_ROCKET, true);
    if (slot < 0 || t < rocketAt) return false;
    int previous = bot.getInventory().selectedSlot;
    bot.getInventory().selectedSlot = slot;
    bot.getMainHandStack().use(bot.getServerWorld(), bot, Hand.MAIN_HAND);
    bot.getInventory().selectedSlot = previous;
    rocketAt = t + o.spin.rocketDelay;
    return true;
  }

  private BlockPos webAtOwner() {
    return webAt(owner);
  }

  private boolean escapeOwnWeb(int t) {
    BlockPos web = webAt(bot);
    if (web == null) {
      webEscapeSince = -1;
      return false;
    }
    BlockPos head = BlockPos.ofFloored(bot.getEyePos());
    if (bot.isOnGround()
        && !bot.isFallFlying()
        && bot.getPose() == EntityPose.STANDING
        && bot.getServerWorld().getBlockState(head).isOf(net.minecraft.block.Blocks.COBWEB)) {
      breakTrainingBlock(head, "Liberando teia do rosto");
      return true;
    }
    // Feet-only webs and gliding webs never interrupt melee to mine.
    if (breakingWeb != null
        && bot.getServerWorld().getBlockState(breakingWeb).isOf(net.minecraft.block.Blocks.COBWEB))
      breakTrainingBlock(null, "Interrompendo mineracao para sair voando");
    Vec3d delta = owner.getPos().subtract(bot.getPos());
    if (delta.horizontalLengthSquared() < 0.25)
      delta = new Vec3d(o.x - bot.getX() + 1, 0, o.z - bot.getZ() + 1);
    Vec3d dir = new Vec3d(delta.x, 0, delta.z).normalize();
    look(clamp(bot.getPos().add(dir.multiply(3)).add(0, 0.6, 0)), o.difficulty.aimSpeed);
    bot.forwardSpeed = 1;
    bot.sidewaysSpeed = 0;
    if (bot.isOnGround()) bot.jump();
    else if (!bot.isFallFlying()) bot.checkFallFlying();
    bot.setSneaking(bot.isFallFlying());
    if (bot.isFallFlying()) useRocket(t);
    phase = "Tentando sair da teia";
    return false;
  }

  private BlockPos webAt(net.minecraft.entity.LivingEntity entity) {
    for (BlockPos p :
        BlockPos.iterate(
            BlockPos.ofFloored(
                entity.getBoundingBox().minX,
                entity.getBoundingBox().minY,
                entity.getBoundingBox().minZ),
            BlockPos.ofFloored(
                entity.getBoundingBox().maxX,
                entity.getBoundingBox().maxY,
                entity.getBoundingBox().maxZ)))
      if (bot.getServerWorld().getBlockState(p).isOf(net.minecraft.block.Blocks.COBWEB))
        return p.toImmutable();
    return null;
  }

  private BlockPos standingDoubleWebFeet() {
    BlockPos feet = owner.getBlockPos(), head = headWeb();
    return !owner.isFallFlying() && owner.getPose() == EntityPose.STANDING
        && head != null && head.getY() > feet.getY()
        && bot.getServerWorld().getBlockState(feet).isOf(net.minecraft.block.Blocks.COBWEB)
        ? feet : null;
  }

  private boolean breakTargetWeb() {
    BlockPos target = standingDoubleWebFeet();
    if (target != null && Math.abs(bot.getY() - owner.getY()) > 1.2) target = null;
    if (target == null && onTowerAtTarget()) target = webAtOwner();
    if (target == null) {
      BlockPos woolWork = breakingWeb != null ? breakingWeb : minePrepared;
      if (woolWork != null && bot.getServerWorld().getBlockState(woolWork)
          .isIn(net.minecraft.registry.tag.BlockTags.WOOL)) return false;
    }
    return breakTrainingBlock(target, "Quebrando teia do alvo");
  }

  private boolean breakBlockingWool() {
    var world = bot.getServerWorld();
    var ray =
        world.raycast(
            new RaycastContext(
                bot.getEyePos(),
                owner.getEyePos(),
                RaycastContext.ShapeType.OUTLINE,
                RaycastContext.FluidHandling.NONE,
                bot));
    BlockPos target = ray.getType() == HitResult.Type.BLOCK ? ray.getBlockPos() : null;
    if (target == null
        || !world.getBlockState(target).isIn(net.minecraft.registry.tag.BlockTags.WOOL))
      target = null;
    return breakTrainingBlock(target, "Quebrando la no caminho");
  }

  private void finishMining(int now) {
    breakingWeb = null;
    webBreakProgress = 0;
    mineStopSent = false;
    mineReadyAt = now + 8;
    minePrepared = null;
    selectSword();
  }

  private boolean breakTrainingBlock(BlockPos target, String label) {
    var world = bot.getServerWorld();
    int now = bot.getServer().getTicks();
    if (breakingWeb != null && world.getBlockState(breakingWeb).isAir()) finishMining(now);
    if (now < mineReadyAt) return false;
    boolean reachable =
        target != null
            && insideArena(target)
            && (world.getBlockState(target).isOf(net.minecraft.block.Blocks.COBWEB)
                || world.getBlockState(target).isIn(net.minecraft.registry.tag.BlockTags.WOOL))
            && bot.getEyePos().squaredDistanceTo(Vec3d.ofCenter(target)) < 20;
    boolean insideOwnHead =
        reachable
            && world.getBlockState(target).isOf(net.minecraft.block.Blocks.COBWEB)
            && target.equals(BlockPos.ofFloored(bot.getEyePos()))
            && bot.isOnGround()
            && !bot.isFallFlying()
            && bot.getPose() == EntityPose.STANDING;
    if (reachable && !insideOwnHead) {
      var ray =
          world.raycast(
              new RaycastContext(
                  bot.getEyePos(),
                  Vec3d.ofCenter(target),
                  RaycastContext.ShapeType.OUTLINE,
                  RaycastContext.FluidHandling.NONE,
                  bot));
      reachable = ray.getType() == HitResult.Type.BLOCK && ray.getBlockPos().equals(target);
    }
    if (breakingWeb != null && (!reachable || !breakingWeb.equals(target))) {
      bot.interactionManager.processBlockBreakingAction(
          breakingWeb,
          net.minecraft.network.packet.c2s.play.PlayerActionC2SPacket.Action.ABORT_DESTROY_BLOCK,
          Direction.UP,
          world.getTopY() - 1,
          0);
      breakingWeb = null;
      webBreakProgress = 0;
      mineStopSent = false;
    }
    if (!reachable) {
      minePrepared = null;
      selectSword();
      return false;
    }
    int shears = find(Items.SHEARS, true);
    if (shears >= 0) bot.getInventory().selectedSlot = shears;
    else selectSword();
    bot.forwardSpeed = 0;
    bot.sidewaysSpeed = 0;
    look(Vec3d.ofCenter(target), o.difficulty.aimSpeed);
    phase = label;
    Vec3d direction = Vec3d.ofCenter(target).subtract(bot.getEyePos()).normalize();
    if (bot.getRotationVec(1).dotProduct(direction) < 0.98) return true;
    if (breakingWeb == null) {
      if (!target.equals(minePrepared)) {
        minePrepared = target.toImmutable();
        minePrepareAt = now + 4;
      }
      if (now < minePrepareAt) return true;
      breakingWeb = target;
      breakStartedAt = now;
      mineStopSent = false;
      bot.interactionManager.processBlockBreakingAction(
          target,
          net.minecraft.network.packet.c2s.play.PlayerActionC2SPacket.Action.START_DESTROY_BLOCK,
          Direction.UP,
          world.getTopY() - 1,
          0);
    }
    bot.swingHand(Hand.MAIN_HAND);
    if (world.getBlockState(target).isAir()) {
      finishMining(now);
      return true;
    }
    webBreakProgress =
        world.getBlockState(target).calcBlockBreakingDelta(bot, world, target)
            * (now - breakStartedAt + 1);
    if (!mineStopSent && webBreakProgress >= 1) {
      bot.interactionManager.processBlockBreakingAction(
          target,
          net.minecraft.network.packet.c2s.play.PlayerActionC2SPacket.Action.STOP_DESTROY_BLOCK,
          Direction.UP,
          world.getTopY() - 1,
          0);
      mineStopSent = true;
      if (world.getBlockState(target).isAir()) finishMining(now);
    }
    return true;
  }

  private boolean onTowerAtTarget() {
    return webRoute == WebRoute.TOWER
        && bot.isOnGround()
        && bot.getY() >= owner.getY() - 0.6
        && builtBlocks.containsKey(bot.getBlockPos().down());
  }

  private int buildingSlot() {
    // Prefer any wool color, including stacks in the reserve inventory. Decorative
    // map/chest blocks must never be consumed as disposable scaffolding.
    for (int pass = 0; pass < 2; pass++)
      for (int i = 0; i < 36; i++) {
        var stack = bot.getInventory().getStack(i);
        if (stack.getItem() instanceof BlockItem block
            && !(block.getBlock() instanceof net.minecraft.block.BlockEntityProvider)
            && (pass == 0
                ? block.getBlock().getDefaultState().isIn(net.minecraft.registry.tag.BlockTags.WOOL)
                : false))
          return find(stack.getItem(), true);
      }
    return -1;
  }

  public boolean isTrainingBlock(BlockPos pos) {
    return builtBlocks.containsKey(pos);
  }

  private BlockPos headWeb() {
    BlockPos pos = BlockPos.ofFloored(owner.getEyePos());
    return bot.getServerWorld().getBlockState(pos).isOf(net.minecraft.block.Blocks.COBWEB)
        ? pos
        : null;
  }

  private boolean cageHead(int t) {
    if (bot.getY() > owner.getY() + .5) return false;
    BlockPos head = headWeb();
    if (head == null) {
      trappedHead = null;
      cageIndex = 0;
      return false;
    }
    if (!head.equals(trappedHead)) {
      trappedHead = head;
      headWebSince = t;
      cageIndex = 0;
    }
    if (t - headWebSince < 60 || t < cageAt || cageIndex >= 5) return false;
    Direction dir =
        new Direction[] {
              Direction.UP, Direction.NORTH, Direction.SOUTH, Direction.WEST, Direction.EAST
            }
            [cageIndex];
    BlockPos pos = head.offset(dir);
    if (!insideArena(pos) || !bot.getServerWorld().getBlockState(pos).isAir()) {
      cageIndex++;
      return false;
    }
    if (bot.getEyePos().squaredDistanceTo(Vec3d.ofCenter(pos)) > 9 || buildingSlot() < 0)
      return false;
    if (placeBuildingBlock(pos)) {
      cageIndex++;
      cageAt = t + 8;
      heldUntil = t + 2;
      return true;
    }
    // An entity occupying this side must not stall the other faces forever.
    cageIndex++;
    return false;
  }

  private boolean insideArena(BlockPos pos) {
    return Math.abs(pos.getX() - o.x) < o.size / 2
        && Math.abs(pos.getZ() - o.z) < o.size / 2
        && pos.getY() > o.y
        && pos.getY() <= o.y + Arena.HEIGHT;
  }

  private boolean placeBuildingBlock(BlockPos pos) {
    int slot = buildingSlot();
    if (slot < 0 || !insideArena(pos)) return false;
    var w = bot.getServerWorld();
    for (Direction dir : Direction.values()) {
      BlockPos support = pos.offset(dir);
      if (w.getBlockState(support).isAir()) continue;
      Vec3d face = Vec3d.ofCenter(support).subtract(Vec3d.of(dir.getVector()).multiply(0.499));
      var ray =
          w.raycast(
              new RaycastContext(
                  bot.getEyePos(),
                  face,
                  RaycastContext.ShapeType.OUTLINE,
                  RaycastContext.FluidHandling.NONE,
                  bot));
      if (ray.getType() != HitResult.Type.BLOCK || !ray.getBlockPos().equals(support)) continue;
      int previous = bot.getInventory().selectedSlot;
      bot.getInventory().selectedSlot = slot;
      look(face, 180);
      var result =
          bot.interactionManager.interactBlock(
              bot,
              w,
              bot.getMainHandStack(),
              Hand.MAIN_HAND,
              new BlockHitResult(face, dir.getOpposite(), support, false));
      bot.getInventory().selectedSlot = previous;
      if (result.isAccepted() && !w.getBlockState(pos).isAir()) {
        builtBlocks.put(pos.toImmutable(), w.getBlockState(pos));
        bot.swingHand(Hand.MAIN_HAND);
        return true;
      }
    }
    return false;
  }

  private BlockPos chooseTowerColumn() {
    BlockPos best = null;
    double nearest = Double.MAX_VALUE;
    // Stand beside the web, not underneath the opponent or inside its collision box.
    for (Direction side : Direction.Type.HORIZONTAL) {
      BlockPos candidate = owner.getBlockPos().offset(side).withY(o.y + 1);
      if (!insideArena(candidate)) continue;
      var world = bot.getServerWorld();
      if (!world.getBlockState(candidate.down()).isSideSolidFullSquare(world, candidate.down(), Direction.UP))
        continue;
      boolean clear = true;
      for (int y = candidate.getY(); y <= owner.getBlockY() + 1; y++) {
        var state = world.getBlockState(candidate.withY(y));
        if (!state.isAir() && !builtBlocks.containsKey(candidate.withY(y))
            && !state.isIn(net.minecraft.registry.tag.BlockTags.WOOL)
            && !state.isOf(net.minecraft.block.Blocks.COBWEB)
            && y < owner.getBlockY() - 1) {
          clear = false;
          break;
        }
      }
      double distance = bot.getPos().squaredDistanceTo(Vec3d.ofCenter(candidate));
      if (clear && distance < nearest) {
        best = candidate;
        nearest = distance;
      }
    }
    return best;
  }

  private boolean clearTowerWool(int t, double horizontalDistance) {
    if (towerColumn == null || horizontalDistance > 9) return false;
    var world = bot.getServerWorld();
    java.util.List<BlockPos> candidates = new java.util.ArrayList<>();
    if (horizontalDistance > .16) {
      candidates.add(new BlockPos(towerColumn.getX(), bot.getBlockY(), towerColumn.getZ()));
      candidates.add(new BlockPos(towerColumn.getX(), bot.getBlockY() + 1, towerColumn.getZ()));
    }
    candidates.add(bot.getBlockPos().up());
    candidates.add(bot.getBlockPos().up(2));
    for (BlockPos pos : candidates) {
      if (!world.getBlockState(pos).isIn(net.minecraft.registry.tag.BlockTags.WOOL)
          || pos.equals(bot.getBlockPos().down())
          || pos.equals(owner.getBlockPos().down()) && bot.getY() < owner.getY() - .6) continue;
      if (breakTrainingBlock(pos, "Liberando la / retomando a torre")) {
        towerProgressAt = t;
        routeUntil = t + 140;
        return true;
      }
    }
    return false;
  }

  private boolean scaffold(int t) {
    if (webAtOwner() != null && owner.getY() <= o.y + 4) return false;
    double dx = owner.getX() - bot.getX(), dz = owner.getZ() - bot.getZ();
    if (towerColumn != null) {
      dx = towerColumn.getX() + .5 - bot.getX();
      dz = towerColumn.getZ() + .5 - bot.getZ();
    }
    if (towerColumn != null && dx * dx + dz * dz <= 9) {
      bot.stopFallFlying(); bot.setSneaking(false);
    }
    if (clearTowerWool(t, dx * dx + dz * dz)) return true;
    if (dx * dx + dz * dz > (towerColumn == null ? 2.0 : .16)
        || (bot.isOnGround() && bot.getY() >= owner.getY() - 0.6))
      return false;
    BlockPos place = bot.getBlockPos().down();
    if (place.getY() < o.y || place.getY() > o.y + Arena.HEIGHT) return false;
    int slot = buildingSlot();
    if (slot < 0) return false;
    if (towerProgressAt == 0) towerProgressAt = t;
    if (t - towerProgressAt > 60) {
      webRoute = WebRoute.AIR;
      routeUntil = t + 100;
      return false;
    }
    bot.stopFallFlying();
    bot.setSneaking(false);
    bot.forwardSpeed = 0;
    bot.sidewaysSpeed = 0;
    bot.setVelocity(new Vec3d(0, bot.getVelocity().y, 0));
    phase = "Subindo com blocos";
    if (bot.isOnGround()) bot.jump();
    if (t < buildAt || !bot.getServerWorld().getBlockState(place).isAir()) return true;
    BlockPos support = place.down();
    if (!bot.getServerWorld().getBlockState(support)
        .isSideSolidFullSquare(bot.getServerWorld(), support, Direction.UP))
      return true;
    Vec3d face = Vec3d.ofCenter(support).add(0, 0.5, 0);
    look(face, 180);
    int previous = bot.getInventory().selectedSlot;
    bot.getInventory().selectedSlot = slot;
    var result =
        bot.interactionManager.interactBlock(
            bot,
            bot.getServerWorld(),
            bot.getMainHandStack(),
            Hand.MAIN_HAND,
            new BlockHitResult(face, Direction.UP, support, false));
    bot.getInventory().selectedSlot = previous;
    if (result.isAccepted() && !bot.getServerWorld().getBlockState(place).isAir()) {
      builtBlocks.put(place.toImmutable(), bot.getServerWorld().getBlockState(place));
      buildAt = t + 4;
      towerProgressAt = t;
      routeUntil = t + 140;
      bot.swingHand(Hand.MAIN_HAND);
    }
    return true;
  }

  public void cleanupBuilding() {
    for (var entry : builtBlocks.entrySet())
      if (bot.getServerWorld().getBlockState(entry.getKey()).equals(entry.getValue()))
        bot.getServerWorld()
            .setBlockState(entry.getKey(), net.minecraft.block.Blocks.AIR.getDefaultState(), 3);
    builtBlocks.clear();
  }

  private void trackTotemPops(int t) {
    int own = owner.getStatHandler().getStat(net.minecraft.stat.Stats.USED, Items.TOTEM_OF_UNDYING);
    int mine = bot.getStatHandler().getStat(net.minecraft.stat.Stats.USED, Items.TOTEM_OF_UNDYING);
    if (own > ownerTotemUses) lastOwnerPopAt = t;
    if (mine > botTotemUses) lastBotPopAt = t;
    ownerTotemUses = own;
    botTotemUses = mine;
  }

  private boolean footCampAllowed(int t) {
    trackTotemPops(t);
    double disadvantage = Aim.fraction(owner.getHealth(), owner.getMaxHealth())
        - Aim.fraction(bot.getHealth(), bot.getMaxHealth());
    return disadvantage <= .10 || t - lastOwnerPopAt <= 60 && t - lastBotPopAt <= 60;
  }

  /** Ground-only web dueling: keep native reach/CPS and native mining when leaving. */
  private boolean footWebFight(int t, double distance) {
    var world = bot.getServerWorld();
    boolean viable = footCampAllowed(t) && !healing && !escaping && !landingForGap;
    if (plantedFootWeb != null
        && (!world.getBlockState(plantedFootWeb).isOf(net.minecraft.block.Blocks.COBWEB)
            || !bot.getBoundingBox().intersects(new Box(plantedFootWeb)))) {
      plantedFootWeb = null;
      leavingFootWeb = false;
      footRetryAt = t + 60;
    }
    if (plantedFootWeb != null
        && (!viable || !o.footWeb
            || !o.teia
            || !bot.isOnGround()
            || bot.isFallFlying()
            || distance > 25
            || Math.abs(owner.getY() - bot.getY()) > 2.0)) leavingFootWeb = true;
    if (plantedFootWeb != null && leavingFootWeb) {
      plantedFootWeb = null;
      leavingFootWeb = false;
      footRetryAt = t + 60;
      return false;
    }
    if (plantedFootWeb == null) {
      if (leavingFootWeb) return false;
      if (!viable || !o.footWeb
          || !o.teia
          || !bot.isOnGround()
          || distance > attackReach() * attackReach()
          || t < footRetryAt) return false;
      boolean losing =
          Aim.fraction(bot.getHealth(), bot.getMaxHealth())
              < Aim.fraction(owner.getHealth(), owner.getMaxHealth());
      BlockPos feet = bot.getBlockPos();
      boolean alreadyWebbed = world.getBlockState(feet).isOf(net.minecraft.block.Blocks.COBWEB);
      if (!alreadyWebbed && !owner.isOnGround() && distance <= 9 && !losing) return false;
      if (!alreadyWebbed && !placeWebAt(feet, t, true)) {
        footRetryAt = t + 10;
        return false;
      }
      plantedFootWeb = feet.toImmutable();
      footAttackWebAt = t + 20;
      if (healing || escaping || landingForGap) endRecovery(t, 20);
    }
    bot.stopFallFlying();
    bot.setSneaking(false);
    bot.setSprinting(false);
    bot.forwardSpeed = bot.sidewaysSpeed = 0;
    phase = "Teia no pe / combate";
    look(owner.getEyePos(), o.difficulty.aimSpeed);
    bot.setHeadYaw(bot.getYaw());
    bot.setBodyYaw(bot.getYaw());
    if (owner.isOnGround() && distance <= 9 && t >= footAttackWebAt) {
      footAttackWebAt = t + 40;
      if (placeWebAt(owner.getBlockPos(), t, true)) return true;
    }
    if (selectSword() >= 0 && heldUntil <= t && distance <= 36 && readyToAttack()) {
      bot.swingHand(Hand.MAIN_HAND);
      if (canHit()) attackOwner();
    }
    return true;
  }

  private void brakeIntoWeb() {
    Vec3d toward = owner.getPos().subtract(bot.getPos());
    toward = new Vec3d(toward.x, 0, toward.z).normalize();
    double inward = bot.getVelocity().dotProduct(toward);
    if (inward > 0) bot.setVelocity(bot.getVelocity().subtract(toward.multiply(inward)));
  }

  private boolean placeWeb(BlockPos pos, int t) {
    return placeWebAt(pos, t, false);
  }

  private boolean placeWebAt(BlockPos pos, int t, boolean feet) {
    if (!bot.isOnGround()
        || (feet
            ? !(pos.equals(bot.getBlockPos()) || pos.equals(owner.getBlockPos()))
                || pos.getY() < o.y + 1
                || pos.getY() > o.y + 2
            : !pos.equals(BlockPos.ofFloored(owner.getEyePos()))
                || pos.getY() <= owner.getBlockPos().getY()
                || pos.getY() < o.y + 2
                || pos.getY() > o.y + 3)
        || !feet && new Box(pos).intersects(bot.getBoundingBox().expand(.1))
        || !bot.getServerWorld().getBlockState(pos).isAir()
        || bot.getEyePos().squaredDistanceTo(Vec3d.ofCenter(pos)) > 9) return false;
    int slot = find(Items.COBWEB, true);
    if (slot < 0) return false;
    for (Direction dir : Direction.values()) {
      BlockPos support = pos.offset(dir);
      if (!bot.getServerWorld().getBlockState(support)
        .isSideSolidFullSquare(bot.getServerWorld(), support, Direction.UP))
        continue;
      Vec3d face = Vec3d.ofCenter(support).subtract(Vec3d.of(dir.getVector()).multiply(0.499));
      var ray =
          bot.getServerWorld()
              .raycast(
                  new RaycastContext(
                      bot.getEyePos(),
                      face,
                      RaycastContext.ShapeType.COLLIDER,
                      RaycastContext.FluidHandling.NONE,
                      bot));
      if (ray.getType() != HitResult.Type.BLOCK || !ray.getBlockPos().equals(support)) continue;
      look(face, 180);
      bot.getInventory().selectedSlot = slot;
      var result =
          bot.interactionManager.interactBlock(
              bot,
              bot.getServerWorld(),
              bot.getMainHandStack(),
              Hand.MAIN_HAND,
              new BlockHitResult(face, dir.getOpposite(), support, false));
      if (result.isAccepted()
          && bot.getServerWorld().getBlockState(pos).isOf(net.minecraft.block.Blocks.COBWEB)) {
        if (!feet) {
          webAt = t + o.webCooldown;
          maneuverUntil = 0;
          bot.forwardSpeed = bot.sidewaysSpeed = 0;
          brakeIntoWeb();
        }
        heldUntil = t + 2;
        bot.swingHand(Hand.MAIN_HAND);
        return true;
      }
    }
    return false;
  }

  public String roundMessage(boolean playerWon) {
    if (playerWon) {
      int remaining = 0;
      for (int i = 0; i < owner.getInventory().size(); i++)
        if (owner.getInventory().getStack(i).isOf(Items.TOTEM_OF_UNDYING))
          remaining += owner.getInventory().getStack(i).getCount();
      String[] lines =
          remaining <= 2
              ? new String[] {
                "Seloko, jogou muito!",
                "Quaseee! Mandou bem!",
                "Foi por pouco! GG!",
                "Essa foi no ultimo suspiro!",
                "Que luta! Mandou demais!",
                "Acabou no detalhe! GG!"
              }
              : new String[] {
                "GG! Jogou bem!",
                "Boa! Bora mais uma?",
                "Mandou bem nessa!",
                "Voce leu meu jogo!",
                "Bela mira! GG!",
                "Boa troca de hits!"
              };
      return lines[random.nextInt(lines.length)];
    }
    String[] lines = {
      "GG, foi bem!",
      "Boa luta! Bora de novo?",
      "Quase! Na proxima voce leva!",
      "Essa foi disputada!",
      "GG! Vamos outra?",
      "Treino bom! Continua assim!"
    };
    return lines[random.nextInt(lines.length)];
  }

  public Text statusText() {
    var text =
        Text.empty()
            .append(Text.literal("◆ DuckBox").formatted(Formatting.GOLD, Formatting.BOLD))
            .append(Text.literal("  » ").formatted(Formatting.DARK_GRAY))
            .append(Text.literal(o.difficulty.toString()).formatted(Formatting.AQUA))
            .append(Text.literal(" | ").formatted(Formatting.DARK_GRAY))
            .append(Text.literal(o.rules.toString()).formatted(Formatting.YELLOW))
            .append(Text.literal(" | ").formatted(Formatting.DARK_GRAY))
            .append(Text.literal("◇ Totens " + countTotems()).formatted(Formatting.GREEN));
    return text;
  }

  public void status() {
    if (bot.getServer().getTicks() < settingsVisibleUntil) return;
    if (countingDown() ? countdownTicks % 10 != 0 : clock % 10 != 0) return;
    owner.sendMessage(statusText(), true);
  }

  public int countTotems() {
    int n = 0;
    for (int i = 0; i < bot.getInventory().size(); i++)
      if (Kits.isTotem(bot.getInventory().getStack(i)))
        n += bot.getInventory().getStack(i).getCount();
    return n;
  }
}
