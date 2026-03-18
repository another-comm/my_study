#include "CreditCard.h"
#include <iostream>

CreditCard::CreditCard(string owner, string password, double initialDeposit)
    : Card(owner, password, initialDeposit) {
    creditLimit = initialDeposit * 1.5;  // 信用额度为存款的1.5倍
    incrementCardCount();
}

void CreditCard::displayInfo() const {
    cout << "信用卡 - 持卡人: " << *id << ", 余额: " << *balance << ", 信用额度: " << *balance*1.5 << endl;
}

void CreditCard::deposit(double amount) {
    Card::deposit(amount);  // 调用基类方法
}

void CreditCard::withdraw(double amount) {
    if ((*balance * 1.5) >= amount) {
        *balance -= amount;
        logAction("Withdrew " + to_string(amount));
    }
    else {
        cout << "超出信用额度！" << endl;
    }
}

double CreditCard::getCreditLimit() const {
    return creditLimit;
}
