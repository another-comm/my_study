#include "CreditCard.h"
#include <iostream>

CreditCard::CreditCard(string owner, string password, double initialDeposit)
    : Card(owner, password, initialDeposit) {
    creditLimit = initialDeposit * 1.5;  
    incrementCardCount();// 信用卡额度为存款的1.5倍
}

void CreditCard::displayInfo()  {
    cout << "Credit Card - Owner: " << *id << ", Balance: " << *balance << ", Credit Limit: " << creditLimit << endl;
}

void CreditCard::deposit(double amount) {
    Card::deposit(amount);  // 调用基类方法
}

void CreditCard::withdraw(double amount) {
    if ((*balance *1.5) >= amount) {
        *balance -= amount;
        logAction("Withdrew " + to_string(amount));
    }
    else {
        cout << "Exceeds credit limit!" << endl;
    }
}

double CreditCard::getCreditLimit() const {
    return *balance*1.5;
}
