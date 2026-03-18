#include "D:\\BankAccount\\S4\\S4_date.h"
#include "D:\\BankAccount\\S4\\S4_Account.h"
#include "D:\\BankAccount\\S4\\S4_accumulator.h"
#ifndef SAVINGSACCOUNT_H
#define SAVINGSACCOUNT_H
class SavingsAccount:public Account{
    private:
        Accumulator acc;
        double rate;
    public:
    SavingsAccount(Date date,string id,double rate);
    double getRate()const{return rate;}
    void deposit(Date date,double amount, string desc);
    void withdraw(Date date, double amount, string desc);
    void settle(Date date);
};
#endif