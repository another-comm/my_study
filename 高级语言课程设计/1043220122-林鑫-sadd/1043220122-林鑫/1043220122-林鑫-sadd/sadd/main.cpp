#include "sadd_CreditAccount.h"
int main()
{
    Date date(2008, 11, 1);
    CreditAccount ca(date, "C5392394", 10000, 0.0005, 50);
    ca.withdraw(Date(2008, 11, 15), 2000, "buy a cell");
    ca.settle(Date(2008, 12, 1));
    ca.deposit(Date(2008, 12, 1), 2016, "repay the credit");
    ca.settle(Date(2009, 1, 1));
    ca.show();
    ca.withdraw(Date(2009, 3, 5), 12000, "buy a new laptop");
    cout << "Total:" << CreditAccount::getTotal() << endl;
    return 0;
}