#include "savingsaccount.h"

SavingsAccount::SavingsAccount(const Date& date, const string& id, double rate) :
    Account(date, id), acc(date, 0), rate(rate) {}


void SavingsAccount::deposit(const Date& date, double amount, const string& desc)
{
    record(date, amount, desc);
    acc.change(date, getBalance());
}

void SavingsAccount::withdraw(const Date& date, double amount, const string& desc)
{
    if (amount > getBalance())
        cout << "Error: not enough money" << endl;
    else
        record(date, -amount, desc);
    acc.change(date, getBalance());
}

void SavingsAccount::settle(const Date& date)
{
    if (date.getMonth() == 1)
    {
        double interest = acc.getSum(date) * rate / (date - Date(date.getYear() - 1, 1, 1));//计算利息
        if (interest != 0)
        {
            record(date, interest, "interest");
        }
        acc.reset(date, getBalance());//重置accumulation=0
    }
}

void SavingsAccount::show()const
{
    Account::show();
}
