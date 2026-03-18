%% problem1
n=20;
A = zeros(n);
for i = 1:n
    for j = 1:n
        A(i,j) = 1 / (i + j - 1);
    end
end

b = zeros(n,1);
for i = 1:n
    b(i) = sum( 1 ./ (i + (1:n) - 1) );
end
c = zeros(n,1);
%% 
tic
[L,U,P] = gauss1(A);
y = fwd_sub(L, P*b);
x = back_sub(U, y);
toc
disp(x);
disp(norm((x-c),2));
disp(norm((A*x-b),2));
%% 
tic
[L,U,P] = gauss2(A);
y = fwd_sub(L, P*b);
x = back_sub(U, y);
toc
disp(x);
disp(norm((x-c),2));
disp(norm((A*x-b),2));
%% problem 2
clc;clear;
A=[9,3,-6;3,26,-7;-6,-7,28];
b=[3;49;32];
L=Cholesky(A);
y=fwd_sub(L,b);
x=back_sub(L',y);
disp(x);disp(L);
disp(norm((L*L'-A),2));
disp(norm((A*x-b),2));

%% 3
clear;clc;
t=[-1;-0.75;-0.5;0;0.25;0.5;0.75];
y=[1.02;0.83;0.74;1.01;1.30;1.76;2.33];
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
err1=norm((y-A*x1),2);
err2=norm((y-A*x2),2);
disp(err1);disp(err2);

ti = linspace(min(t), max(t), 100)';
Ai = [ones(100,1), ti, ti.^2];
plot(t, y, 'ro', ti, Ai*x1, 'b-', ti, Ai*x2, 'g--');
legend('Data', 'Cholesky', 'QR');
grid on;

%% 4
clc;clear;
A=[10,1,2,3,4;
    1,9,-1,2,-3;
    2,-1,12,3,-5;
    3,2,3,12,-1;
    4,-3,-5,-1,15];
b=[12;-27;14;-17;12];
x0 = [0; 0; 0; 0; 0];
tol = 1e-6;
% --- 最速下降法 ---
tic
[x_sd, k_sd, r_sd] = steepest_descent(A, b, x0, tol);
toc
disp(x_sd'); disp(k_sd);disp(r_sd(end)); 
% --- 共轭梯度法 ---
tic
[x_cg, k_cg, P, r_cg] = conjugate_gradient(A, b, x0, tol);
toc
disp(x_cg'); disp(k_cg);disp(r_cg(end));
figure;
plot(0:k_sd, log10(r_sd), 'b-o', 'LineWidth', 1);
hold on;
plot(0:k_cg, log10(r_cg), 'r-s', 'LineWidth', 1);
xlabel('迭代次数');
ylabel('log_{10}(||r_k||_2)');
legend('最速下降', '共轭梯度');
grid on;
%% 5
clc; clear;
n = 100;
A = randn(n, n);
for i = 1:n
    A(i, i) = 100 + rand;
end
c = ones(n, 1);
b = A * c;
x0 = zeros(n, 1);
tol = 1e-6;
max_it = 1000;

tic;
[x1, k1, r1] = my_jacobi(A, b, x0, tol, max_it);
toc
disp(k1); disp(norm(x1 - c, 2)); disp(r1(end));

tic;
[x2, k2, r2] = my_sor(A, b, x0, 1, tol, max_it);
toc
disp(k2); disp(norm(x2 - c, 2)); disp(r2(end));

tic;
[x3, k3, r3] = my_sor(A, b, x0, 1.2, tol, max_it);
toc
disp(k3); disp(norm(x3 - c, 2)); disp(r3(end));

%% 6
clc;clear;
A=[3,1,1;1,4,2;1,2,5];
[lam, v,k] = power_method(A, 100, 1e-6);
disp(lam);disp(v);disp(k);
A1=A;
for k = 1:30
    A_old = A;
    [Q1, R1] = zqr(A);
    A = R1 * Q1;      
    err = norm(A - A_old, inf);
end
eig_direct = diag(A); 
disp(eig_direct);
disp(abs(lam-eig_direct(1)));
disp(norm((A1*v-lam*v),2));