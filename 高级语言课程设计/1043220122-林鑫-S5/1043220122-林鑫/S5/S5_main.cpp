#include "S5_SavingsAccount.h"
#include "S5_CreditAccount.h"
#include<vector>
using namespace std;
int main() {

	vector<Account*> accounts;
	Date date(2008, 11, 1);
	accounts.push_back(new SavingsAccount( date, "03755217", 0.015));
	accounts.push_back(new SavingsAccount(date, "02342342", 0.015));
	accounts.push_back(new CreditAccount(date, "C5392394", 10000, 0.0005, 50));
	accounts.push_back(new CreditAccount(Date(2008, 3, 20), "C5392398", 10000, 0.0005, 50));
	accounts[0]->deposit(Date(2008, 11, 5), 5000, "salary");
	accounts[1]->deposit(Date(2008, 11, 25), 10000, "sell stock 0323");
	accounts[0]->deposit(Date(2008, 12, 5), 5500, "salary");
	accounts[1]->withdraw(Date(2008, 12, 20), 4000, "buy a laptop");
	accounts[2]->withdraw(Date(2008, 11, 15), 2000, "buy a cell");
	accounts[2]->settle(Date(2008, 12, 1));
	accounts[2]->deposit(Date(2008, 12, 1), 2016, "repay the credit");
	accounts[3]->withdraw(Date(2008, 3, 28), 3000, "buy a monitor");
	accounts[3]->settle(Date(2008, 12, 1));
	accounts[3]->deposit(Date(2008, 12, 1), 3500, "repay the credit");
	
	for (int i = 0; i < accounts.size(); i++)
	{
		accounts[i]->settle(Date(2009, 1, 1));
		accounts[i]->show();
		cout << endl;
	}
	accounts[1]->withdraw(Date(2009, 5, 1), 400000, "buy a car");
	accounts[2]->withdraw(Date(2009, 3, 5), 12000, "buy a new laptop");
	accounts[3]->withdraw(Date(2009, 4, 5), 5000, "buy a new laptop");
	cout << "Total: " << Account::getTotal() << endl;
	cout << endl;
	return 0;
}