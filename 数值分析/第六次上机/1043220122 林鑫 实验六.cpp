#include <iostream>
#include <vector>
#include <cmath>
#include <fstream> 
#include <functional>
#include <iomanip>

using namespace std;

class RK4Solver {
private:
    double a, b;
    double y0;
    int N;
    double h;
    vector<double> x_result;
    vector<double> y_result;

public:
    RK4Solver(double start, double end, double initVal, int steps) 
        : a(start), b(end), y0(initVal), N(steps) {
        h = (b - a) / N;
    }

    // RK4 求解
    void solve(function<double(double, double)> f) {
        x_result.clear();
        y_result.clear();

        double x = a;
        double y = y0;
        
        x_result.push_back(x);
        y_result.push_back(y);

        for (int k = 0; k < N; ++k) {
            double k1 = f(x, y);
            double k2 = f(x + h / 2.0, y + h / 2.0 * k1);
            double k3 = f(x + h / 2.0, y + h / 2.0 * k2);
            double k4 = f(x + h, y + h * k3);

            y = y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4);
            x = a + (k + 1) * h;

            x_result.push_back(x);
            y_result.push_back(y);
        }
    }

    // 将结果写入文件（带列名）
    void saveToFile(const string& filename) {
        ofstream outfile(filename);
        if (!outfile.is_open()) {
            cerr << "无法打开文件: " << filename << endl;
            return;
        }

        // 写入表头
        outfile << "x\t\ty" << endl;

        outfile << fixed << setprecision(6);
        
        // 写入数据
        for (size_t i = 0; i < x_result.size(); ++i) {
            outfile << x_result[i] << "\t" << y_result[i] << endl;
        }

        outfile.close();
        cout << "结果已保存至 " << filename << endl;
    }
};

// 题目方程: y' = y - x^2 + 1
double targetEquation(double x, double y) {
    return y - pow(x, 2) + 1.0;
}

int main() {
    // 参数: [0, 2], y(0)=0.5, N=10
    RK4Solver solver(0.0, 2.0, 0.5, 10);
    
    solver.solve(targetEquation);
    solver.saveToFile("out.txt");

    return 0;
}
