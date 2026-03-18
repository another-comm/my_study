#include "D:\\BankAccount\\S4\\S4_SavingsAccount.h"
SavingsAccount::SavingsAccount(Date date,string id,double rate):
Account(date,id),rate(rate), acc(date,0){}
void SavingsAccount::deposit(Date date,double amount, string desc)
{
    record(date,amount,desc);
    acc.change(date,getBalance());
}

void SavingsAccount::withdraw(Date date, double amount, string desc)
{
	if(amount>getBalance()){ 
	error("not enough money");
}
	else
	{
	record(date, -amount,desc);
	acc.change(date,getBalance());
	}
}

void SavingsAccount::settle(Date date)
{
    double interest=acc.getSum(date)*rate/date.distance(Date(date.getYear()-1,1,1));//计算利息
    if(interest!=0)
    record(date,interest,"interest");
    acc.reset(date,getBalance()); 
}