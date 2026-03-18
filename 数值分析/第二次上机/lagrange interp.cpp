#include<cstdio>
#include <cmath>
#define n 7
 #define m 4
 int main()
{double lagrange(double *x, double *y, double x0);
  double x[n+1]={0.5,0.7,0.9,1.1,1.3,1.5,1.7,1.9};
  double y[n+1]={0.48,0.64,0.78,0.89,0.96,1.00,0.99,0.95};
  double a[m+1]={0.74,1.6,0.55,1.2,1.85};
  int i;
  double Ln;
  for (i = 0; i <= m; i++)    
    { 
    Ln = lagrange(x, y,a[i]);    
   
    printf("f(%6.3f)=%12.8e\n", a[i],Ln);    
   
   }
  
 return 0; 
}
double lagrange(double *x, double *y, double x0)    
{    
    int i, j;    
    double Ln = 0, l;    
   
    for (i = 0; i <= n; i++)    
    {    
        l = 1.0;    
        for (j = 0; j <= n; j++)    
        {    
            if (j !=i)    
            {    
                    l = l * (x0 - x[j]) /(x[i] - x[j]); 
            }    
               
        }    
        Ln = Ln + y[i] * l;    
   
    }    
    return Ln;    
}    
