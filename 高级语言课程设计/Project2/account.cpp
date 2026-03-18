#include "account.h"

double SavingsAccount::total = 0; // 静态成员初始化

SavingsAccount::SavingsAccount(int date, long int id, double rate)
    : lastDate(date), id(id), rate(rate), balance(0), accumulation(0)
{
    cout << date << "\t#" << id << " is created" << endl;
}


double SavingsAccount::accumulate(int date) const {
    return accumulation + balance * (date - lastDate);
}

void SavingsAccount::record(int date, double amount)
{
    accumulation = accumulate(date);
    balance += amount;
    lastDate = date;
    total += amount; // 更新总金额
    cout << date << "\t" << id << "\t" << amount << "\t" << balance << endl;
}

void SavingsAccount::deposit(int date, double amount)
{
    record(date, amount);
}

void SavingsAccount::withdraw(int date, double amount)
{
    if (amount > balance)
        cout << "Error: not enough money" << endl;
    else
        record(date, -amount);
}

void SavingsAccount::settle(int date)
{
    double interest = accumulate(date) * rate / 365;
    if (interest != 0)
        record(date, interest);
    accumulation = 0;
}


void SavingsAccount::show() const
{
    cout << "#" << id << "\tBalance:" << balance;
}
