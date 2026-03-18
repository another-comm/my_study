#ifndef SAVINGSACCOUNT_H
#define SAVINGSACCOUNT_H

#include "date.h"
#include "account.h"
#include "accumulator.h"

class SavingsAccount :public Account {
private:
	Accumulator acc;
	double rate;
public:
	SavingsAccount(const Date& date, const std::string& id, double rate);
	double getRate() const { return rate; }
	virtual void deposit(const Date& date, double amount, const string& desc);
	virtual void withdraw(const Date& date, double amount, const string& desc);
	virtual void settle(const Date& date);
	virtual void show() const ;

};
#endif // SAVINGSACCOUNT_H
