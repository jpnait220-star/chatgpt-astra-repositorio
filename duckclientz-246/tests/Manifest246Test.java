import com.duckswords.update.*;import com.duckswords.connect.ServiceRoute241;import java.nio.file.*;
public final class Manifest246Test {
 public static void main(String[] a)throws Exception {
  String envelope=Files.readString(Path.of(a[0]));String game=a[1];
  var release=UpdateManifest229.verify(envelope,ServiceRoute241.KEY,game,"1.5.28-beta.2.45");
  if(release==null||!release.version().equals("1.5.28-beta.2.46"))throw new AssertionError("Wrong release");
  UpdateDownload229.validate(Path.of(a[2]),release);
  if(UpdateManifest229.verify(envelope,ServiceRoute241.KEY,game,"1.5.28-beta.2.46")!=null)throw new AssertionError("Loop");
  if(!ServiceRoute241.verify(Files.readString(Path.of(a[3])),ServiceRoute241.KEY).enabled())throw new AssertionError("Service inactive");
  System.out.println("PASS 2.45->2.46 update signature/hash/size/metadata, self-update no-op, active service signature: "+game);
 }
}
