#include <iostream>
#include "DebitCard.h"
#include "CreditCard.h"
#include <vector>

using namespace std;

int main() {
    vector<Card*> accounts;  // 存储指向Card对象的指针
    bool running = true;

    cout << "Choose an option:\n"
        << "1. Create new Debit Card\n"
        << "2. Create new Credit Card\n"
        << "3. Deposit\n"
        << "4. Withdraw\n"
        << "5. Change password\n"
        << "6. Show logs\n"
        << "7. Show card info\n"
        << "8. Show card count\n"
        << "9. Exit\n";

    while (running) {
        int choice;
        cout << "Enter choice: ";
        cin >> choice;

        switch (choice) {
        case 1: {
            // 创建新借记卡并将其加入到账户列表
            DebitCard* newCard = new DebitCard("Alice", "123456", 500);  // 使用new动态分配内存
            accounts.push_back(newCard);
            break;
        }
        case 2: {
            // 创建新信用卡并将其加入到账户列表
            CreditCard* newCard = new CreditCard("Bob", "password", 1000);  // 使用new动态分配内存
            accounts.push_back(newCard);
            break;
        }
        case 3: {
            int accountIdx;
            cout << "Enter account index to deposit: ";
            cin >> accountIdx;
            double amount;
            cout << "Enter deposit amount: ";
            cin >> amount;
            accounts[accountIdx]->deposit(amount);
            break;
        }
        case 4: {
            int accountIdx;
            cout << "Enter account index to withdraw: ";
            cin >> accountIdx;
            double amount;
            cout << "Enter withdrawal amount: ";
            cin >> amount;
            accounts[accountIdx]->withdraw(amount);
            break;
        }
        case 5: {
            int accountIdx;
            cout << "Enter account index to change password: ";
            cin >> accountIdx;
            string newPassword;
            cout << "Enter new password: ";
            cin >> newPassword;
            accounts[accountIdx]->changePassword(newPassword);
            break;
        }
        case 6: {
            int accountIdx;
            cout << "Enter account index to view logs: ";
            cin >> accountIdx;
            accounts[accountIdx]->showLogs();
            break;
        }
        case 7: {
            int accountIdx;
            cout << "Enter account index to view info: ";
            cin >> accountIdx;
            accounts[accountIdx]->displayInfo();
            break;
        }
        case 8: {
            cout << "Debit card count: " << Card::getCardCount() << endl;
            break;
        }
        case 9:
            running = false;
            cout << "Exiting program. Thank you!" << endl;
            // 删除所有卡片对象，释放内存
            for (auto card : accounts) {
                delete card;  // 删除每个指针指向的对象
            }
            break;
        default:
            cout << "Invalid choice. Please try again." << endl;
        }
    }

    return 0;
}
