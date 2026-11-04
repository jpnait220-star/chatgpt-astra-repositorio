package dev.duckbox;

import java.util.*;
import net.minecraft.entity.*;
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
  private int attackAt,
      rocketAt,
      webAt,
      jumpAt,
      maneuverUntil,
      maneuverAt = 40,
      healingStartedAt,
      swapAt = -1,
      refillAt = -1,
      gapWait,
      heldUntil;
  private int side = 1, damageCount;
  private float lastHealth;
  private boolean healing, strafeActive;
  private String phase = "Preparando";
  private double aimX, aimY, aimZ;

  public Session(ServerPlayerEntity p, TrainingBot b, Options options) {
    owner = p;
    bot = b;
    o = options;
    b.session = this;
    lastHealth = b.getHealth();
    aimX = p.getX();
    aimY = p.getEyeY();
    aimZ = p.getZ();
  }

  public void control() {
    if (closed || finish != null) return;
    clock++;
    int t = (int) clock;
    var d = o.difficulty;
    if (!owner.isAlive()
        || owner.isDisconnected()
        || owner.getServerWorld() != bot.getServerWorld()) {
      finish = "Treino encerrado: jogador saiu.";
      return;
    }
    bot.forwardSpeed = 0;
    bot.sidewaysSpeed = 0;
    bot.setSneaking(false);
    if (t == 2 || t == 3) {
      bot.setHealth(bot.getMaxHealth());
      owner.setHealth(owner.getMaxHealth());
    }
    double dist = bot.squaredDistanceTo(owner);
    if (t % 30 == 0 && random.nextBoolean()) side = -side;
    if (t % d.reaction == 0) strafeActive = random.nextDouble() < d.strafe;
    float health = bot.getHealth();
    if (health < lastHealth) {
      damageCount++;
      if (healing && damageCount >= 2) {
        bot.stopUsingItem();
        healing = false;
        gapWait = t + 50;
        selectSword();
      }
    } else if (t % 40 == 0) damageCount = 0;
    lastHealth = health;
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
    boolean behind =
        Aim.fraction(health, bot.getMaxHealth()) + 0.12
            < Aim.fraction(owner.getHealth(), owner.getMaxHealth());
    boolean otherEating =
        owner.isUsingItem()
            && owner.getActiveItem().contains(net.minecraft.component.DataComponentTypes.FOOD);
    if (!healing
        && o.gap
        && t > gapWait
        && (behind || otherEating || o.tank)
        && health < bot.getMaxHealth() - 4) {
      if (bot.isGliding() && t >= rocketAt) useRocket(t);
      int apple = find(Items.ENCHANTED_GOLDEN_APPLE, true);
      if (apple < 0) apple = find(Items.GOLDEN_APPLE, true);
      if (apple >= 0) {
        bot.getInventory().selectedSlot = apple;
        bot.getMainHandStack().use(bot.getServerWorld(), bot, Hand.MAIN_HAND);
        healing = bot.isUsingItem();
        healingStartedAt = t;
        damageCount = 0;
      }
    }
    if (healing && (!bot.isUsingItem() || t - healingStartedAt > 48)) {
      bot.stopUsingItem();
      healing = false;
      gapWait = t + 25;
      selectSword();
    }
    if (t % d.reaction == 0) {
      Vec3d point = owner.getEyePos().subtract(0, owner.getHeight() * 0.12, 0);
      double error =
          switch (d) {
            case LOW -> 0.45;
            case MEDIUM -> 0.20;
            case HIGH -> 0.09;
            case EXPERT -> 0.035;
          };
      aimX = point.x + random.nextGaussian() * error;
      aimY = point.y + random.nextGaussian() * error;
      aimZ = point.z + random.nextGaussian() * error;
    }
    Vec3d aim = new Vec3d(aimX, aimY, aimZ);
    if (healing || o.tank) {
      phase = healing ? "Recuperando com gap" : "Tank / evasao";
      double a = Math.atan2(bot.getZ() - o.z, bot.getX() - o.x) + side * 0.55;
      double r = o.size / 2.0 - 2;
      aim =
          new Vec3d(
              o.x + Math.cos(a) * r, Math.max(o.y + 1.1, bot.getY() - 0.7), o.z + Math.sin(a) * r);
    } else phase = "Combate";
    if (t < maneuverUntil && !healing && !o.tank && dist < 25 && dist > 9) {
      Vec3d relative = bot.getPos().subtract(owner.getPos());
      double angle = Math.atan2(relative.z, relative.x) + side * 0.65;
      aim =
          new Vec3d(
              owner.getX() + Math.cos(angle) * 2.2,
              owner.getY() + 0.5,
              owner.getZ() + Math.sin(angle) * 2.2);
      phase = "Reposicionando perto do alvo";
    }
    look(aim, d.aimSpeed);
    bot.setHeadYaw(bot.getYaw());
    bot.setBodyYaw(bot.getYaw());
    bot.setSprinting(!healing);
    bot.forwardSpeed = healing || o.tank ? 1 : dist > 2.3 ? 1 : 0.15f;
    if (o.strafe && !healing && strafeActive) bot.sidewaysSpeed = side;
    if (o.wtap && owner.getY() > bot.getY() + 1 && t % 18 < 3) bot.forwardSpeed = 0;
    if (bot.isOnGround() && t >= jumpAt) {
      bot.jump();
      jumpAt = t + 8 + (d == Options.Difficulty.LOW ? random.nextInt(13) : random.nextInt(4));
    } else if (!bot.isOnGround()
        && !bot.isGliding()
        && bot.getVelocity().y > -0.6
        && bot.getVelocity().y < 0.35
        && !(d == Options.Difficulty.LOW && t % 4 != 0)) bot.checkGliding();
    if (CombatPlan.mayReposition(
            o.giro,
            bot.isGliding(),
            healing,
            o.tank,
            t,
            maneuverAt,
            dist,
            bot.getY() - owner.getY())
        && bot.getVelocity().y < 0.08
        && random.nextDouble() < d.rockets) {
      if (useRocket(t)) {
        maneuverUntil = t + 6;
        maneuverAt = t + 55 + random.nextInt(35);
      }
    } else if (o.tank && !healing && bot.isGliding() && t >= rocketAt && dist < 60) useRocket(t);
    if (o.teia && t >= webAt && !healing) {
      if (placeWeb(o.tank ? bot.getBlockPos().down() : owner.getBlockPos().up(), t)) return;
    }
    if (!o.tank && !healing && heldUntil <= t && t >= attackAt) {
      int sword = selectSword();
      if (sword >= 0 && dist < CombatPlan.meleeIntentRange(bot.getEntityInteractionRange())) {
        bot.swingHand(Hand.MAIN_HAND);
        if (canHit()) bot.attack(owner);
        attackAt = t + Math.max(1, 20 / d.cps) + random.nextInt(2);
      }
    }
  }

  private boolean retotem(int t) {
    if (!bot.getOffHandStack().isEmpty()) return false;
    if (swapAt >= 0) {
      phase = "Retotem";
      if (t < swapAt) return true;
      int slot = bot.getInventory().selectedSlot;
      ItemStack main = bot.getMainHandStack();
      if (Kits.isTotem(main)) {
        bot.getInventory().setStack(40, main);
        bot.getInventory().setStack(slot, ItemStack.EMPTY);
      }
      swapAt = -1;
      selectSword();
      bot.getInventory().markDirty();
      return true;
    }
    int hot = find(Items.TOTEM_OF_UNDYING, false);
    if (hot >= 0) {
      bot.stopUsingItem();
      healing = false;
      bot.getInventory().selectedSlot = hot;
      swapAt = t + o.difficulty.swapDelay;
      return true;
    }
    int reserve = -1;
    for (int i = 9; i < 36; i++)
      if (Kits.isTotem(bot.getInventory().getStack(i))) {
        reserve = i;
        break;
      }
    if (reserve < 0) return false;
    phase = "Repondo 3 totems";
    bot.setSneaking(true);
    if (refillAt < 0) refillAt = t + o.difficulty.reaction + 4;
    if (t < refillAt) return true;
    // Move existing stacks only; never creates replacement totems.
    int moved = 0;
    for (int slot = 6; slot <= 8; slot++)
      if (bot.getInventory().getStack(slot).isEmpty()) {
        for (int i = 9; i < 36; i++)
          if (Kits.isTotem(bot.getInventory().getStack(i))) {
            bot.getInventory().setStack(slot, bot.getInventory().getStack(i));
            bot.getInventory().setStack(i, ItemStack.EMPTY);
            moved++;
            break;
          }
      }
    if (moved == 0) {
      int empty = -1;
      for (int i = 0; i < 9; i++)
        if (bot.getInventory().getStack(i).isEmpty()) {
          empty = i;
          break;
        }
      if (empty >= 0) {
        bot.getInventory().setStack(empty, bot.getInventory().getStack(reserve));
        bot.getInventory().setStack(reserve, ItemStack.EMPTY);
      }
    }
    refillAt = -1;
    bot.getInventory().markDirty();
    return false;
  }

  private int find(Item item, boolean move) {
    for (int i = 0; i < 9; i++)
      if ((item == Items.TOTEM_OF_UNDYING
          ? Kits.isTotem(bot.getInventory().getStack(i))
          : bot.getInventory().getStack(i).isOf(item))) return i;
    if (move)
      for (int i = 9; i < 36; i++)
        if ((item == Items.TOTEM_OF_UNDYING
            ? Kits.isTotem(bot.getInventory().getStack(i))
            : bot.getInventory().getStack(i).isOf(item))) {
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
    rocketAt = t + 35 + random.nextInt(20);
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
