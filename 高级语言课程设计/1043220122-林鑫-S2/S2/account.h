#ifndef ACCOUNT_H
#define ACCOUNT_H

#include <iostream>
using namespace std;

class SavingsAccount {
private:
    long int id;
    double balance;
    double rate;
    int lastDate;
    double accumulation;
    static double total; // 静态数据成员，记录总金额

    void record(int date, double amount);
    double accumulate(int date) const;

public:
    SavingsAccount(int date, long int id, double rate);
    long int getId() const { return id; }
    double getBalance() const { return balance; }
    double getRate() const { return rate; }
    void deposit(int date, double amount);
    void withdraw(int date, double amount);
    void settle(int date);
    void show() const;
    static double getTotal() { return total; } // 静态成员函数
};

#endif