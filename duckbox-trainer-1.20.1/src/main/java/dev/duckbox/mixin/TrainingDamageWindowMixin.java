package dev.duckbox.mixin;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.damage.DamageSource;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.*;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
@Mixin(LivingEntity.class)
public abstract class TrainingDamageWindowMixin {
 @Inject(method="method_5643",at=@At("RETURN"),remap=false)
 private void duckbox$window(DamageSource source,float amount,CallbackInfoReturnable<Boolean> ci){if(ci.getReturnValue())dev.duckbox.DuckBox.shortenTrainingHitWindow((LivingEntity)(Object)this,source);}
}
