%% 1
syms x
f=1/(x^2+1);
disp(int(f,x));
disp(diff(f,x));

%% 2
A=rand(4,4);
B=[1,0,0,1;-1,1,0,1;-1,-1,1,1;-1,-1,-1,1];
fprintf('A + B:\n');
disp(A+B);
fprintf('A - B:\n');
disp(A-B);
fprintf('A * B:\n');
disp(A*B);
fprintf('A * B^(-1):\n');
disp(A*inv(B));
fprintf("B 的 1-范数 : \n");
disp(norm(B,1));
fprintf("B 的 无穷-范数 : \n");
disp(norm(B,inf));
fprintf("B 的 2-范数 : \n");
disp(norm(B,2));

%% 3
clear;
x=linspace(1,50,1000);
x_i=x(2:end);
x_j=x(1:end-1);
part_1=100*(x_i-x_j.^2).^2;
part_2=(1-x_j).^2;
f=1+sum(part_1+part_2);
disp(f);

%% 4
clear;
n=100;
A = diag(8 * ones(n, 1), 0) ...
  + diag(2 * ones(n-1, 1), 1) ...
  + diag(1 * ones(n-1, 1), -1);
b=ones(n,1);
[L,U]=lu_dp(A);
y=fwd_sub(L,b);
x=back_sub(U,y);
fprintf("方程的解为: \n")
disp(x);