#include <iostream>
using namespace std;
int addi(int a, int b)
{
    return a + b;
}
double addd(double a, double b)
{
    return a + b;
}
int main()
{
    cout << "please enter two numbers(int):" << endl;
    int x, y;
    cin >> x >> y;
    cout << x << '+' << y << "=" << addi(x, y) << endl;
    cout << "please enter two numbers(double):" << endl;
    double c, d;
    cin >> c >> d;
    cout << c << '+' << d << '=' << addd(c, d) << endl;
  
}


