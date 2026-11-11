import com.duckswords.update.*;import com.duckswords.connect.ServiceRoute241;
import java.nio.file.*;import java.util.*;
public final class Manifest241Test{
 public static void main(String[] args)throws Exception{
  String text=Files.readString(Path.of(args[0]));String game=args[1];Path jar=Path.of(args[2]);
  var release=UpdateManifest229.verify(text,ServiceRoute241.KEY,game,"1.5.28-beta.2.40");
  if(release==null||!release.version().equals("1.5.28-beta.2.41"))throw new AssertionError("Invalid new release");
  UpdateDownload229.validate(jar,release);
  if(UpdateManifest229.verify(text,ServiceRoute241.KEY,game,"1.5.28-beta.2.41")!=null)throw new AssertionError("Self-update loop");
  if(ServiceRoute241.verify(Files.readString(Path.of(args[3])),ServiceRoute241.KEY).enabled())throw new AssertionError("Unexpected active service endpoint");
  Path bad=Files.createTempFile("duck-invalid-jar-",".jar");
  try{Files.writeString(bad,"not a mod");boolean rejected=false;try{UpdateDownload229.validate(bad,release);}catch(Exception e){rejected=true;}if(!rejected)throw new AssertionError("Invalid jar accepted");}finally{Files.delete(bad);}
  System.out.println("PASS signed manifest, 240->241 transition, whole JAR hash/size/identity, no update loop, pending route and corrupted artifact rejection: "+game);
 }
}
