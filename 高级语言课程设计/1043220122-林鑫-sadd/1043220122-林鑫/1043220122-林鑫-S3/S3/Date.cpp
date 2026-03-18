#include "Date.h"

int maxday[12] = { 31,28,31,30,31,30,31,31,30,31,30,31 };



Date::Date(int year, int month, int day) :
	year(year), month(month), day(day){
	totalDays = 0;
	totalDays += 365 * (year - 1) + (year - 1) / 4 - (year - 1) / 100 + (year - 1) / 400+day;
	for(int i=month-1;i>=1;i--)
		totalDays += maxday[i - 1];
	if (month > 2&&isLeapYear() ) totalDays +=1;

}
bool Date::isLeapYear() const{
	int year = getYear();
	if ((year % 4 == 0 && year % 100 != 0) || year % 400 == 0)
		return true;
	else return false;

}
int Date::getMaxDay() const {
	if (!isLeapYear())
	return maxday[getMonth()-1];
	else
	{
		return getMonth() == 2 ? 29 : maxday[getMonth()-1];
	}
}

int Date::distance(Date date) const{
	/*
	cout << "两个日期相差的天数为: " << gettotalDays() - date.gettotalDays
	*/
	return totalDays-date.totalDays;
}

void Date::show()const{
	cout << year << '-' << month << '-' << day ;
}