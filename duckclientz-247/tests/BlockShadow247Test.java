import com.duckswords.render.BlockShadow247;import java.util.*;
public final class BlockShadow247Test {
 static int checks;static void ok(boolean v,String why){checks++;if(!v)throw new AssertionError(why);}
 static boolean ray(double[] c,double[] p,double[] q){double lo=0,hi=1-1e-7;for(int k=0;k<3;k++){double d=p[k]-c[k];if(Math.abs(d)<1e-12){if(c[k]<q[k]||c[k]>q[k+3])return false;}else{double a=(q[k]-c[k])/d,b=(q[k+3]-c[k])/d;lo=Math.max(lo,Math.min(a,b));hi=Math.min(hi,Math.max(a,b));if(lo>hi)return false;}}return true;}
 static boolean visible(double[] intervals,double t){for(int i=0;i<intervals.length;i+=2)if(t>intervals[i]+1e-5&&t<intervals[i+1]-1e-5)return true;return false;}
 public static void main(String[] args){
  double[] camera={0,0,0},a={-2,0,4},b={2,0,4},wall={-.25,-1,2,.25,1,3};
  double[] v=BlockShadow247.visible(camera,a,b,List.of(wall));ok(v.length==4,"partial wall splits line");ok(Math.abs(v[1]-.375)<1e-5&&Math.abs(v[2]-.625)<1e-5,"projective clipping boundaries");
  ok(BlockShadow247.visible(camera,a,b,List.of(new double[]{-4,-4,2,4,4,3})).length==0,"full wall blocks entire edge");
  ok(BlockShadow247.visible(camera,a,b,List.of(new double[]{-4,-4,6,4,4,7})).length==2,"wall behind target does not hide outline");
  ok(BlockShadow247.visible(camera,a,b,List.of(new double[]{-1,-1,-1,1,1,1})).length==0,"camera inside solid block");
  Random random=new Random(247);int comparisons=0;
  for(int run=0;run<3000;run++){
   double[] c={random.nextDouble()*8-4,random.nextDouble()*8-4,random.nextDouble()*8-4};double[] x=new double[3],y=new double[3],q=new double[6];
   for(int k=0;k<3;k++){x[k]=random.nextDouble()*8-4;y[k]=random.nextDouble()*8-4;q[k]=random.nextDouble()*6-3;q[k+3]=q[k]+.03+random.nextDouble()*2;}
   double[] intervals=BlockShadow247.visible(c,x,y,List.of(q));
   for(int j=0;j<40;j++){double t=(j+.381)/40;boolean near=false;for(double edge:intervals)if(Math.abs(edge-t)<2e-5)near=true;if(near)continue;double[] p={x[0]+(y[0]-x[0])*t,x[1]+(y[1]-x[1])*t,x[2]+(y[2]-x[2])*t};boolean expected=!ray(c,p,q);if(visible(intervals,t)!=expected)throw new AssertionError("independent ray/interval disagreement "+run+" "+t);comparisons++;}
  }
  System.out.println("PASS "+checks+" occlusion cases and "+comparisons+" independent ray/interval comparisons; full/partial/behind/inside block.");
 }
}
