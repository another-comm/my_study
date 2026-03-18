#include <iostream>
#include <cstdlib>  
#include <ctime>
#include <iomanip>
using namespace std;

void trans_mtx(int** a,int** b,int m,int n)
{
	
	for (int i = 0; i < n; i++)
	{
		for (int j = 0; j < m; j++)
		{
			b[i][j] = a[j][i];
		}
	}
}
void create_mtx(int** a, int m, int n)
{
	for (int i = 0; i < m; i++)
	{
		for (int j = 0; j < n; j++)
			a[i][j] = rand() % 65536;
	}
}
void output_mtx(int** b, int m, int n)
{
	for (int i = 0; i < m; i++)
	{
		for (int j = 0; j < n; j++)
		{
			cout << left << setw(5) << b[i][j] << " ";

		}
		cout << endl;
	}
	cout << endl;
}
int main()
{
	int m, n;
	cout << "please input m and n: " << endl;
	cin >> m >> n;

	int** mtx = new int* [m];  // 分配指向行的指针数组
	for (int i = 0; i < m; ++i) {
		mtx[i] = new int[n];  // 每一行分配 n 个整数的空间
	}

	int** mtx2 = new int* [n];
	for (int i = 0; i < n; ++i) {
		mtx2[i] = new int[m];
	}
	srand(static_cast<unsigned int>(time(0)));
	create_mtx(mtx, m, n);
	output_mtx(mtx, m, n);
	trans_mtx(mtx,mtx2, m, n);
	output_mtx(mtx2, n, m);
}

