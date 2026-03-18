#ifndef CARD_H
#define CARD_H

#include <string>
#include <vector>
#include <iostream>
#include <ctime>

using namespace std;

class Card {
public:
    static int CardCount;  // 只声明，不定义

    static int getCardCount() {
        return CardCount;
    }

    // 构造函数
    Card(string owner, string password, double balance);

    // 虚析构函数
    virtual ~Card();

    // 存款、取款、改密码等基础功能
    void deposit(double amount);        // 存款
    void withdraw(double amount);       // 取款
    void changePassword(string newPassword);  // 改密码
    virtual void displayInfo() const;   // 显示卡片信息

    // 记录日志
    void logAction(const string& action);
    void showLogs() const;

    // 获取卡号
    string getCardNumber() const;

    // 友元函数，用于打印银行卡信息
    friend void print_information(Card& s);

protected:
    string* id;
    string* password;
    double* balance;
    vector<string> logs;
};



#endif
