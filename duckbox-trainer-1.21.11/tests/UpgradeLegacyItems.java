import java.nio.file.*;
import com.google.gson.*;
import net.minecraft.nbt.*;
public final class UpgradeLegacyItems {
 public static void main(String[] args)throws Exception{
  net.minecraft.SharedConstants.createGameVersion();net.minecraft.Bootstrap.initialize();
  var input=JsonParser.parseString(Files.readString(Path.of(args[0]))).getAsJsonArray();var output=new JsonObject();
  for(var value:input){var raw=StringNbtReader.readCompound(value.getAsString());output.addProperty(value.getAsString(),dev.duckbox.LegacyStockMigration.upgrade(raw).toString());}
  Files.writeString(Path.of(args[1]),output.toString());System.out.println("UPGRADED "+output.size()+" native ItemStack records");System.exit(0);
 }
}
