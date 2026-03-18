#include "S5_SavingsAccount.h"

SavingsAccount::SavingsAccount(const Date& date, string id, double rate) :
	Account(date, id), acc(date, 0), rate(rate)
{
	date.show();
	cout << "\t#" << id << " is created" << endl;
}

void SavingsAccount::deposit(const Date& date, double amount, string desc)
{

	record(date, amount, desc);
	acc.change(date, getBalance());

}
void SavingsAccount::withdraw(const Date& date, double amount, string desc)
{
	if (amount > getBalance())
		error("Error: not enough money");
	else
	{

		record(date, -amount, desc);
		acc.change(date, getBalance());
	}
}

void SavingsAccount::settle(const Date& date)
{
	double interest = 0;
	if(date.getMonth()==1)
	interest = acc.getSum(date) * rate /(date-Date(date.getYear()-1,1,1));//º∆À„¿˚œ¢
	if (interest != 0)
		record(date, interest, "interest");
	acc.reset(date, getBalance());
}
void SavingsAccount::show()const
{
	cout << "#" << getId() << "\tBalance: " << getBalance() << endl;
}

