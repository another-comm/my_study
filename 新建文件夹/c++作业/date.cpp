#include"date.h"
#include <iostream>

using namespace std;
const int DAYS_BEFORE_MONTH[] = { 0,31,59,90,120,151,181,212,243,273,304,334,365 };//平年
Date::Date(int year, int month, int day) :
    year(year), month(month), day(day) {
    int years = year - 1;
    totalDays = years * 365 + years / 4 - years / 100 + years / 400 + DAYS_BEFORE_MONTH[month - 1] + day;//平年
    if (isLeapYear() && month > 2)
        totalDays++;
}

int Date::getYear() const {
    return year;
}

int Date::getMonth() const {
    return month;
}

int Date::getDay() const {
    return day;
}

int Date::getTotalDays() const {
    return totalDays;
}

int Date::getMaxDay() const {
    if (isLeapYear() && month == 2)
        return 29;
    else
        return DAYS_BEFORE_MONTH[month] - DAYS_BEFORE_MONTH[month - 1];
}

bool Date::isLeapYear() const {
    if ((year % 4 == 0 && year % 100 != 0) || year % 400 == 0) {
        return true;
    }
    else {
        return false;
    }
}

void Date::show() const {
    cout << getYear() << "-" << getMonth() << "-" << getDay();
}

int Date::operator-(const Date& date) const {
    return totalDays - date.totalDays;
}

