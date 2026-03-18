#ifndef S5_SAVINGSACCOUNT_H
#define S5_SAVINGSACCOUNT_H
#include "S5_Account.h"
#include"S5_Accumulator.h"

class SavingsAccount :public Account {
private:
	Accumulator acc;
	double rate;
public:
	SavingsAccount(const Date& date, string id, double rate);
	double getRate()const { return rate; }
	void deposit(const Date& date, double amount, string desc);
	void withdraw(const Date& date, double amount, string desc);
	void settle(const Date& date);
	void show() const;
};


#endif