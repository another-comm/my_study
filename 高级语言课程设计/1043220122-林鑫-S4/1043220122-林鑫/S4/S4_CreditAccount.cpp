#include "S4_CreditAccount.h"
CreditAccount::CreditAccount(Date date, string id, double credit, double rate, double fee):
	Account(date,id),acc(date,0),credit(credit),rate(rate),fee(fee)
{
	date.show();
	cout << "\t#" << id << " is created" << endl;
}

double CreditAccount::getDebt() const
{
    return getBalance() < 0 ? getBalance() : 0;
}
double CreditAccount::getAvailableCredit()const
{
    return credit + getDebt();
}

void CreditAccount::deposit(Date date, double amount, string desc)
{
    
    record(date, amount, desc);
    acc.change(date, getDebt());
}

void CreditAccount::withdraw(Date date, double amount, string desc)
{
    if (amount > getAvailableCredit()) {
        error("Error: not enough credit");
    }
    else {
        
        record(date, -amount, desc);
        acc.change(date, getDebt());
    }
}

void CreditAccount::settle(Date date)
{
    double interest = 0;
    interest = -acc.getSum(date) * rate;
    if (interest != 0)
    {
        acc.change(date, getDebt() - interest);
        record(date, -interest, "interest");
    }
    if (date.getMonth()==1)
    {
        record(date, -fee, "annual fee");
        acc.change(date, getDebt() );
    }
    acc.reset(date, getDebt());
}