#include <iostream>
#include "DebitCard.h"
#include "CreditCard.h"

using namespace std;

int main() {
    DebitCard debit("12121212", "123456", 1000.0);
    CreditCard credit("000012121", "abcdef", 2000.0);

    // 使用 << 运算符直接输出对象
    cout << debit << endl;
    cout << credit << endl;

    return 0;
}