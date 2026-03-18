#include <iostream>
#include "DebitCard.h"
#include "CreditCard.h"

using namespace std;

int main() {
    // 创建卡片实例
    DebitCard debitCard1("张三", "password123", 1000);
    CreditCard creditCard1("李四", "password456", 2000);

    // 操作借记卡
    debitCard1.displayInfo();
    debitCard1.deposit(500);  // 存款500
    debitCard1.displayInfo();
    debitCard1.withdraw(2000);  // 取款2000
    debitCard1.showLogs();  // 显示日志

    // 操作信用卡
    creditCard1.displayInfo();
    creditCard1.deposit(500);  // 存款500
    creditCard1.displayInfo();
    creditCard1.withdraw(2000);  
    creditCard1.displayInfo();
    creditCard1.showLogs();  // 显示日志

    return 0;
}
