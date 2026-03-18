#ifndef DEBITCARD_H
#define DEBITCARD_H

#include "Card.h"

class DebitCard : public Card {
public:
    DebitCard(string owner, string password, double initialDeposit);

    void displayInfo() ;
    void deposit(double amount) ;
    void withdraw(double amount) ;

    static DebitCard openNewAccount();
    static DebitCard openNewAccountByCardNumber(string cardNumber);
    static void incrementCardCount() {
        Card::CardCount++;
    }
    // 打印账户信息
    void printAccountInfo() ;
};

#endif
