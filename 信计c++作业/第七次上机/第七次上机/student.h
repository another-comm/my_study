#ifndef STUDENT_H
#define STUDENT_H

#include <string>
using namespace std;

class Student {

public:
    void Set(const string& name, const string& studentId, int credits);

    string GetName() const;

    string GetStudentId() const;

    int GetCredits() const;

    void Print() const;
private:
    string name;
    string studentId;
    int credits;

};

#endif 
