#ifndef SAVINGSACCOUNT_H
#define SAVINGSACCOUNT_H
#include "Date.h"
#include<string>
using namespace std;

class SavingsAccount {
private:
    string id;
    double balance;
    double rate;
    Date lastDate;
    double accumulation;
    static double total; // 静态数据成员，记录总金额

    void error(string msg);
    void record(Date date, double amount,string desc);
    double accumulate(Date date) const;

public:
    SavingsAccount(Date date, string id, double rate);
    string getId() const { return id; }
    double getBalance() const { return balance; }
    double getRate() const { return rate; }
    void deposit(Date date, double amount,string desc);
    void withdraw(Date date, double amount,string desc);
    void settle(Date date);
    void show() const;
    static double getTotal() { return total; } // 静态成员函数
};

#endif