#include <iostream>
#include <string>
#include <vector>
using namespace std;

class bank {
public:
    static int debitCardCount;
    static int return_debitCardCount()
    {
        return debitCardCount;
    }

    bank() 
    {
        id = new string("11111");
        password = new string("666666");
        balance = new int(0);
  
    };
    bank(const bank& s) 
    {
        id = new string(*s.id);
        password = new string(*s.password);
        balance = new int(*s.balance);
        logs = s.logs;
    }
    ;
    bank(const string& cardNumber)
    {
        id = new string(cardNumber);
        password = new string("666666");
        balance = new int(0);

    }
    ~bank() {
        addlog("您已成功销毁此卡");
        delete id;
        delete password;
        delete balance;
       
    };

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
    static bank openNewAccount11(string& s);
    void printLogs() const;
    void printbalance() const;
    void changeCard();

    // 使用友元打印账户信息
    friend void print_information(bank& s);

private:
    void addlog(const string& message);

protected:
    string* id;
    string* password;
    int* balance;
    vector<string> logs;
};
int bank::debitCardCount = 0;

class CreditCard : public bank 
{
public:
    CreditCard() : creditLimit(0) {}

    // 接收卡号和初始存款的构造函数
    CreditCard(const string& cardNumber, int initialDeposit)
        : bank(cardNumber), creditLimit(initialDeposit * 1.5) {
        new_deposit(initialDeposit);
    }

    // 获取信用额度
    double getCreditLimit() const { return creditLimit; }

    // 打印信用卡信息
    void printCreditInfo() const {
        cout << "信用卡信息 - 账户ID: " << *id
            << ", 信用额度: " << creditLimit
            << ", 余额: " << *balance << " 元" << endl;
    }

private:
    double creditLimit;
};

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
    debitCardCount++;
    return newaccount;
}
// 创建仅使用一个卡号的信用卡
bank bank::openNewAccount11(string& s) {
    bank newaccount(s);
    newaccount.addlog("创建一个新账户");
    cout << "您已成功创建一个新账户" << endl;
    debitCardCount++;
    return newaccount;
}

// 换卡功能
void bank::changeCard() {
    addlog("账户已更换为新卡");
    cout << "您的账户已成功更换!" << endl;

    string* oldId = id;
    string* oldPassword = password;
    int* oldBalance = balance;

    id = new string(*oldId);
    password = new string(*oldPassword);
    balance = new int(*oldBalance);

    delete oldId;
    delete oldPassword;
    delete oldBalance;
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
//使用友元直接打印
void print_information(bank& s) {
    cout << "您的银行卡信息如下: \n"
        << "银行卡ID: " << *s.id << endl
        << "银行卡余额: " << *s.balance << endl;
}
int get_account()
{
    cout << "请输入要操作的账户: ";
    int i; cin >> i;
    return i;
}


int main() {
    vector <bank> account;
    bool running = true;
    cout << "请选择您的操作:\n"
        << "1、创建新账户\n"
        << "2、修改密码\n"
        << "3、查询余额\n"
        << "4、存款\n"
        << "5、取款\n"
        << "6、查询明细\n"
        << "7、结束\n"
        << "8、换卡\n"
        << "9、打印银行卡信息\n"
        << "10、查询银行卡数量\n"
        << "11、新建信用卡\n"
        << "12、创建仅使用一个卡号的银行卡\n"
        << "13、删除账户\n";

       

    while (running) {
        int a;
        cout << endl << "输入操作编号: ";
        cin >> a;

        switch (a) {
        case 1: {
            account.emplace_back(bank::openNewAccount());
            break;
        }
        case 2: {
            
                int i = get_account()-1;
                string newpassword;
                cout << "请输入您的新密码: ";
                cin >> newpassword;
                account[i].setnewpassword(newpassword);
            
 
            break;
        }
        case 3: {
            int i = get_account() - 1;
            account[i].printbalance();
            break;
        }
        case 4: {
                int i = get_account() - 1;
                int amount1;
                cout << "请输入您想存款的数目: ";
                cin >> amount1;
                account[i].new_deposit(amount1);
   
            break;
        }
        case 5: {
            int i = get_account() - 1;
       
                int amount2;
                cout << "请输入您想取款的数目: ";
                cin >> amount2;
                account[i].new_withdrawal(amount2);
       
            break;
        }
        case 6: {
            int i = get_account() - 1;
            for(int j=0;j<=i;j++)
                 account[j].printLogs();
            break;
        }
        case 7: {
            running = false;
            cout << "操作结束，感谢您的使用!" << endl;
            break;
        }
        case 8: {
                int i = get_account() - 1;
                account[i].changeCard();
            break;
        }
        case 9: {
                int i = get_account() - 1;
                print_information(account[i]);
            break;
        }
        case 10: {
          
                cout << "当前借记卡总数量为: "
                    << bank::return_debitCardCount() << endl;
            break;
        }
        case 11: {
                int i = get_account() - 1;
        
                CreditCard creditCard(account[i].getnewbankid(), account[i].getbalance());
                creditCard.printCreditInfo();  // 打印信用卡信息
            
            break;
        }

        case 12: {
     
                string s1;
                cout << "请输入卡号: \n";
                cin >> s1;
                account.emplace_back(bank::openNewAccount11(s1));

                break;
            
        }
        case 13: {
            int i = get_account() - 1;
            account[i].~bank();
            cout << "您已成功删除账户" << i + 1 << endl;
            bank::debitCardCount --;
            break;
        }
        default:
            cout << "无效的操作编号，请重新输入!" << endl;
        }
        

    }
    
    return 0;
}
