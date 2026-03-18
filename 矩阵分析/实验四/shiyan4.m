%% 2
clear;clc;
x=[19;25;31;38];
y=[19.0;32.3;49.0;73.3];
%法方程组法
A=[ones(length(x),1),x.^2];
L=Cholesky(A'*A);
y1=fwd_sub(L,A'*y);
x1=back_sub(L',y1);
disp(x1);
%QR分解
[m,n]=size(A);
[Q,R]=zqr(A);
R1 = R(1:n, 1:n);
y2 = Q' * y;
y2 = y2(1:n);
x2=back_sub(R1,y2);
disp(x2);
%验证
J1=norm(y-A*x1);
J2=norm(y-A*x2);
disp(J1);
disp(J2);
%% 3
clear;clc;
t=[-1;-0.75;-0.5;0;0.25;0.5;0.75];
y=[1.00;0.8125;0.75;1.00;1.3125;1.75;2.3125];
%法方程组法
A=[ones(length(t),1),t,t.^2];
L=Cholesky(A'*A);
y1=fwd_sub(L,A'*y);
x1=back_sub(L',y1);
disp(x1);
%QR分解
[m,n]=size(A);
[Q,R]=zqr(A);
R1 = R(1:n, 1:n);
y2 = Q' * y;
y2 = y2(1:n);
x2=back_sub(R1,y2);
disp(x2);
%验证
J1=norm(y-A*x1);
J2=norm(y-A*x2);
disp(J1);
disp(J2);