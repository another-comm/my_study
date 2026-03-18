#include "Card.h"
#include <iostream>

// 初始化静态成员变量
int Card::CardCount = 0;

Card::Card(string owner, string password, double balance) {
    id = new string(owner);
    this->password = new string(password);
    this->balance = new double(balance);
}

Card::~Card() {
    logAction("Account destroyed");
    delete id;
    delete password;
    delete balance;
}

void Card::deposit(double amount) {
    *balance += amount;
    logAction("Deposited " + to_string(amount));
}

void Card::withdraw(double amount) {
    if (*balance >= amount) {
        *balance -= amount;
        logAction("Withdrew " + to_string(amount));
    }
    else {
        cout << "余额不足！" << endl;
    }
}

void Card::changePassword(string newPassword) {
    *password = newPassword;
    logAction("Password changed");
}

void Card::logAction(const string& action) {
    logs.push_back(action);
}

void Card::showLogs() const {
    cout << "卡号 " << *id << " 的操作日志：" << endl;
    for (const string& log : logs) {
        cout << log << endl;
    }
}

string Card::getCardNumber() const {
    return *id;
}

void print_information(Card& s) {
    cout << "卡号: " << *s.id << ", 余额: " << *s.balance << endl;
}


void Card::displayInfo() const {
 

}
