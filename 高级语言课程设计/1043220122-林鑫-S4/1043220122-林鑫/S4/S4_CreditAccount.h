#ifndef S4_CREDITACCOUNT_H
#define S4_CREDITSACCOUNT_H
#include "S4_Account.h"
#include"S4_Accumulator.h"

class CreditAccount : public Account {
private:
	Accumulator acc;
	double credit;
	double rate;
	double fee;
	double getDebt()const;
public:
	CreditAccount(Date date, string id, double credit, double rate, double fee);
	double getCredit()const { return credit; }
	double getRate()const { return rate; }
	double getFee()const { return fee; }
	double getAvailableCredit()const;
	void deposit(Date date, double amount, string desc);
	void withdraw(Date date, double amount, string desc);
	void settle(Date date);
};



#endif