#include "D:\\BankAccount\\S4\\S4_Account.h"
#include "D:\\BankAccount\\S4\\S4_accumulator.h"
double Account::total=0;
Account::Account(Date date, string id):id(id),balance(0)
{
    date.show();
    cout<<"\t#"<<id<<" created"<<endl;
}
void Account::record(Date date, double amount, string desc)
{
    balance+=amount;
	total+=amount;
	date.show();
	cout<<"\t"<<id<<"\t"<<amount<<"\t"<<balance<<"\t"<<desc<<endl;
}
void Account::error(string msg)const
{
    cout<<"Error(# "<<id<<"):"<<msg<<endl;
}
void Account::show()const
{
    cout<<"#"<<id<<"\tBalance:"<<balance;
}