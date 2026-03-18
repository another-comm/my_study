#include <iostream>
#include <vector>

using namespace std;

class Interpolation {
private:
    int n;                          // 插值节点数（n+1个点）
    vector<double> x, y;            // 节点与函数值

public:
    // === 构造函数 ===
    Interpolation() : n(0) {}

    // === 设置数据 ===
    void setData(const vector<double>& xData, const vector<double>& yData) {
        if (xData.size() != yData.size()) {
            cerr << "Error: x 和 y 的长度不匹配！" << endl;
            exit(1);
        }
        x = xData;
        y = yData;
        n = x.size() - 1;
    }

    // === 拉格朗日插值法 ===
    double lagrange(double x0) const {
        double Ln = 0.0;
        for (int i = 0; i <= n; i++) {
            double l = 1.0;
            for (int j = 0; j <= n; j++) {
                if (j != i)
                    l *= (x0 - x[j]) / (x[i] - x[j]);
            }
            Ln += y[i] * l;
        }
        return Ln;
    }

    // === 牛顿插值法 ===
   double newton(double x0) const {
    // 差商表
    vector<vector<double>> f(n + 1, vector<double>(n + 1));
    for (int i = 0; i <= n; i++) f[i][0] = y[i];

    for (int j = 1; j <= n; j++) {
        for (int i = j; i <= n; i++) {
            f[i][j] = (f[i][j - 1] - f[i - 1][j - 1]) / (x[i] - x[i - j]);
        }
    }

    // 牛顿插值
    double Nn = f[0][0];
    for (int k = 1; k <= n; k++) {
        double term = f[k][k];
        for (int j = 0; j < k; j++)
            term *= (x0 - x[j]);
        Nn += term;
    }

    return Nn;
}   
};

int main() {
    vector<double> x = {0.5, 0.7, 0.9, 1.1,1.3,1.5,1.7,1.9};
    vector<double> y = {0.48, 0.64, 0.78, 0.89,0.96,1.00,0.99,0.95};

    Interpolation interp;
    interp.setData(x, y);

    vector<double> a= {0.74,1.6,0.55,1.2,1.85};
    for(int i=0;i<a.size();i++)
    {
    cout << "插值点 a = " << a[i] << endl;
    cout << "拉格朗日插值结果: " << interp.lagrange(a[i]) << endl;
    cout << "牛顿插值结果: " << interp.newton(a[i]) << endl;
	}

    return 0;
}

