#include "accumulator.h"
#include "date.h"
#include "creditaccount.h"
#include <string>
#include <iostream>

using namespace std;

CreditAccount::CreditAccount(const Date& date, const string& id, double credit, double rate, double fee) :
	Account(date, id), credit(credit), rate(rate), fee(fee), acc(date, 0) {}

void CreditAccount::deposit(const Date& date, double amount, const std::string& desc)
{
	record(date, amount, desc);
	acc.change(date, getDebt());
}

void CreditAccount::withdraw(const Date& date, double amount, const std::string& desc)
{
	if ((amount - getBalance()) > credit)
		error("not enough credit");
	else
	{
		record(date, -amount, desc);
		acc.change(date, getDebt());
	}
}

void CreditAccount::settle(const Date& date)
{
	double interest = acc.getSum(date) * rate;
	if (interest != 0)
		record(date, interest, "interest");
	if (date.getMonth() == 1)
		record(date, -fee, "annual fee");
	acc.reset(date, getDebt());
}

void CreditAccount::show() const {
	Account::show();
	cout << "\tAvailable credit:" << getAvailableCredit();
}
