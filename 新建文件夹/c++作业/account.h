#ifndef ACCOUNT_H
#define ACCOUNT_H
#include<string>
#include "date.h"
#include<iostream>
using namespace std;
//Account类的定义
class Account { //账户类
private:
	string id;				//账号
	double balance;		//余额
	static double total;	//所有账户的总金额
protected:
	Account(const Date& date, const string& id);
	void record(const Date& date, double amount, const string& desc);
	void error(const string& msg) const;
public:
	const string& getId() const { return id; }
	double getBalance() const { return balance; }
	static double getTotal() { return total; }
	virtual void deposit(const Date& date, double amount, const string& desc) = 0; //  存现金
	virtual void withdraw(const Date& date, double amount, const string& desc) = 0;    //  取现金
	virtual void settle(const Date& date) = 0;      //结算年息
	virtual void show() const;
};

#endif 
