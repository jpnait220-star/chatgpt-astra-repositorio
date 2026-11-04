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
  private final CpsCadence clicks = new CpsCadence(15);
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
  private int side = 1, damageCount, gapsLeft, healingStartedAt, appleCountBefore, escapeUntil;
  private float lastHealth, fullHealth;
  private boolean healing, escaping, airGap, strafeActive;
  private String phase = "Preparando";
  private Vec3d recoveryPoint;
  private double aimX, aimY, aimZ;

  public Session(ServerPlayerEntity p, TrainingBot b, Options options) {
    owner = p;
    bot = b;
    o = options;
    b.session = this;
    lastHealth = b.getHealth() + b.getAbsorptionAmount();
    aimX = p.getX();
    aimY = p.getEyeY();
    aimZ = p.getZ();
  }

  public void maintainRules() {
    int amplifier = o.rules == Options.Rules.NORMAL_SPAM ? 1 : 0;
    for (var p : List.of(owner, bot)) {
      var effect = p.getStatusEffect(StatusEffects.RESISTANCE);
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
    int t = (int) ++clock;
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
    bot.setSneaking(bot.isGliding());
    if (t == 2 || t == 3) {
      bot.setHealth(bot.getMaxHealth());
      owner.setHealth(owner.getMaxHealth());
    }
    fullHealth = Math.max(fullHealth, bot.getMaxHealth());
    double dist = bot.squaredDistanceTo(owner);
    float health = bot.getHealth();
    if (t % 30 == 0 && random.nextBoolean()) side = -side;
    if (t % d.reaction == 0) strafeActive = random.nextDouble() < d.strafe;
    float vitality = health + bot.getAbsorptionAmount();
    if (vitality < lastHealth) {
      damageCount++;
      if ((healing || escaping) && damageCount >= 2) endRecovery(t, 45);
    } else if (t % 40 == 0) damageCount = 0;
    lastHealth = vitality;
    if (o.retotem && retotem(t)) return;
    if (heldUntil > t) {
      phase = "Trocando item";
      return;
    }
    if (heldUntil != 0) {
      heldUntil = 0;
      selectSword();
    }
    if (Math.abs(owner.getX() - o.x) > o.size / 2.0 + 3
        || Math.abs(owner.getZ() - o.z) > o.size / 2.0 + 3
        || owner.getY() < o.y - 3
        || owner.getY() > o.y + Arena.HEIGHT + 3) {
      finish = "Voce saiu da arena.";
      return;
    }
    // A consumed apple decreases the real inventory count; interruption does not.
    if (healing && !bot.isUsingItem()) {
      if (apples() < appleCountBefore) gapsLeft--;
      if (gapsLeft > 0 && health < bot.getMaxHealth() - 2) startApple(t);
      else endRecovery(t, 30);
    }
    if (healing && t - healingStartedAt > 45) endRecovery(t, 35);
    boolean behind =
        Aim.fraction(health, bot.getMaxHealth()) + 0.12
            < Aim.fraction(owner.getHealth(), owner.getMaxHealth());
    boolean otherEating =
        owner.isUsingItem()
            && owner.getActiveItem().contains(net.minecraft.component.DataComponentTypes.FOOD);
    if (!healing
        && !escaping
        && gapsLeft == 0
        && o.gap
        && t > gapWait
        && health < bot.getMaxHealth() - 4
        && (behind || otherEating || o.tank || health < bot.getMaxHealth() * 0.55)
        && apples() > 0) {
      gapsLeft = health < bot.getMaxHealth() * 0.65 ? 2 : 1;
      damageCount = 0;
      airGap = o.giro && random.nextDouble() < 0.65;
      double radius = o.size / 2.0 - 1.8;
      recoveryPoint =
          new Vec3d(
              o.x + (random.nextBoolean() ? radius : -radius),
              o.y + (airGap ? Arena.HEIGHT - 1.6 : 1.2),
              o.z + (random.nextBoolean() ? radius : -radius));
      escaping = airGap;
      escapeUntil = t + 26;
      if (!escaping) startApple(t);
    }
    if (escaping && (bot.getY() > o.y + 2.8 || t >= escapeUntil)) {
      escaping = false;
      startApple(t);
    }
    if (t % d.reaction == 0) {
      Vec3d point =
          owner
              .getEyePos()
              .subtract(0, owner.getHeight() * 0.12, 0)
              .add(owner.getVelocity().multiply(owner.isGliding() ? 1 : 0));
      double error =
          switch (d) {
            case LOW -> 0.20;
            case MEDIUM -> 0.15;
            case HIGH -> 0.09;
            case EXPERT -> 0.035;
          };
      aimX = point.x + random.nextGaussian() * error;
      aimY = point.y + random.nextGaussian() * error;
      aimZ = point.z + random.nextGaussian() * error;
    }
    Vec3d aim = new Vec3d(aimX, aimY, aimZ);
    if (healing || escaping) {
      phase = escaping ? "Buscando quina no alto" : "Recuperando: " + gapsLeft + " gap";
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
      if (t < maneuverUntil && dist > 9 && dist < 25) {
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

    look(aim, d.aimSpeed);
    bot.setHeadYaw(bot.getYaw());
    bot.setBodyYaw(bot.getYaw());
    bot.setSprinting(!healing);
    bot.forwardSpeed = healing || escaping || o.tank ? 1 : dist > 2.3 ? 1 : 0.15f;
    if (o.strafe && !healing && !escaping && strafeActive) bot.sidewaysSpeed = side;
    if (o.wtap && !escaping && owner.getY() > bot.getY() + 1 && dist < 12 && t % 18 < 3)
      bot.forwardSpeed = 0;
    if (bot.isOnGround() && t >= jumpAt) {
      bot.jump();
      jumpAt = t + 8 + random.nextInt(4);
    } else if (!bot.isOnGround()
        && !bot.isGliding()
        && bot.getVelocity().y > -0.6
        && bot.getVelocity().y < 0.35) bot.checkGliding();
    // Match crouching to actual elytra flight, including the tick it starts.
    bot.setSneaking(bot.isGliding());
    if (escaping && bot.isGliding()) useRocket(t);
    boolean pursuit =
        (owner.isGliding() || owner.getY() > bot.getY() + 1.4 || otherEating)
            && dist > CombatPlan.meleeIntentRange(bot.getEntityInteractionRange())
            && dist < 324;
    boolean near = dist >= 4 && dist < 30;
    if (o.giro
        && bot.isGliding()
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
    } else if (o.tank && o.giro && !healing && bot.isGliding()) useRocket(t);
    if (o.teia
        && t >= webAt
        && !healing
        && !escaping
        && placeWeb(o.tank ? bot.getBlockPos().down() : owner.getBlockPos().up(), t)) return;
    if (!o.tank && !healing && !escaping && heldUntil <= t) {
      int sword = selectSword();
      if (sword >= 0
          && dist < CombatPlan.meleeIntentRange(bot.getEntityInteractionRange())
          && clicks.next()) {
        bot.swingHand(Hand.MAIN_HAND);
        if (canHit()) bot.attack(owner);
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

  private void startApple(int t) {
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
    if (!healing) endRecovery(t, 30);
  }

  private void endRecovery(int t, int pause) {
    bot.stopUsingItem();
    healing = false;
    escaping = false;
    gapsLeft = 0;
    gapWait = t + pause;
    selectSword();
  }

  private boolean retotem(int t) {
    if (swapAt >= 0) {
      phase = "Trocando offhand";
      if (t < swapAt) return true;
      ItemStack off = bot.getOffHandStack();
      bot.getInventory().setStack(40, bot.getInventory().getStack(pendingSlot));
      bot.getInventory().setStack(pendingSlot, off);
      swapAt = -1;
      pendingSlot = -1;
      selectSword();
      bot.getInventory().markDirty();
      return true;
    }
    boolean protector = bot.getOffHandStack().isOf(Items.TOTEM_OF_UNDYING);
    boolean low = bot.getHealth() < Math.max(12, fullHealth * 0.45);
    boolean recovered = bot.getHealth() >= bot.getMaxHealth() * 0.82;
    int candidate = -1;
    if (!protector && (low || bot.getOffHandStack().isEmpty()))
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
    if (protector || (!low && !bot.getOffHandStack().isEmpty())) return false;
    int reserve = -1;
    for (int i = 9; i < 36; i++)
      if (bot.getInventory().getStack(i).isOf(Items.TOTEM_OF_UNDYING)) {
        reserve = i;
        break;
      }
    if (reserve < 0) return false;
    phase = "Repondo3totems";
    bot.setSneaking(true);
    if (refillAt < 0) refillAt = t + o.difficulty.reaction + 4;
    if (t < refillAt) return true;
    for (int slot = 6; slot <= 8; slot++)
      if (Kits.isCharm(bot.getInventory().getStack(slot))) {
        for (int free = 9; free < 36; free++)
          if (bot.getInventory().getStack(free).isEmpty()) {
            bot.getInventory().setStack(free, bot.getInventory().getStack(slot));
            bot.getInventory().setStack(slot, ItemStack.EMPTY);
            break;
          }
      }
    for (int target = 6; target <= 8; target++)
      if (bot.getInventory().getStack(target).isEmpty())
        for (int i = 9; i < 36; i++)
          if (bot.getInventory().getStack(i).isOf(Items.TOTEM_OF_UNDYING)) {
            bot.getInventory().setStack(target, bot.getInventory().getStack(i));
            bot.getInventory().setStack(i, ItemStack.EMPTY);
            break;
          }
    // With a packed custom hotbar, exchange a reserve totem with a non-sword slot instead of
    // deleting an item.
    if (find(Items.TOTEM_OF_UNDYING, false) < 0) {
      int slot = 8;
      ItemStack previous = bot.getInventory().getStack(slot);
      bot.getInventory().setStack(slot, bot.getInventory().getStack(reserve));
      bot.getInventory().setStack(reserve, previous);
    }
    refillAt = -1;
    bot.getInventory().markDirty();
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

  private void look(Vec3d point, float max) {
    Vec3d delta = point.subtract(bot.getEyePos());
    float yaw = (float) Math.toDegrees(Math.atan2(-delta.x, delta.z));
    float pitch =
        (float)
            -Math.toDegrees(Math.atan2(delta.y, Math.sqrt(delta.x * delta.x + delta.z * delta.z)));
    bot.setYaw(Aim.approach(bot.getYaw(), yaw, max));
    bot.setPitch(MathHelper.clamp(Aim.approach(bot.getPitch(), pitch, max), -85, 85));
  }

  private boolean canHit() {
    Vec3d start = bot.getEyePos(),
        end = start.add(bot.getRotationVec(1).multiply(bot.getEntityInteractionRange()));
    var hit = owner.getBoundingBox().raycast(start, end);
    if (hit.isEmpty() && !owner.getBoundingBox().contains(start)) return false;
    Vec3d target = hit.orElse(start);
    return bot.getServerWorld()
            .raycast(
                new RaycastContext(
                    start,
                    target,
                    RaycastContext.ShapeType.COLLIDER,
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

  private boolean placeWeb(BlockPos pos, int t) {
    if (!bot.getServerWorld().getBlockState(pos).isAir()
        || bot.getEyePos().squaredDistanceTo(Vec3d.ofCenter(pos)) > 20) return false;
    int slot = find(Items.COBWEB, true);
    if (slot < 0) return false;
    for (Direction dir : Direction.values()) {
      BlockPos support = pos.offset(dir);
      if (bot.getServerWorld().getBlockState(support).isAir()) continue;
      Vec3d face = Vec3d.ofCenter(support).subtract(Vec3d.of(dir.getVector()).multiply(0.501));
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
      if (result.isAccepted()) {
        webAt = t + o.webCooldown;
        heldUntil = t + 2;
        bot.swingHand(Hand.MAIN_HAND);
        return true;
      }
    }
    return false;
  }

  public void status() {
    if (clock % 10 != 0) return;
    owner.sendMessage(
        Text.literal(
            "DuckBox | "
                + o.difficulty
                + " | "
                + o.rules
                + " | "
                + phase
                + " | Bot "
                + Math.round(bot.getHealth())
                + "/"
                + Math.round(bot.getMaxHealth())
                + " | Totems "
                + countTotems()),
        true);
  }

  public int countTotems() {
    int n = 0;
    for (int i = 0; i < bot.getInventory().size(); i++)
      if (Kits.isTotem(bot.getInventory().getStack(i)))
        n += bot.getInventory().getStack(i).getCount();
    return n;
  }
}
