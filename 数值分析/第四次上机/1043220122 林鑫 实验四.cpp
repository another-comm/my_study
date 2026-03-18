#include <iostream>  
#include <cmath>    
#include <iomanip>   

using namespace std; 


double f1(double x) {
    return 1.0 / (1.0 + sin(x) * sin(x));
}

double f2(double x) {
    return x * log10(x);
}

class NumericalIntegrator {
public:
   
    static double csr(int n, double a, double b, double (*f)(double)) {
        if (n % 2 != 0) {
            cerr << "错误: 复合辛普森公式的 n 必须为偶数。" << endl;
            return 0.0;
        }

        double h = (b - a) / n;
        double sum = f(a) + f(b);
    
        for (int k = 1; k < n; k += 2) {
            sum += 4.0 * f(a + k * h);
        }
        for (int k = 2; k < n; k += 2) {
            sum += 2.0 * f(a + k * h);
        }

        return sum * (h / 3.0);
    }


    static double ctr(int n, double a, double b, double (*f)(double)) {
        double h = (b - a) / n;
        double sum = f(a) + f(b);

        for (int k = 1; k < n; k++) { 
            sum += 2.0 * f(a + k * h);
        }

        return sum * (h / 2.0);
    }
};


int main() {
    double a1 = 0.0, b1 = 1.0;
    int n1 = 10;
    cout << " 问题 1:" << endl;
    
    double trap_result1 = NumericalIntegrator::ctr(n1, a1, b1, f1);
    cout << "复合梯形公式结果: " << trap_result1 << endl;

    double simp_result1 = NumericalIntegrator::csr(n1, a1, b1, f1);
    cout << "复合Simpson公式结果: " << simp_result1 << endl;
    


    double a2 = 1.0, b2 = 2.0;
    int n2 = 8;
    cout << " 问题 2:" << endl;

    double trap_result2 = NumericalIntegrator::ctr(n2, a2, b2, f2);
    cout << "复合梯形公式结果: " << trap_result2 << endl;

    double simp_result2 = NumericalIntegrator::csr(n2, a2, b2, f2);
    cout << "复合Simpson公式结果: " << simp_result2 << endl;

    return 0;
}
