
#include <iostream>
using namespace std;
double algorithm_do_while(int n,double x)
{
    double sum = 0,xx=1;
    int i = 0;
    do
    {
        if (i % 2||!i) sum += xx;
        else sum -= xx;
        i++;
        xx = xx * x / i;
    } while (i <= n);
    return sum;
}

double algorithm_while(int n, double x)
{
    double sum = 0, xx = 1;
    int i = 0;
    while (i <= n)
    {
        if (i % 2 || !i) sum += xx;
        else sum -= xx;
        i++;
        xx = xx * x / i;
    }
    return sum;
}

double algorithm_for(int n, double x)
{
    double sum = 0, xx = 1;
    for (int i = 0; i <= n; i++)
    {
        if (i % 2 || !i) sum += xx;
        else sum -= xx;
        xx = xx * x / (i + 1);
    }
    return sum;
}

int main()
{
    int n;
    double x;
    cout << "please enter n and x: " << endl;
    cin >> n >> x;
    cout << algorithm_do_while(n, x) << endl;
    cout << algorithm_while(n, x) << endl;
    cout << algorithm_for(n, x) << endl;

}


