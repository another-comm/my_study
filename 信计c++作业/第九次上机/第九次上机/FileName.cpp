#include<iostream>
#include<cstring>
#include<vector>
using namespace std;

class bank {
public:
    bank();
    bank(const bank& s);
    ~bank();

    string getnewbankid() const { return *id; }
    void setnewbankid(string id1) {
        *id = id1;
        logs.push_back("您的账户是 " + id1);
        cout << "您的账户是： " << id1 << endl;
    }

    string getnewpassword() const { return *password; }
    void setnewpassword(string pass) {
        *password = pass;
        logs.push_back("您的密码更改为 " + pass);
        cout << "更改密码成功." << endl;
    }

    int getbalance() const { return *balance; }
    void new_deposit(int amount);
    void new_withdrawal(int amount);

    static bank openNewAccount();
    void printLogs() const;
    void printbalance();

protected:
    string* id;
    string* password;
    int* balance;
    vector<string> logs;

};

// 默认构造函数
bank::bank() {
    id = new string;
    *id = "11111"; // 初始化账户ID为字符串
    password = new string;
    *password = "666666"; // 初始化密码
    balance = new int;
    *balance = 0; // 初始余额为0
}

// 拷贝构造函数
bank::bank(const bank& s) {
    id = new string;
    *id = *s.id;
    password = new string;
    *password = *s.password;
    balance = new int;
    *balance = *s.balance;
}

// 析构函数
bank::~bank() {
    delete id;
    delete password;
    delete balance;
}

// 存款操作
void bank::new_deposit(int amount) {
    *balance += amount;
    logs.push_back("存款 " + (amount)); // 使用 to_string 转换 int 为字符串
    cout << "您已成功存款: " << amount << "元" << endl;
}

// 取款操作
void bank::new_withdrawal(int amount) {
    if (*balance >= amount) {
        *balance -= amount;
        logs.push_back("取款: " + (amount));
        cout << "您已成功取款 " << amount << "元" << endl;
    }
    else {
        cout << "余额不足，无法取款。" << endl;
    }
}

// 创建新账户
bank bank::openNewAccount() {
    bank newaccount;
    logs.push_back("创建一个新账户");
    cout << "您已成功创建一个新账户" << endl;
    return newaccount;
}

// 打印日志记录
void bank::printLogs() const {
    for (auto it = logs.begin(); it != logs.end(); ++it) {
        cout << *it << endl;
    }
}

// 打印余额
void bank::printbalance() {
    cout << "您当前的余额是: " << *balance << "元" << endl;
}

int main() {
    bank now_account;
    bool bb = true;  // 初始化 bb 为 true

    while (bb) {
        cout << "\n请选择您的操作:\n"
            << "1、创建新账户\n"
            << "2、修改密码\n"
            << "3、查询余额\n"
            << "4、存款\n"
            << "5、取款\n"
            << "6、查询明细\n"
            << "7、结束\n";

        int a;
        cin >> a;

        switch (a) {
        case 1: {
            now_account = bank::openNewAccount(); // 创建新账户
            break;
        }
        case 2: {
            string newpassword;
            cout << "请输入您的新密码: ";
            cin >> newpassword;
            now_account.setnewpassword(newpassword); // 修改密码
            break;
        }
        case 3: {
            now_account.printbalance(); // 查询余额
            break;
        }
        case 4: {
            int amount1;
            cout << "请输入您想存款的数目: ";
            cin >> amount1;
            now_account.new_deposit(amount1); // 存款
            break;
        }
        case 5: {
            int amount2;
            cout << "请输入您想取款的数目: ";
            cin >> amount2;
            now_account.new_withdrawal(amount2); // 取款
            break;
        }
        case 6: {
            now_account.printLogs(); // 查询明细
            break;
        }
        case 7: {
            bb = false;
            cout << "操作结束，感谢您的使用!" << endl; // 结束程序
            break;
        }
        default:
            cout << "无效输入，请重新选择。\n";
        }
    }

    return 0;
}
