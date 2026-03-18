#ifndef ACCOUNT_H
#define ACCOUNT_H
#include "D:\\BankAccount\\S4\\S4_date.h"
#include <cstring>
class Account{
    private:
        string id;
        double balance;
        static double total;
    protected:
        Account(Date date, string id);
        void record(Date date, double amount, string desc);
        void error(string msg)const;
    public:
        string getId()const{return id;}
        double getBalance()const{return balance;}
        void show()const;
        static double getTotal(){return total;};

}; 
#endif