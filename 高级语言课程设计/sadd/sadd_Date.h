#ifndef SADD_DATE_H
#define SADD_DATE_H

#include <iostream>
using namespace std;
class Date {
private:
	int year;
	int month;
	int day;
	int totalDays;
public:
	Date(int year, int month, int day);
	int getYear() const { return year; }
	int getMonth() const { return month; }
	int getDay()  const { return day; }
	int getMaxDay() const;
	int  gettotalDays() const { return totalDays; }
	bool isLeapYear() const;
	void show() const;
	int distance(Date date) const;
};

#endif