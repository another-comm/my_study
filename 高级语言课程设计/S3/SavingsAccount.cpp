#include "SavingsAccount.h"

double SavingsAccount::total = 0; // 静态成员初始化

SavingsAccount::SavingsAccount(Date date, string id, double rate)
    : lastDate(date), id(id), rate(rate), balance(0), accumulation(0)
{
    date.show();
    cout  << "\t#" << id << " is created" << endl;
}


void SavingsAccount::error(string msg) {
    cout << "Error" << "(# " << id << "):" << msg << endl;
}

double SavingsAccount::accumulate(Date date) const {
    return accumulation + balance * (date.distance(lastDate));
}

void SavingsAccount::record(Date date, double amount,string desc)
{
    accumulation = accumulate(date);
    balance += amount;
    lastDate = date;
    total += amount; // 更新总金额
    date.show();
    cout  << "\t" << id << "\t" << amount << "\t" << balance  << "\t" << desc <<endl;
}

void SavingsAccount::deposit(Date date, double amount,string desc)
{
    record(date, amount,desc);
}

void SavingsAccount::withdraw(Date date, double amount,string desc)
{
    if (amount > balance)
        error("Error: not enough money");
    else
        record(date, -amount,desc);
}

void SavingsAccount::settle(Date date)
{
    int y = date.getYear();
    double interest = rate * accumulate(date) / Date(y,1,1).distance(Date(y-1,1,1));
    if (interest != 0)
        record(date, interest,"interest");
    accumulation = 0;
}

void SavingsAccount::show() const
{
    cout << "#" << id << "\tBalance:" << balance;
}
