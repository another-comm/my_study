#ifndef ACCUMULATOR_H
#define ACCUMULATOR_H

#include "date.h"

class Accumulator {
private:
	Date lastDate;
	double value;
	double sum;
public:
	Accumulator(const Date& date, double value) :lastDate(date), value(value), sum(0) {}
	double getSum(const Date& date)const {
		return sum + value * (date-lastDate);
	}

	void change(const Date& date, double value) {
		sum = getSum(date);
		lastDate = date;
		this->value = value;
	}
	void reset(const Date& date, double value) {
		lastDate = date;
		this->value = value;
		sum = 0;
	}
};
#endif // ACCUMULATOR_H
