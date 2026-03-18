#include "D:\\BankAccount\\S4\\S4_date.h"
#include "D:\\BankAccount\\S4\\S4_Account.h"
#include "D:\\BankAccount\\S4\\S4_accumulator.h"
#ifndef CREDITACCOUNT_H
#define CREDITACCOUNT_H
class CreditAccount:public Account{
    private:
        Accumulator acc;
        double credit;
        double rate;
        double fee;
        double getDebt()const;
    public:
        CreditAccount(Date date, string id,double credit,double rate, double fee);
        double getCredit()const{return credit;}
        double getRate()const{return rate;}
        double getFee()const{return fee;}
        double getAvailableCredit()const;
        void deposit(Date date,double amount, string desc);
        void withdraw(Date date,double amount, string desc);
        void settle(Date date);
        
}; 
#endif