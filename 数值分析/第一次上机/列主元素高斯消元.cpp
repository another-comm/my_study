#include <iostream>
#include <vector>
#include <cmath>
using namespace std;

void elimination(vector<vector<double>>& a, vector<vector<double>>& l, vector<double>& b, int n, int k)
{
    for (int i = k + 1; i <= n; i++) {
        l[i][k] = a[i][k] / a[k][k];
        b[i] = b[i] - l[i][k] * b[k];

        for (int j = k + 1; j <= n; j++) {
            a[i][j] = a[i][j] - l[i][k] * a[k][j];
        }
    }
}

void back_sub(vector<vector<double>>& a, vector<double>& b, vector<double>& x, int n)
{
    x[n] = b[n] / a[n][n];
    for (int k = n - 1; k >= 1; k--) {
        double sum = 0.0;
        for (int j = k + 1; j <= n; j++) {
            sum += a[k][j] * x[j];
        }
        x[k] = (b[k] - sum) / a[k][k];
    }
}

void pivot_ele(vector<vector<double>>& a, vector<double>& b, int k, int n)
{
    int p = k;
    for (int i = k + 1; i <= n; i++) {
        if (fabs(a[i][k]) > fabs(a[p][k]))
            p = i;
    }

    if (p != k) {
        for (int j = k; j <= n; j++) {
            double t = a[k][j];
            a[k][j] = a[p][j];
            a[p][j] = t;
        }
        double t = b[k];
        b[k] = b[p];
        b[p] = t;
    }
}

void solve(vector<vector<double>>& a, vector<vector<double>>& l, vector<double>& b, vector<double>& x, int n)
{
    for (int k = 1; k <= n - 1; k++) {
        pivot_ele(a, b, k, n);
        elimination(a, l, b, n, k);
    }
    back_sub(a, b, x, n);

    for (int i = 1; i <= n; i++)
        printf("x[%d] = %16.8e\n", i, x[i]);
}

int main()
{
    vector<vector<double>> a = {
        {0, 0, 0, 0},
        {0, 0.2641, 0.1735, 0.8642},
        {0, 0.9411, -0.0175, 0.1463},
        {0, -0.8641, -0.4243, 0.0711}
    };
    vector<vector<double>> l(4, vector<double>(4, 0.0));
    vector<double> b = {0, -0.7521, 0.6310, 0.2501};
    vector<double> x(4, 0.0);

    solve(a, l, b, x, 3);

    return 0;
}

