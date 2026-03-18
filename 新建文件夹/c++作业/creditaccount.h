#ifndef CREDITACCOUNT_H
#define CREDITACCOUNT_H

#include "date.h"
#include "account.h"
#include "accumulator.h"

class CreditAccount :public Account {
private:
	Accumulator acc;
	double credit;
	double rate;
	double fee;
	double getDebt() const {
		double balance = getBalance();
		return (balance < 0 ? balance : 0);
	}
public:
	CreditAccount(const Date& date, const std::string& id, double credit, double rate, double fee);
	double getCredit() const { return credit; }
	double getRate() const { return rate; }
	double getFee() const { return fee; }
	double getAvailableCredit() const {
		if (getBalance() < 0)
			return credit + getBalance();
		else
			return credit;
	}
	void deposit(const Date& date, double amount, const std::string& desc);
	void withdraw(const Date& date, double amount, const std::string& desc);
	void settle(const Date& date);
	void show() const;

};
#endif // CREDITACCOUNT_H
