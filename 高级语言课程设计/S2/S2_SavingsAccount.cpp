#include "D:\\BankAccount\\S2\\S2_SavingsAccount.h"

double SavingsAccount::total=0;
SavingsAccount::SavingsAccount(int date, string id, double rate):lastDate(date),id(id),rate(rate),balance(0),accumulation(0)
{
	cout<<date<<"\t#"<<id<<" is created."<<endl; 	
}
void SavingsAccount::record(int date,double amount)
{
	accumulation=accumulate(date);
	balance+=amount;
	total+=amount;
	lastDate=date;
	cout<<date<<"\t"<<id<<"\t"<<amount<<"\t"<<balance<<endl;

}
void SavingsAccount::deposit(int date, double amount)
{record(date,amount);}

void SavingsAccount::withdraw(int date, double amount)
{
	if(amount>getBalance())
	cout<<"Error: not enough money"<<endl;
	else
	record(date, -amount);
}

void SavingsAccount::settle(int date)
{double interest=accumulate(date)*rate/365;//计算利息
if(interest!=0)
record(date,interest);
accumulation=0; 
}

void SavingsAccount::show() const
{cout<<"#"<<id<<"\tBalance:"<<balance;
}
