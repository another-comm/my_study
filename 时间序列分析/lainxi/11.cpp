#include<iostream>
using namespace std;
int main()
{
	double a[105],sum=0;
	a[0]=0.5,a[1]=0.05;
	sum+=a[0]*a[0]+a[1]*a[1];
	for(int i=2;i<99;i++)
	{
		a[i]=a[i-1]-0.7*a[i-2];
		sum+=a[i]*a[i];
	}
	cout << sum;
	return 0;
	
}
