#include <iostream>
#include <string>
using namespace std;


struct Block {
    int day;          
    char from;         
    char to;          
    int amount;        
    int balance[4];    
    string thing;      
    Block* pre_add;    


    Block(int day, char m, char n, int amt, int a, int b, int c, int d, string str, Block* pre)
        : day(day), from(m), to(n), amount(amt), thing(str), pre_add(pre) {
        balance[0] = a;
        balance[1] = b;
        balance[2] = c;
        balance[3] = d;
    }
};


Block* change_rec(int day, char m, char n, int amount, string str, Block* ptr) {

    int new_balance[4] = { ptr ? ptr->balance[0] : 100,
                           ptr ? ptr->balance[1] : 100,
                           ptr ? ptr->balance[2] : 100,
                           ptr ? ptr->balance[3] : 100 };

    new_balance[m - 'A'] -= amount;
    new_balance[n - 'A'] += amount;


    return new Block(day, m, n, amount,
        new_balance[0], new_balance[1],
        new_balance[2], new_balance[3], str, ptr);
}


void print_blockchain(Block* ptr) {
    while (ptr != nullptr) {
        cout << "第" << ptr->day << "天，" << ptr->from << " 向 "
            << ptr->to << " 支付了 " << ptr->amount << " 元用于 "
            << ptr->thing << endl;

        cout << "目前余额: ";
        for (int i = 0; i < 4; i++) {
            cout << char('A' + i) << ":" << ptr->balance[i] << "元; ";
        }
        cout << endl << "------------------------------------" << endl;

        ptr = ptr->pre_add;  
    }
}

int main() {

    Block* blockchain = nullptr;

 
    blockchain = change_rec(2, 'A', 'B', 20, "购买一些牛肉", blockchain);
    blockchain = change_rec(2, 'B', 'C', 5, "购买一瓶矿泉水", blockchain);
    blockchain = change_rec(3, 'C', 'A', 10, "理发", blockchain);
    blockchain = change_rec(3, 'A', 'B', 2, "购买一些芹菜", blockchain);
    blockchain = change_rec(4, 'B', 'C', 8, "购买一瓶啤酒", blockchain);
    blockchain = change_rec(4, 'D', 'A', 10, "理发", blockchain);

 
    print_blockchain(blockchain);

  
    
    return 0;
}
