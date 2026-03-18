#ifndef DATE_H
#define DATE_H

class Date {
private:
    int year;
    int month;
    int day;
    int totalDays;

public:
    Date() = default;
    Date(int year, int month, int day);
    int getYear() const;
    int getMonth() const;
    int getDay() const;
    int getTotalDays() const;
    int getMaxDay() const;
    bool isLeapYear() const;
    void show() const;
    int operator- (const Date & date) const;

};

#endif // DATE_H
