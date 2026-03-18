#include <iostream>
#include <string>
#include <vector>
using namespace std;

class bank {
public:
    bank();
    bank(const bank& s);
    ~bank();

    string getnewbankid() const { return *id; }
    void setnewbankid(string id1) {
        *id = id1;
        addlog("您的账户是 " + id1);
        cout << "您的账户是： " << id1 << endl;
    }

    string getnewpassword() const { return *password; }
    void setnewpassword(string pass) {
        *password = pass;
        addlog("您的密码更改为 " + pass);
        cout << "更改密码成功." << endl;
    }

    int getbalance() const { return *balance; }
    void new_deposit(int amount);
    void new_withdrawal(int amount);

    static bank openNewAccount();
    void printLogs() const;
    void printbalance() const;
    void changeCard();  

private:
    void addlog(const string& message);

protected:
    string* id;
    string* password;
    int* balance;
    vector<string> logs;
};

// 默认构造函数
bank::bank() {
    id = new string("11111");
    password = new string("666666");
    balance = new int(0);
}

// 拷贝构造函数
bank::bank(const bank& s) {
    id = new string(*s.id);
    password = new string(*s.password);
    balance = new int(*s.balance);
    logs = s.logs;
}

// 析构函数
bank::~bank() {
    addlog("您已成功销毁此卡");
    delete id;
    delete password;
    delete balance;
}

// 存款
void bank::new_deposit(int amount) {
    *balance += amount;
    addlog("存款 " + to_string(amount) + " 元");
    cout << "您已成功存款: " << amount << " 元" << endl;
}

// 取款
void bank::new_withdrawal(int amount) {
    if (amount <= *balance) {
        *balance -= amount;
        addlog("取款 " + to_string(amount) + " 元");
        cout << "您已成功取款 " << amount << " 元" << endl;
    }
    else {
        cout << "余额不足，无法取款!" << endl;
    }
}

// 新办卡功能
bank bank::openNewAccount() {
    bank newaccount;
    newaccount.addlog("创建一个新账户");
    cout << "您已成功创建一个新账户" << endl;
    return newaccount;
}

// 换卡功能
void bank::changeCard() {
    bank newAccount(*this); 
    addlog("账户已更换为新卡");
    cout << "您的账户已成功更换!" << endl;

  
    delete id;
    delete password;
    delete balance;

   
    id = new string(*newAccount.id);
    password = new string(*newAccount.password);
    balance = new int(*newAccount.balance);  
}


// 打印日志
void bank::printLogs() const {
    cout << "账户操作明细:" << endl;
    for (const auto& log : logs) {
        cout << log << endl;
    }
}

// 打印余额
void bank::printbalance() const {
    cout << "您当前的余额是: " << *balance << " 元" << endl;
}

// 添加日志
void bank::addlog(const string& message) {
    logs.push_back(message);
}

int main() {
    bank* now_account = nullptr; 
    bool running = true;
    cout << "请选择您的操作:\n"
        << "1、创建新账户\n"
        << "2、修改密码\n"
        << "3、查询余额\n"
        << "4、存款\n"
        << "5、取款\n"
        << "6、查询明细\n"
        << "7、结束\n"
        << "8、换卡\n"; 

    while (running) {
        int a;
        cout << endl << "输入操作编号: ";
        cin >> a;

        switch (a) {
        case 1: {
            delete now_account; // 删除旧账户
            now_account = new bank(bank::openNewAccount()); // 创建新账户
            break;
        }
        case 2: {
            if (now_account) {
                string newpassword;
                cout << "请输入您的新密码: ";
                cin >> newpassword;
                now_account->setnewpassword(newpassword);
            }
            else {
                cout << "请先创建新账户！" << endl;
            }
            break;
        }
        case 3: {
            if (now_account) now_account->printbalance();
            else cout << "请先创建新账户！" << endl;
            break;
        }
        case 4: {
            if (now_account) {
                int amount1;
                cout << "请输入您想存款的数目: ";
                cin >> amount1;
                now_account->new_deposit(amount1);
            }
            else {
                cout << "请先创建新账户！" << endl;
            }
            break;
        }
        case 5: {
            if (now_account) {
                int amount2;
                cout << "请输入您想取款的数目: ";
                cin >> amount2;
                now_account->new_withdrawal(amount2);
            }
            else {
                cout << "请先创建新账户！" << endl;
            }
            break;
        }
        case 6: {
            if (now_account) now_account->printLogs();
            else cout << "请先创建新账户！" << endl;
            break;
        }
        case 7: {
            running = false;
            cout << "操作结束，感谢您的使用!" << endl;
            break;
        }
        case 8: {  
            if (now_account) {
                now_account->changeCard();
            }
            else {
                cout << "请先创建新账户！" << endl;
            }
            break;
        }
        default:
            cout << "无效的操作编号，请重新输入!" << endl;
        }
    }
    delete now_account; // 退出时清理内存
    return 0;
}
