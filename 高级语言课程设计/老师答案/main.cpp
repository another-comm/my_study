#include "D:\\BankAccount\\S4\\S4_date.h"
#include "D:\\BankAccount\\S4\\S4_Account.h"
#include "D:\\BankAccount\\S4\\S4_accumulator.h"
#include "D:\\BankAccount\\S4\\S4_CreditAccount.h"
#include "D:\\BankAccount\\S4\\S4_SavingsAccount.h"
#include <iostream>
using namespace std;
int main()
{
	Date date(2008,11,1);
	SavingsAccount sa[]={
	SavingsAccount(date,"03755217",0.015),
	SavingsAccount(date,"02342342",0.015)};
	const int n=sizeof(sa)/sizeof(SavingsAccount);//账户总数
	CreditAccount ca[]={CreditAccount(Date(2008,1,1),"C5392394",10000,0.0005,50),CreditAccount(Date(2008,3,20),"C5392398",10000,0.0005,50)};
	sa[0].deposit(Date(2008,11,5),5000,"salary");
	sa[1].deposit(Date(2008,11,25),10000,"sell stock 0323");
	sa[0].deposit(Date(2008,12,5),5500,"salary");
	sa[1].withdraw(Date(2008,12,20),4000,"buy a laptop");
	cout<<endl;
	for(int i=0;i<n;i++)
	{	sa[i].settle(Date(2009,1,1));
		sa[i].show();
		cout<<endl;
	}
	
    ca[0].withdraw(Date(2008,11,15),2000,"buy a cell");
    ca[0].settle(Date(2008,12,1));   
    ca[0].deposit(Date(2008,12,1),2016,"repay the credit");
    ca[0].settle(Date(2009,1,1));
    ca[0].withdraw(Date(2009,3,5),12000,"buy a new laptop");
	ca[0].show();cout<<endl;

 	ca[1].withdraw(Date(2008,3,28),3000,"buy a monitor");
    ca[1].settle(Date(2008,12,1));   
    ca[1].deposit(Date(2008,12,1),3500,"repay the credit");
    ca[1].settle(Date(2009,1,1));
    ca[0].withdraw(Date(2009,4,5),5000,"buy a new laptop");
	ca[1].show();cout<<endl;
	cout<<"Total:"<<Account::getTotal()<<endl;
	return 0; 
}