#ifndef S5_ACCUMULATOR_H
#define S5_ACCUMULATOR_H
#include "S5_Date.h"
#include<string>

class Accumulator {
private:
	Date lastDate;
	double value;//相当于balance
	double sum;//相当于accumulation
public:
	Accumulator(const Date& date, double value) :lastDate(date), value(value), sum(0) {}

	double getSum(const Date& date)const
	{
		return sum + value * (date-lastDate);
	}


	void change(const Date& date, double value)
	{
		sum = getSum(date);
		this->value = value;
		lastDate = date;
	}
	void reset(const Date& date, double value)
	{
		lastDate = date;
		this->value = value;
		sum = 0;
	}

};



#endif