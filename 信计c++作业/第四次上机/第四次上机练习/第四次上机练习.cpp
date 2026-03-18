#include <iostream>
#include <iomanip>
using namespace std;
void multiplication_table(int n)
{
	for (int i = 1; i <= n; i++)//i行 j列
	{
		for (int j = 1; j <= i; j++)

		{
			cout << j << "X" << i << "=" << left << setw(2) << j * i << " ";
		}
		cout << endl;
	}
}
int main()
{
	multiplication_table(9);
}


