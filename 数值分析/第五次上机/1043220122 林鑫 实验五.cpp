#include <cstdio>
#include <cmath>

class NewtonSolver {
private:
    double (*f)(double);
    double (*df)(double);

public:
    NewtonSolver(double (*func)(double), double (*dfunc)(double))
        : f(func), df(dfunc) {}

    // Newton 迭代
    void solve(double x0, double epsilon, int maxIter) {
        double x1;
        int i = 1;

        while (i <= maxIter) {
            x1 = x0 - f(x0) / df(x0);

            if (fabs(x1 - x0) / (1 + fabs(x1)) < epsilon) {
                printf("Newton 法迭代步数 = %d，近似值 = %.5f\n", i, x1);
                return;
            }

            x0 = x1;
            i++;
        }

        printf("Newton 法超过最大迭代次数\n");
    }

    // --- 修改后的离散 Newton（割线法） ---
    void solveSecant(double x0, double x1, double epsilon, int maxIter) {
        double x2;
        int iter = 1;   // ?从第 1 次迭代开始数

        while (iter <= maxIter) {
            x2 = x1 - f(x1) * (x1 - x0) / (f(x1) - f(x0));

            if (fabs(x2 - x1) / (1 + fabs(x2)) < epsilon) {
                printf("离散 Newton 法迭代步数 = %d，近似值 = %.5f\n", iter, x2);
                return;
            }

            x0 = x1;
            x1 = x2;
            iter++;   // ?正常累计
        }

        printf("离散 Newton 法超过最大迭代次数\n");
    }
};

// --- 原函数 ---
double f1(double x) { return x*x*x - 3*x - 1; }
double f1_d(double x) { return 3*x*x - 3; }

int main() {
    double epsilon = 0.5e-5;
    int maxIter = 20;

    NewtonSolver solver(f1, f1_d);

    printf("=== Newton 法求解 ===\n");
    solver.solve(2.0, epsilon, maxIter);

    printf("\n=== 离散 Newton 法求解 ===\n");
    solver.solveSecant(2.0, 1.9, epsilon, maxIter);

    return 0;
}

