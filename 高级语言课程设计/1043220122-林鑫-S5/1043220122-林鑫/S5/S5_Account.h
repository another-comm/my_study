#ifndef S5_ACCOUNT_H
#define S5_ACCOUNT_H
#include "S5_Date.h"
#include<string>

class Account {
private:
	string id;
	double balance;
	static double total;
protected:
	Account(const Date& date, string id);
	void record(const Date& date, double amount, string desc);
	void error(string msg) const;
public:
	string getId()const { return id; }
	double getBalance()const { return balance; }
	virtual void show()const ;
	static double getTotal() { return total; };

	virtual void deposit(const Date& date, double amount, string desc) = 0;
	virtual void withdraw(const Date& date, double amount, string desc) = 0;
	virtual void settle(const Date& date) = 0;

};



#endif