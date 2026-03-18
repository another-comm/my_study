#include "stdio.h" 
#include "math.h"
#include "malloc.h"
double  f0(double  x, double  y) 
{  
	return (-pow(x,2)+1+y); 
} 
double  f1(double  x, double  y) 
{  
	return (-y+x*x+4.*x-1.)/2.; 
} 

double ff(double x)
{
	//return -exp(-x)+pow(x,2)-x+1.;
	return 1+pow(x,5.)/5.;
}


/*double ff(double x)
{
	return -x-1+2*exp(x);
}
*/

double  f2(double  x, double  y) 
{  
	return 3.*y/(1.+x); 
} 
double f3(double x,double y)
{
	return y-2.*x/y;
}
void  RK4 ( double (*f)( double,double ), double a, double b, double y0, int N, FILE *outfile)
{
//根据Runge-Kunta格式写出此函数

	double *y,*x,K_1,K_2,K_3,K_4,h;
	int k;
y=(double*)malloc((sizeof(double)) * (N+1));
x=(double*)malloc((sizeof(double)) * (N+1));
y[0]=y0;
h=(b-a)/N;

  for (k =0 ; k <= N; k++)
  {
      x[k]=a+k*h;
  }


  for (k =0 ; k <= N-1; k++)
  {    
       K_1=(*f)(x[k],y[k]);
	   K_2=(*f)(x[k]+h/2.,y[k]+h/2.*K_1);
       K_3=(*f)(x[k]+h/2.,y[k]+h/2.*K_2);
	   K_4=(*f)(x[k]+h,y[k]+h*K_3);
	   y[k+1]=y[k]+h/6.*(K_1+2*K_2+2*K_3+K_4);
  }

  
  
for (k =0 ; k <= N; k++)
  {
	  fprintf(outfile,"%6.4f\t%12.9e\n",x[k],y[k]);
  }

}

int main( ) 
{ 
	FILE *outfile = fopen("out.txt", "w"); 
	int  N; 
	double  a, b, y0;   
	a = 0.0;  b = 1.0;  
	y0 = 0.0;  
	N = 5; 
	RK4(f1, a, b, y0, N, outfile); 
	/*a = 0.0;  b = 0.3;  
	y0 = 1.;  
	n = 3; 
	RK4(f0, a, b, y0, N, outfile);*/


/*	fprintf(outfile, "\n"); 

a = 0.0;  b = 1.0;  
	y0 = 1.;  
	n = 5; 
	RK4(f2, a, b, y0, N, outfile);*/

	//test
	 
	/*a = 0.0;  b = 1.0;  
	y0 = 0.;  
	N = 5; 
	RK4(f0, a, b, y0, N, outfile); */

	fclose(outfile);
	return 0;
 } 
