#include <iostream>
#include <vector>
#include <cmath>
#include <cstdio>
using namespace std;

class GaussianElimination {
private:
    vector<vector<double>> a;  // 系数矩阵
    vector<vector<double>> l;  // L 矩阵
    vector<double> b;          // 常数向量
    vector<double> x;          // 解向量
    int n;                     // 方程规模

    // 列主元素选主元
    void pivot_ele(int k) {
        int p = k;
        for (int i = k + 1; i <= n; i++) {
            if (fabs(a[i][k]) > fabs(a[p][k]))
                p = i;
        }
        if (p != k) {
            for (int j = k; j <= n; j++) {
                swap(a[k][j], a[p][j]);
            }
            swap(b[k], b[p]);
        }
    }

    // 消元过程
    void elimination(int k) {
        for (int i = k + 1; i <= n; i++) {
            l[i][k] = a[i][k] / a[k][k];
            b[i] = b[i] - l[i][k] * b[k];
            for (int j = k + 1; j <= n; j++) {
                a[i][j] = a[i][j] - l[i][k] * a[k][j];
            }
        }
    }

    // 回代
    void back_sub() {
        x[n] = b[n] / a[n][n];
        for (int k = n - 1; k >= 1; k--) {
            double sum = 0.0;
            for (int j = k + 1; j <= n; j++) {
                sum += a[k][j] * x[j];
            }
            x[k] = (b[k] - sum) / a[k][k];
        }
    }

public:
    // 构造函数
    GaussianElimination(const vector<vector<double>>& A,
                        const vector<double>& B, int N)
        : a(A), b(B), n(N) {
        l = vector<vector<double>>(n + 1, vector<double>(n + 1, 0.0));
        x = vector<double>(n + 1, 0.0);
    }

    // 执行求解
    void solve() {
        for (int k = 1; k <= n - 1; k++) {
            pivot_ele(k);
            elimination(k);
        }
        back_sub();
    }

    // 打印解向量
    void print_solution() const {
        for (int i = 1; i <= n; i++) {
            printf("x[%d] = %16.8e\n", i, x[i]);
        }
    }

    // 获取解向量
    vector<double> get_solution() const {
        return x;
    }
};

int main() {
    vector<vector<double>> a = {
        {0, 0, 0, 0},
        {0, 0.2641, 0.1735, 0.8642},
        {0, 0.9411, -0.0175, 0.1463},
        {0, -0.8641, -0.4243, 0.0711}
    };

    vector<double> b = {0, -0.7521, 0.6310, 0.2501};

    GaussianElimination solver(a, b, 3);
    solver.solve();
    solver.print_solution();

    return 0;
}

