#ifndef S5_CREDITACCOUNT_H
#define S5_CREDITACCOUNT_H
#include "S5_Account.h"
#include"S5_Accumulator.h"

class CreditAccount : public Account {
private:
	Accumulator acc;
	double credit;
	double rate;
	double fee;
	double getDebt()const;
public:
	CreditAccount(const Date& date, string id, double credit, double rate, double fee);
	double getCredit()const { return credit; }
	double getRate()const { return rate; }
	double getFee()const { return fee; }
	double getAvailableCredit()const;
	void deposit(const Date& date, double amount, string desc);
	void withdraw(const Date& date, double amount, string desc);
	void settle(const Date& date);
	void show() const;
};



#endif