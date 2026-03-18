#include "S4_SavingsAccount.h"
#include "S4_CreditAccount.h"
#include<vector>
using namespace std;
int main() {

	vector<SavingsAccount> accounts;
	accounts.emplace_back(Date(2008, 11, 1), "03755217", 0.015);
	accounts.emplace_back(Date(2008, 11, 1), "02342342", 0.015);
	accounts[0].deposit(Date(2008, 11, 5), 5000, "salary");
	accounts[1].deposit(Date(2008, 11, 25), 10000, "sell stock 0323");
	accounts[0].deposit(Date(2008, 12, 5), 5500, "salary");
	accounts[1].withdraw(Date(2008, 12, 20), 4000, "buy a laptop");
	cout << endl;
	for (int i = 0; i < accounts.size(); i++)
	{
		accounts[i].settle(Date(2009, 1, 1));
		accounts[i].show();
		cout << endl;
	}
	accounts[1].withdraw(Date(2009, 5, 1), 400000, "buy a car");
	cout << "Total: " << SavingsAccount::getTotal() << endl;
	cout << endl;

	Date date(2008, 11, 1);
	CreditAccount ca(date, "C5392394", 10000, 0.0005, 50);
	ca.withdraw(Date(2008, 11, 15), 2000, "buy a cell");
	ca.settle(Date(2008, 12, 1));
	ca.deposit(Date(2008, 12, 1), 2016, "repay the credit");
	ca.settle(Date(2009, 1, 1));
	ca.show(); 
	cout << "Available credit: " << ca.getAvailableCredit() << endl;
	ca.withdraw(Date(2009, 3, 5), 12000, "buy a new laptop");
	cout << "Total:" << CreditAccount::getTotal() << endl;
	return 0;
}