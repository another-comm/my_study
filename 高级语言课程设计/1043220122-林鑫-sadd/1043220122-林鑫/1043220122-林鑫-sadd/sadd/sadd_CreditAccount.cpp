#include "sadd_CreditAccount.h"
#include <iostream>

double CreditAccount::total = 0;

CreditAccount::CreditAccount(Date date, string id, double credit, double rate, double fee)
    : lastDate(date), id(id), credit(credit), rate(rate), fee(fee), balance(0), accumulation(0)
{
    date.show();
    cout << "\t#" << id << " is created." << endl;
}

void CreditAccount::error(string msg) {
    cout << msg << endl;
}

double CreditAccount::accumulate(Date date) const {
    if (balance < 0)
        return accumulation + balance * date.distance(lastDate);
    else
        return accumulation;
}

void CreditAccount::record(Date date, double amount, string desc) {
    accumulation = accumulate(date);
    balance += amount;
    lastDate = date;
    total += amount;
    date.show();
    cout << "\t" << id << "\t" << amount << "\t" << balance << "\t" << desc << endl;
}

void CreditAccount::deposit(Date date, double amount, string desc) {
    record(date, amount, desc);
}

void CreditAccount::withdraw(Date date, double amount, string desc) {
    if (amount > getAvailableCredit()) {
        error("Error: not enough credit");
    }
    else {
        record(date, -amount, desc);
    }
}

void CreditAccount::settle(Date date) {
        double interest = 0;
        if (balance < 0) {
            interest = accumulate(date) * rate ;
            if (interest != 0)
                record(date, interest, "interest");
        }
        if (date.getYear() > lastDate.getYear()) {
            record(date, -fee, "annual fee");
        }
    
}
void CreditAccount::show() const {
    cout << "#" << id << " Balance:" << balance << " Available credit:" << getAvailableCredit() << endl;
}

double CreditAccount::getAvailableCredit() const {
 
    if (balance < 0)
        return credit + balance;
    else
        return credit;
}