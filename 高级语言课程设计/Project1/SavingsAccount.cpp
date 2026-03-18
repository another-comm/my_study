#include <iostream>
using namespace std;
class SavingsAccount { 
private:
	int id;
	double balance;
	double rate;
	int lastDate;
	double accumulation;

	void record(int date, double amount); 
	double accumulate(int date) const; 

public:
	SavingsAccount(int date, long int id, double rate);
	long int getId() { return id; }
	double getBalance() { return balance; }
	double getRate() { return rate; }
	void deposit(int date, double amount);
	void withdraw(int date, double amount);
	void settle(int date);
	void show();

};

SavingsAccount::SavingsAccount(int date, long int id, double rate) :
	lastDate(date), id(id), rate(rate), balance(0), accumulation(0)
{
	cout << date << "\t#" << id << " is created" << endl;
}

void SavingsAccount::record(int date, double amount)
{
	accumulation = accumulate(date);
	balance += amount;
	lastDate = date;
	cout << date << "\t" << id << "\t" << amount << "\t" << balance << endl;

}

double SavingsAccount::accumulate(int date) const {
	return accumulation + balance * (date - lastDate);
}

void SavingsAccount::deposit(int date, double amount)
{
	record(date, amount);
}

void SavingsAccount::withdraw(int date, double amount)
{
	if (amount > balance)
		cout << "Error: not enough money" << endl;
	else
		record(date, -amount);
}

void SavingsAccount::settle(int date)
{
	double interest = accumulate(date) * rate / 365;
	if (interest != 0)
		record(date, interest);
	accumulation = 0;
}

void SavingsAccount::show()
{
	cout << "#" << id << "\tBalance:" << balance;
}

int main()
{//创建账户
	SavingsAccount sa0(1, 21325302, 0.015);
	SavingsAccount sa1(1, 58320212, 0.015);
	//几笔账目
	sa0.deposit(5, 5000);
	sa1.deposit(25, 10000);
	sa0.deposit(45, 5500);
	sa1.withdraw(60, 4000);
	//开户后第90天到了银行的计息日，结算所有账户的年息 
	sa0.settle(90);
	sa1.settle(90);
	//输出各个账户信息
	sa0.show(); cout << endl;
	sa1.show(); cout << endl;
	return 0;
}