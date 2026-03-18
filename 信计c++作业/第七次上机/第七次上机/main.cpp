#include "Student.h"

using namespace std;

int main() {
    Student s1, s2, s3;

    s1.Set("Alice", "1043220101", 100);
    s2.Set("Bob", "1043220102", 50);
    s3.Set("Charlie", "1043220103", 25);

    s1.Print();
    s2.Print();
    s3.Print();

    return 0;
}
