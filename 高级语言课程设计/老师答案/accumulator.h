#ifndef ACCUMULATOR_H
#define ACCUMULATOR_H
#include "D:\\BankAccount\\S4\\S4_date.h"
class Accumulator{
    private:
        Date lastDate;
        double value;//相当于balance
        double sum;//相当于accumulation
    public:
    Accumulator(Date date, double value):lastDate(date),value(value),sum(0){}
    double getSum(Date date)const
    {
        return sum+value*date.distance(lastDate);
    }
    void change(Date date,double value)//
    {
        sum=getSum(date);
        this->value=value;
        lastDate=date;
    }
    void reset(Date date, double value)
    {
        lastDate=date;
        this->value=value;
        sum=0;
    }

};
#endif