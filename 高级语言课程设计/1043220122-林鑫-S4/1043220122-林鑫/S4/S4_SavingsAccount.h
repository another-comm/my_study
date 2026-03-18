#ifndef S4_SAVINGSACCOUNT_H
#define S4_SAVINGSACCOUNT_H
#include "S4_Account.h"
#include"S4_Accumulator.h"

class SavingsAccount :public Account {
private:
	Accumulator acc;
	double rate;
public:
	SavingsAccount(Date date, string id, double rate);
	double getRate()const { return rate; }
	void deposit(Date date, double amount, string desc);
	void withdraw(Date date, double amount, string desc);
	void settle(Date date);

};


#endif