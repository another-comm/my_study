#ifndef SAVINGSACCOUNT_H
#define SAVINGSACCOUNT_H
#include <iostream>
using namespace std;
#include <cstring>
class SavingsAccount{
	private:
		string id;
		double balance;//余额 
		double rate;// 存款的年利率
		int lastDate;//上次变更余额的日期
		double accumulation;//余额按日累加之和 
		static double total;//所有账户的总金额 

		void record(int date, double amount);	//记录一笔帐，date为日期，amount为金额
		double accumulate(int date) const{
		return accumulation+balance*(date-lastDate);}//计算余额按日累加之和
	
	public:
		SavingsAccount(int date, string id, double rate);//构造函数
		string getId()const {return id;}
		double getBalance() const {return balance;}
		double getRate() const {return rate;}
		static double getTotal(){return total;}//Total函数实现 
		void deposit(int date, double amount);//存入现金
		void withdraw(int date, double amount) ;//取出现金
		void settle(int date);//结算利息
		void show() const;//显示账户信息
};
#endif
