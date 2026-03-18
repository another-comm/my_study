#include "SavingsAccount.h"
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


	return 0;
}