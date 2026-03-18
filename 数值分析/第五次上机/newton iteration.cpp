#include<cstdio>
#include <cmath>
double f1(double x)
{
	return x*x*x-3.*x-1;
	//return x-tan(x);
	//return pow(2.,x)-4.*x;
}
double f_d1(double x )
{
	return 3.*x*x-3.;
	//return -tan(x)*tan(x);
	//return pow(2.,x)*log(2.)-4.;
}
//double newton(double x_0)
double newton(double x_0,double (*f)(double),double (*f_d)(double))
{
	//return x_0-(*f)(x_0)/(*f_d)(x_0);
	return x_0-f(x_0)/f_d(x_0);

}
double delta(double x_0,double x_1)
{
	double r;
	/*if (fabs(x_1)<C)
		r=fabs(x_1-x_0);
	else
		r=fabs(x_1-x_0)/fabs(x_1);*/
	r=fabs(x_1-x_0)/(1.+fabs(x_1));
	return r;
}
int main()
{
  double x_0, x_1,epsilon=0.5e-5;
	//printf("%f\n",epsilon);
	int N=20,i;
	i=1;
	
	x_0=0;
	while (i<=N)
{ 
   x_1=newton(x_0,f1,f_d1);
  
  if (fabs(delta(x_0,x_1))<epsilon)
  {
   printf("newton法迭代步数=%d， 近似值=%.5f\n",i,x_1);
    break;
  }
   x_0=x_1;
   i=i+1; 
}
if (i>N)
 printf("超过最大迭代次数");
return 0;
}
