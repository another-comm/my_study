#pragma once
#ifndef CREDITCARD_H
#define CREDITCARD_H

#include "Card.h"

class CreditCard : public Card {
public:
    CreditCard(string owner, string password, double initialDeposit);

    // 重写虚函数
    void displayInfo() const;
    void deposit(double amount);
    void withdraw(double amount);

    double getCreditLimit() const;  // 获取信用额度
    static void incrementCardCount() {
        Card::CardCount++;
    }

private:
    double creditLimit;
};

#endif
