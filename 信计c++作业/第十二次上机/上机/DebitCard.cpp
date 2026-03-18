#include "DebitCard.h"
#include <iostream>

DebitCard::DebitCard(string owner, string password, double initialDeposit)
    : Card(owner, password, initialDeposit) {
    incrementCardCount();
}

void DebitCard::displayInfo() const {
    cout << "借记卡 - 持卡人: " << *id << ", 余额: " << *balance << endl;
}

void DebitCard::deposit(double amount) {
    Card::deposit(amount);  // 调用基类方法
}

void DebitCard::withdraw(double amount) {
    Card::withdraw(amount);  // 调用基类方法
}

DebitCard DebitCard::openNewAccount() {
    DebitCard newCard("新用户", "123456", 0.0);
    incrementCardCount();
    return newCard;
}

DebitCard DebitCard::openNewAccountByCardNumber(string cardNumber) {
    DebitCard newCard(cardNumber, "123456", 0.0);
    incrementCardCount();
    return newCard;
}

