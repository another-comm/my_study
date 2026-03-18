#include<iostream>
#include"creditaccount.h"
#include"savingsaccount.h"
#include<vector>
using namespace std;

int main()
{

	Date date(2008, 11, 1);
	Account* pt[3];
	SavingsAccount sa1(date, "03755217", 0.015);
	SavingsAccount sa2(date, "02342342", 0.015);
	CreditAccount ca1(date, "c5392394", 10000, 0.0005, 50);
	pt[0] = &sa1;
	pt[1] = &sa2;
	pt[2] = &ca1;
	const int n = sizeof(pt) / sizeof(pt[0]);//计算账户总数
	pt[0]->deposit(Date(2008, 11, 5), 5000, "salary");
	pt[2]->withdraw(Date(2008, 11, 15), 2000, "buy a cell");
	pt[1]->deposit(Date(2008, 11, 25), 10000, "sell stock 0323");
	pt[2]->settle(Date(2008, 12, 1));
	pt[2]->deposit(Date(2008, 12, 1), 2016, "repay the credit");
	pt[0]->deposit(Date(2008, 12, 5), 5500, "salary");
	for (int i = 0; i < n; i++)
	{
		pt[i]->settle(Date(2009, 1, 1));
	}
	cout << endl;
	for (int i = 0; i < n; i++)
	{
		pt[i]->show();
		cout << endl;
	}
	cout << "Total:" << Account::getTotal() << endl;
	return 0;
}
