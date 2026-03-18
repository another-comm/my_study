#include "account.h"
#include <string>
#include <cmath>
#include <iostream>

using namespace std;

double Account::total = 0.0;
Account::Account(const Date& date, const string& id) :id(id), balance(0)
{
	date.show();
	cout << "\t#" << id << " created" << endl;
}

void Account::record(const Date& date, double amount, const string& desc)
{
	amount = floor(amount * 100 + 0.5) / 100;
	balance += amount;
	total += amount;
	date.show();
	cout << "\t#" << id << "\t" << amount << "\t" << balance << "\t" << desc << endl;
}
void Account::show() const { cout << "#" << id << "\tBalance: " << balance; }
void Account::error(const string& msg) const { cout << "Error(#" << id << "):" << msg << endl; }
