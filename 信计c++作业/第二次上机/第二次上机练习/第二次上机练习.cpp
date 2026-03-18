#include<iostream>
#include<cmath>
#include <iomanip>
using namespace std;
float to_area(float a, float b, float c)
{
	float s = (a + b + c) / 2;
	return sqrt(s * (s - a) * (s - b) * (s - c));
}
int main() {
	float a, b, c;
	cout << "please input 3 sides of one triangle:\n";
	cin >> a >> b >> c;

	cout << "a=" << setw(7) << fixed << setprecision(2) << a
		<< ",b=" << setw(7) << fixed << setprecision(2) << b
		<< ",c=" << setw(7) << fixed << setprecision(2) << c << endl;
	cout << "area of triangle is " << setw(10) << fixed << setprecision(5) << to_area(a, b, c) << endl;

}