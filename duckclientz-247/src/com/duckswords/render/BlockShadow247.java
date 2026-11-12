package com.duckswords.render;
import java.util.*;
/** Exact occlusion intervals along a line. Intersect its camera triangle with each voxel-shape box. */
public final class BlockShadow247 {
 private BlockShadow247(){}
 public static double[] visible(double[] camera,double[] a,double[] b,List<double[]> boxes){
  List<double[]> spans=new ArrayList<>();spans.add(new double[]{0,1});
  for(double[] box:boxes){double[] shadow=shadow(camera,a,b,box);if(shadow==null)continue;
   List<double[]> next=new ArrayList<>();for(double[] span:spans){
    if(shadow[1]<=span[0]||shadow[0]>=span[1])next.add(span);
    else {if(shadow[0]>span[0])next.add(new double[]{span[0],shadow[0]});if(shadow[1]<span[1])next.add(new double[]{shadow[1],span[1]});}
   }spans=next;if(spans.isEmpty())break;
  }
  double[] result=new double[spans.size()*2];for(int i=0;i<spans.size();i++){result[2*i]=spans.get(i)[0];result[2*i+1]=spans.get(i)[1];}return result;
 }
 static double[] shadow(double[] c,double[] a,double[] b,double[] box){
  for(int k=0;k<3;k++)if(box[k]>Math.max(c[k],Math.max(a[k],b[k]))+1e-9||box[k+3]<Math.min(c[k],Math.min(a[k],b[k]))-1e-9)return null;
  List<double[]> polygon=new ArrayList<>();polygon.add(new double[]{0,0});polygon.add(new double[]{1-1e-6,0});polygon.add(new double[]{1-1e-6,1-1e-6});
  for(int k=0;k<3;k++){
   double u=a[k]-c[k],v=b[k]-a[k];
   polygon=clip(polygon,u,v,box[k+3]-c[k]+1e-9);if(polygon.isEmpty())return null;
   polygon=clip(polygon,-u,-v,c[k]-box[k]+1e-9);if(polygon.isEmpty())return null;
  }
  double lo=1,hi=0;for(double[] p:polygon){if(p[0]<1e-10)return new double[]{0,1};double t=Math.max(0,Math.min(1,p[1]/p[0]));lo=Math.min(lo,t);hi=Math.max(hi,t);}
  return hi-lo>1e-10?new double[]{lo,hi}:null;
 }
 private static List<double[]> clip(List<double[]> input,double u,double v,double limit){
  List<double[]> output=new ArrayList<>();if(input.isEmpty())return output;
  double[] previous=input.get(input.size()-1);double prior=u*previous[0]+v*previous[1]-limit;
  for(double[] current:input){double distance=u*current[0]+v*current[1]-limit;
   if((prior<=0)!=(distance<=0)){double t=prior/(prior-distance);output.add(new double[]{previous[0]+(current[0]-previous[0])*t,previous[1]+(current[1]-previous[1])*t});}
   if(distance<=0)output.add(current);previous=current;prior=distance;
  }return output;
 }
}
