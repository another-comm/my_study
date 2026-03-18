#include <iostream>
#include <vector>
#include <cmath>
#include <cstdio>
using namespace std;

// ==================== 高斯消元类 ====================
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
// ==================== 多项式最小二乘拟合类 ====================
class PolynomialLeastSquares {
private:
    int m; // 拟合多项式阶数
    int n; // 数据点个数
    vector<double> x, y, w; // 数据与权重
    vector<double> coeffs;  // 拟合系数

    vector<vector<double>> G; // 正则方程组系数矩阵
    vector<double> d;         // 正则方程组右端向量


    void build_system() {
        G.assign(m + 2, vector<double>(m + 2, 0.0));
        d.assign(m + 2, 0.0);

        // === 构造正规方程组 G * a = d ===
        for (int k = 0; k <= m; k++) { 
            for (int j = 0; j <= m; j++) { 
                for (int i = 1; i <= n; i++) { 
                    G[k + 1][j + 1] += w[i] * pow(x[i], k + j);
                }
            }
        }
        for (int j = 0; j <= m; j++) { 
            for (int i = 1; i <= n; i++) { 
                d[j + 1] += w[i] * y[i] * pow(x[i], j);
            }
        }
    }

public:
    PolynomialLeastSquares(const vector<double>& X,
                           const vector<double>& Y,
                           const vector<double>& W,
                           int degree)
        : x(X), y(Y), w(W), m(degree) {
        n = X.size() - 1; 
        build_system();
        coeffs.assign(m + 2, 0.0);
    }

    void fit() {      
        // === 用高斯消元解方程 ===
        GaussianElimination solver(G, d, m + 1);
        solver.solve();
        coeffs = solver.get_solution(); // 将解存入成员变量
    }
    
    void print_polynomial() const {
        cout << "\n拟合的多项式：" << endl;
        for (int i = m + 1; i >= 1; i--) { 
            if (coeffs[i] >= 0 && i < m + 1) cout << "+";
            cout << coeffs[i];
            if (i > 1) { 
                cout << "*x";
                if (i > 2) cout << "^" << (i - 1); 
            }
        }
        cout << endl;
    }


    double compute_MSE() const {
        double error_sum = 0.0; // 这是残差平方和 (SSE)
        for (int i = 1; i <= n; i++) {
            double ls = 0.0; // 预测值 y_pred
            for (int l = 1; l <= m + 1; l++) { 
                ls += coeffs[l] * pow(x[i], l - 1);
            }
            // 计算加权残差平方
            error_sum += w[i] * pow(ls - y[i], 2.0);
        }
        
        // n 是数据点的个数
        if (n == 0) return 0.0; // 避免除以0
        
        // 返回均方误差 (SSE / n)
        return error_sum / n;
    }
    

    void print_normal_equations() const {
        cout << "正则方程组的系数矩阵 G：" << endl;

        for (int k = 0; k <= m; k++) { 
            for (int j = 0; j <= m; j++) { 
                printf("%12.6f ", G[k + 1][j + 1]);
            }
            cout << endl;
        }

        cout << "\n正则方程组的右端向量 d：" << endl;
        for (int k = 0; k <= m; k++) { 
            printf("d[%d] = %12.6f\n", k, d[k + 1]);
        }
    }

    vector<double> get_coefficients() const { return coeffs; }
};

// ==================== 主函数测试 ====================
int main() {
    
    const int m = 2; // 二次多项式
    vector<double> x = {0., 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9};
    vector<double> y = {0., 5.1234, 5.3057, 5.5680, 5.9378, 6.4370, 7.0978, 7.9493, 9.0253, 10.3627};
    vector<double> w = {0., 1., 1., 1., 1., 1., 1., 1., 1., 1.}; 

    // --- 1. 创建对象 ---
    PolynomialLeastSquares pls(x, y, w, m);
    
    cout << "==== 正则方程组 ====" << endl;
    // --- 2. 打印方程组 ---
    pls.print_normal_equations();
    
    // --- 3. 求解方程组 ---
    pls.fit();

    // --- 4. 输出结果 ---
    pls.print_polynomial();
    cout << "\n拟合均方误差 (MSE): " << pls.compute_MSE() << endl;

    return 0;
}
