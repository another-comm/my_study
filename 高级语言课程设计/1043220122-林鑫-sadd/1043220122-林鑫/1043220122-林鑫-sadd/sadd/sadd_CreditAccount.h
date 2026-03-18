#include "sadd_Date.h"
class CreditAccount {
private:
    string id;                // 信用卡账号
    double balance;           // 信用卡余额
    double rate;              // 欠款的日利率
    Date lastDate;            // 上次更改余额的日期
    double accumulation;      // 余额按日累加和
    double fee;               // 年费
    double credit;            // 信用卡的信用额度
    static double total;      // 所有账户的总金额

    void record(Date date, double amount, string desc); // 记录一笔账，date为日期，amount为金额
    double accumulate(Date date) const;

public:
    CreditAccount(Date date, string id, double credit, double rate, double fee);
    string getId() const { return id; }
    double getBalance() const { return balance; }
    double getRate() const { return rate; }
    double getFee() const { return fee; }
    double getCredit() const { return credit; } // 信用额度
    static double getTotal() { return total; }  // Total函数实现
    void deposit(Date date, double amount, string desc); // 存入现金
    void withdraw(Date date, double amount, string desc); // 取出现金
    void settle(Date date); // 结算利息
    void show() const;      // 显示账户信息
    double getAvailableCredit() const; // 可用的信用额度
    void error(string msg);
};