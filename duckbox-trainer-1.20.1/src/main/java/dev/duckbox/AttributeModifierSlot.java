package dev.duckbox;
public enum AttributeModifierSlot {ANY,MAINHAND,OFFHAND,HAND,HEAD,CHEST,LEGS,FEET,ARMOR;
 public String asString(){return name().toLowerCase(java.util.Locale.ROOT);}
 public net.minecraft.entity.EquipmentSlot nativeSlot(){return net.minecraft.entity.EquipmentSlot.byName(asString());}
}
