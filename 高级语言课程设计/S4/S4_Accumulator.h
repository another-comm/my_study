#ifndef S4_ACCUMULATOR_H
#define S4_ACCUMULATOR_H
#include "S4_Date.h"
#include<string>

class Accumulator {
private:
	Date lastDate;
	double value;//相当于balance
	double sum;//相当于accumulation
public:
	Accumulator(Date date, double value) :lastDate(date), value(value), sum(0) {}

	double getSum(Date date)const
	{
		return sum + value * date.distance(lastDate);
	}


	void change(Date date, double value)
	{
		sum = getSum(date);
		this->value = value;
		lastDate = date;
	}
	void reset(Date date, double value)
	{
		lastDate = date;
		this->value = value;
		sum = 0;
	}

};



#endif