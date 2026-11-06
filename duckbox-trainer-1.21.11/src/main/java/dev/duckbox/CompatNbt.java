package dev.duckbox;
import net.minecraft.entity.Entity;
import net.minecraft.nbt.*;
import net.minecraft.storage.*;
import net.minecraft.util.ErrorReporter;
public final class CompatNbt {
 public static NbtCompound write(Entity e){var view=NbtWriteView.create(ErrorReporter.EMPTY,e.getRegistryManager());e.writeData(view);return view.getNbt();}
 public static void read(Entity e,NbtCompound n){e.readData(NbtReadView.create(ErrorReporter.EMPTY,e.getRegistryManager(),n));}
}
