#include<stdio.h>
#include<math.h>
#define n 9
#define m 2
void gauss(double a[m+1][m+1],double b[m+1],double x[m+1])
{      double l[m+1][m+1];
		double sum;
		

	  int i,j,k;
	 for (k=0;k<=m-1;k++)
{                                                           
     for (i=k+1;i<=m;i++)
     {
        l[i][k]=a[i][k]/a[k][k];
         b[i]=b[i]-l[i][k]*b[k];
		 
         for (j=k+1;j<=m;j++)
            {
           a[i][j]=a[i][j]-l[i][k]*a[k][j];
		  
             }
     }
}

x[m]=b[m]/a[m][m];

 for (k=m-1;k>=0;k--)
{
    sum=0;
   for (j=k+1;j<=m;j++)
    {
    sum=sum+a[k][j]*x[j];
    }  
   
     x[k]=(b[k]-sum)/a[k][k];
	
}
 
}
int main()
{
  int i,j,k,l;
	double G[m+1][m+1],d[m+1],a[m+1];
	double sum,error=0.,ls;
	
	double x[n+1]={0.,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9};
	double y[n+1]={0.,5.1234,5.3057,5.5680,5.9378,6.4370,7.0978,7.9493,9.0253,10.3627};
	double w[n+1]={0.,1.,1.,1.,1.,1.,1.,1.,1.,1.};
	printf("正则方程组的系数矩阵\n"); 
	for (k=0;k<=m;k++)
	{
		for (j=0;j<=m;j++)
		{
			G[k][j]=0.;
			for (i=1;i<=n;i++)
			{
				G[k][j]=G[k][j]+w[i]*pow(x[i],k+j);
			}
			printf("%lf\t",G[k][j]);
		}
		printf("\n");
	}
	printf("正则方程组的右端向量\n");
	for (j=0;j<=m;j++)
	{
		d[j]=0.;
		for (i=1;i<=n;i++)
		{
			d[j]=d[j]+w[i]*y[i]*pow(x[i],j);
		}
		printf("%lf\n",d[j]);
	}

	gauss(G,d,a);
	printf("\n拟合的二次多项式\n");
	for (i=0;i<=m;i++)
	{
		if (a[i]<0)
		printf("(%lf)",a[i]);
		else
         printf("%lf",a[i]);
		for (j=1;j<i;j++)
		{
			printf("x*");
		}
		if (j==i)
			printf("x");
		if (i==m)
			break;
		printf("+");

	}
	for (i=1;i<=n;i++)
	{   ls=0.;
		for (l=0;l<=m;l++)
		{
			ls=ls+a[l]*pow(x[i],l);
		}
		error=error+w[i]*pow(ls-y[i],2.);
	}
	error=sqrt(error);
	//printf("\n均方误差%e\n",error);
	
  return 0;
}
