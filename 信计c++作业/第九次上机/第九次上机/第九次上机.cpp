#include<iostream>
using namespace std;

class CAT
{
public:
	CAT();
	CAT(CAT& s);//TODO 拷贝构造函数声明
	~CAT();
	int GetAge() const { return *itsAge; }
	void SetAge(int age) { *itsAge = age; }
protected:
	int* itsAge;
};

CAT::CAT()
{
	itsAge = new int;
	*itsAge = 5;
}
CAT::CAT(CAT& s)
{
	itsAge = new int;
	*itsAge = *s.itsAge;
}

//TODO 拷贝构造函数实现

CAT::~CAT()
{
	delete itsAge;
	itsAge = 0;
}

int main()
{
	CAT frisky;
	cout << "frisky's age:" << frisky.GetAge() << endl;
	cout << "Setting frisky to 6...\n";
	frisky.SetAge(6);
	cout << "Creating boots from frisky\n";
	CAT boots(frisky); //拷贝构造函数使用
	cout << "frisky's age:" << frisky.GetAge() << endl;
	cout << "boots'age:" << boots.GetAge() << endl;

	cout << "setting frisky to 7...\n";
	frisky.SetAge(7);
	cout << "frisky's age:" << frisky.GetAge() << endl;
	cout << "boots'age:" << boots.GetAge() << endl;
}//---