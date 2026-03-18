#include "D:\\BankAccount\\Date\\Date.h"
const int NoLeapYear_month[]={31,28,31,30,31,30,31,31,30,31,30,31};

Date::Date(int year, int month, int day):year(year),month(month),day(day)
{
    int i,DAYS_BEFORE_MONTH=0;
    for(i=0;i<month-1;i++)
    {
        DAYS_BEFORE_MONTH+=NoLeapYear_month[i];
    }
    totalDays=365*(year-1)+(year-1)/4-(year-1)/100+(year-1)/400+ DAYS_BEFORE_MONTH+day;
    if (isLeapYear()&&month>2)
    totalDays++;

}
bool Date::isLeapYear()const
{
    return year%4==0&&year%100!=0||year%400==0;
}
int Date::getMaxDay()const
{
    if(isLeapYear()&&month==2)
    return 29;
    else
    return
    NoLeapYear_month[month-1];
}
int Date::distance(Date &date)const{
    cout<<"两个日期相差的天数为："<<totalDays-date.totalDays<<endl;
    return totalDays-date.totalDays;
    
}
void Date::show()const
{
    cout<<getYear()<<"-"<<getMonth()<<"-"<<getDay()<<endl;
}