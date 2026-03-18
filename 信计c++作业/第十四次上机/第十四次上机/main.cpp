#include <iostream>
#include "ATM.h"
#include "DebitCard.h"
#include "CreditCard.h"

int main() {
    // 创建ATM实例，支持Card基类及其派生类
    ATM<Card> atm;

    // 创建一些银行卡
    Card* debitCard1 = new DebitCard("1043220122", "1234", 1000);
    Card* debitCard2 = new DebitCard("1043220123", "5678", 2000);
    Card* creditCard = new CreditCard("1043220124", "4321", 1500);

    // 添加银行卡到ATM
    atm.addCard(debitCard1);
    atm.addCard(debitCard2);
    atm.addCard(creditCard);

    // 插入卡并进行操作
    atm.insertCard("1043220122");
    atm.displayCurrentCardInfo();
    atm.deposit(500);
    atm.withdraw(300);
    atm.changePassword("1111");
    atm.showLogs();
    atm.ejectCard();

    atm.insertCard("1043220124");
    atm.displayCurrentCardInfo();
    atm.deposit(500);
    atm.withdraw(300);
    atm.withdraw(4000);  // 超出信用额度
    atm.showLogs();
    atm.ejectCard();

    return 0;
}

