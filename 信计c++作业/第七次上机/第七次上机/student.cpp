#include "Student.h"
#include <iostream>

using namespace std;

void Student::Set(const string& name, const string& studentId, int credits) {
    this->name = name;
    this->studentId = studentId;
    this->credits = credits;
}

string Student::GetName() const {
    return name;
}

string Student::GetStudentId() const {
    return studentId;
}

int Student::GetCredits() const {
    return credits;
}

void Student::Print() const {
    cout << "姓名: " << name << ", 学号: " << studentId << ", 学分: " << credits << endl;
}
