#include "D:\\BankAccount\\S4\\S4_CreditAccount.h"
CreditAccount::CreditAccount(Date date, string id,double credit,double rate, double fee):
Account(date,id),credit(credit),rate(rate),fee(fee),acc(date,0){}
double CreditAccount::getDebt()const
{
    double balance=getBalance();
	return (balance<0?balance:0);

}
double CreditAccount::getAvailableCredit()const
{
    return credit+getBalance();
}
void CreditAccount::deposit(Date date,double amount, string desc)
{
    record(date,amount,desc);
    acc.change(date,getDebt());
}
void CreditAccount::withdraw(Date date,double amount, string desc)
{
    if(amount-getBalance()>credit)
	    error("not enough credit");
	else
	    {
	    record(date, -amount,desc);
	    acc.change(date,getDebt());
	    }
}
void CreditAccount::settle(Date date)
{
    double interest=0;
    if(date.getDay()==1)
        interest=acc.getSum(date)*rate; 
    if(interest!=0&&getBalance()<0)
        record(date,interest,"interest");
    if(date.getMonth()==1&&date.getDay()==1)
        record(date,-fee,"annual fee");
        
    acc.reset(date,getDebt()); 

    }

