// multiplication.cpp
#include <iostream>
#include <iomanip>
#include "multiplication.h"

using namespace std;

void multiplication_table(int n)
{
    for (int i = 1; i <= n; i++) // i ÐÐ j ÁÐ
    {
        for (int j = 1; j <= i; j++)
        {
            cout << j << "X" << i << "=" << left << setw(2) << j * i << " ";
        }
        cout << endl;
    }
}
