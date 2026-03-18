#include "S4_SavingsAccount.h"

SavingsAccount::SavingsAccount(Date date, string id, double rate) :
	Account(date, id), acc(date, 0), rate(rate)
{
	date.show();
	cout << "\t#" << id << " is created" << endl;
}

void SavingsAccount::deposit(Date date, double amount, string desc)
{
	
	record(date, amount, desc);
	acc.change(date, getBalance());

}
void SavingsAccount::withdraw(Date date, double amount, string desc)
{
	if (amount > getBalance())
		error("Error: not enough money");
	else
	{
		
		record(date, -amount, desc);
		acc.change(date, getBalance());
	}
}

void SavingsAccount::settle(Date date) 
{
	int y = date.getYear();
	double interest = rate * acc.getSum(date) / Date(y,1,1).distance(Date(y-1,1,1));
	if (interest != 0)
	{
		acc.change(date, getBalance() + interest);
		record(date, interest, "interest");
	}
	acc.reset(date, getBalance());
}

