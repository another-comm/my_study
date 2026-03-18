#include<cstdio>
#include <cmath>
#define n 5
//suanfa 5.1
int main()
{
  float x0;
  float x[n+1]={0.4,0.55,0.65,0.8,0.9,1.05};
  float y[n+1]={0.41075,0.57815,0.69675,0.88811,1.02652,1.25385}; 
  int i,j,k;
  float Nn,l,Rn;
  x0=0.74;
  float f[n+2],fn[n+1];
  for (k=0;k<=n;k++)
  {
    f[k]=y[k];
  }
 fn[0]=f[n];
 k=0;
 for (i=1;i<=n;i++)
 {
   k=k+1;
   fn[k]=(f[n-1]-f[n])/(x[n-i]-x[n]);
   f[n]=fn[k];
   for (j=n-1;j>=i;j--)
   {
     f[j]=(f[j-1]-f[j])/(x[j-i]-x[j]);
   }
 }
  Nn=f[0];
  for (k=1;k<=n;k++)
  { l=1.;
     for (j=0;j<=k-1;j++)
     {
       l=l*(x0-x[j]);
     }
    Nn=Nn+f[k]*l;
  }
  f[n+1]=Nn;
  for (k=1;k<=n+1;k++)
  {
    f[n+1]=(fn[k-1]-f[n+1])/(x[n+1-k]-x0);
  }
  l=1;
  for (j=0;j<=n;j++)
  {
    l=l*(x0-x[j]);
  }
  Rn=f[n+1]*l;
  printf("Nn=%12.8e,Rn=%12.8e\n",Nn,Rn);
  return 0;
}
