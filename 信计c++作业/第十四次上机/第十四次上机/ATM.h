#ifndef ATM_H
#define ATM_H

#include <vector>
#include <iostream>
using namespace std;

template <typename T>
class ATM {
private:
    vector<T*> cards;  // 使用模板存储银行卡
    T* currentCard;    // 当前插入的卡

public:
    ATM() : currentCard(nullptr) {}

    // 添加银行卡
    void addCard(T* card) {
        cards.push_back(card);
    }

    // 模拟插卡操作
    void insertCard(const string& cardNumber) {
        for (T* card : cards) {
            if (card->getCardNumber() == cardNumber) {
                currentCard = card;
                cout << "已插入卡号: " << cardNumber << endl;
                return;
            }
        }
        cout << "未找到卡号: " << cardNumber << endl;
    }

    // 模拟取卡操作
    void ejectCard() {
        if (currentCard) {
            cout << "卡号 " << currentCard->getCardNumber() << " 已取出。" << endl << endl ;
            currentCard = nullptr;
        }
        else {
            cout << "当前没有插入任何卡。" << endl;
        }
    }

    // 显示当前卡片信息
    void displayCurrentCardInfo() {
        if (currentCard) {
            currentCard->displayInfo();
        }
        else {
            cout << "当前没有插入任何卡。" << endl;
        }
    }

    // 执行存款
    void deposit(double amount) {
        if (currentCard) {
            currentCard->deposit(amount);
        }
        else {
            cout << "当前没有插入任何卡。" << endl;
        }
    }

    // 执行取款
    void withdraw(double amount) {
        if (currentCard) {
            currentCard->withdraw(amount);
        }
        else {
            cout << "当前没有插入任何卡。" << endl;
        }
    }

    // 修改密码
    void changePassword(const string& newPassword) {
        if (currentCard) {
            currentCard->changePassword(newPassword);
        }
        else {
            cout << "当前没有插入任何卡。" << endl;
        }
    }

    // 显示操作日志
    void showLogs() {
        if (currentCard) {
            currentCard->showLogs();
        }
        else {
            cout << "当前没有插入任何卡。" << endl;
        }
    }

    ~ATM() {
        for (T* card : cards) {
            delete card;  // 清理动态分配的内存
        }
        cards.clear();
    }
};

#endif
