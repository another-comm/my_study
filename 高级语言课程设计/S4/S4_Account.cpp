#include "S4_Account.h"
double Account::total = 0;

Account::Account(Date date, string id) :id(id), balance(0) {}

void Account::record(Date date, double amount, string desc) {
    balance += amount;
    total += amount; // 更新总金额
    date.show();
    cout << "\t" << id << "\t" << amount << "\t" << balance << "\t" << desc << endl;
}

void Account::error(string msg) const
{
    cout << "Error (#" << id << "): " << msg << endl;
}

void Account::show() const {
    cout << "#" << id << "\tBalance: " << balance << endl;
}