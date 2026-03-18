%% 1
clear; clc;
A = [0.78 -0.02 -0.12 -0.14; 
    -0.02  0.86 -0.04  0.06; 
    -0.12 -0.04  0.72 -0.08; 
    -0.14  0.06 -0.08  0.74];
b = [0.76; 0.08; 1.12; 0.68];
x0 = [0; 0; 0; 0];
tol = 1e-6;
% --- 最速下降法 ---
[x_sd, k_sd,r_sd] = steepest_descent(A, b, x0, tol);
disp(x_sd');disp(k_sd);
disp(norm(r_sd));

% --- 共轭梯度法 ---
[x_cg, k_cg,P,r_cg] = conjugate_gradient(A, b, x0, tol);
disp(x_cg');disp(k_cg);
disp(norm(r_cg));

%% 2
clear; clc;
A = [2  1 -1;
     1  4  0;
    -1  0  2];
b = [1; -1; -2];
x0 = [0; 0; 0]; 
tol = 1e-6;     
% 因为 f(x) = 0.5*x'Ax + b'x，极值点满足 Ax + b = 0 => Ax = -b
[x, k, P_history,r] = conjugate_gradient(A, -b, x0, tol);
disp(x');
disp(k);
fprintf('生成的三个 A-共轭向量 (p0, p1, p2) 如下：\n');
for i = 1:3
    fprintf('p%d = [%f, %f, %f]^T\n', i-1, P_history(:,i));
end

disp(norm(r));

%% 3
clear;clc;
A=[10,1,2,3,4;
    1,9,-1,2,-3;
    2,-1,7,3,-5;
    3,2,3,12,-1;
    4,-3,-5,-1,15];
b=[12;-27;14;-17;12];
x0=[0;0;0;0;0];
tol=1e-6;
% --- 最速下降法 ---
[x_sd, k_sd,r_sd] = steepest_descent(A, b, x0, tol);
disp(x_sd');disp(k_sd);
disp(norm(r_sd));

% --- 共轭梯度法 ---
[x_cg, k_cg,P,r_cg] = conjugate_gradient(A, b, x0, tol);
disp(x_cg');disp(k_cg);
disp(norm(r_cg));

