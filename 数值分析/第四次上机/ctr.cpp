#include "stdio.h" 
#include "math.h"

double CTR ( int n, double a, double b, double (* f)(double ) )
{
  double h,r;
  int k;
  h=(b-a)/n;

  //r=(* f)(a)+(* f)(b);
  r=f(a)+f(b);
  
  for (k=1;k<=n-1;k++)
  {
// r=r+2.*(*f)(a+k*h);
r=r+2.*f(a+k*h);
  }
 r=r*(h/2.);

 return r;
}


double  f1(double x)
 {  
	return 1./(1.+sin(x)*sin(x));
  }  


 double  f2(double x)
 {  
	 return x*log10(x); 
 }   
 
 double f3(double x)
 {
return (exp(-x*x));
 }
double f4(double x)
{
	return (sqrt(x));
}
double f5(double x)
{
	return x/(4.+pow(x,2.));
}
double f6(double x)
{
	return sqrt(4-pow(sin(x),2.));
}
 int main( )
 { 
  FILE *outfile = fopen("out.txt", "w");  
 int n;    
 double a, b,r; 
 
 a = 0.0;  b = 1.0;  
 n = 10; 
 printf( "复合梯形公式计算第一个积分=%12.9e\n", CTR(n, a, b,f1)); 
 //???f1???????????
 
 a = 1.0;  b = 2.0;  
 n = 8; 
printf( "复合梯形公式计算第二个积分=%12.9e\n", CTR(n, a, b,f2));

/*a = 0.0;  b = 1.0; 
n = 8; 
 printf( "%12.9e\n", CTR(n, a, f3));

a = 1.0;  b = 9.0; 
n = 4; 
 fprintf(outfile, "%12.9e\n", CTR(n, a, b, f4));*/
/*a = 0.0;  b = 1.0; 
n = 1; 
 fprintf(outfile, "%12.9e\n", CTR(n, a, b, f5));

a = 1.0;  b = 9.0; 
n = 1; 
 fprintf(outfile, "%12.9e\n", CTR(n, a, b, f4));*/

fclose(outfile); 
return 0;
 } 




