

%% 第三题：求矩阵 A 的特征值
clear; clc;

% 定义矩阵 A
A_orig = [5 -2 -5 -1; 
          1  0 -3  2; 
          0  2  2 -3; 
          0  0  1 -2];

%% 方法一：直接 QR 法
fprintf('--- 方法一：直接 QR 法 ---\n');
A = A_orig;
for k = 1:30
    A_old = A;
    [Q1, R1] = zqr(A); % 使用自定义的 QR 分解函数
    A = R1 * Q1;       % QR 迭代核心：A_{k+1} = R_k * Q_k
    err = norm(A - A_old, inf);
end
eig_direct = diag(A); % 迭代收敛后，对角线即为特征值
disp('迭代 30 次后的对角线元素（特征值）：');
disp(eig_direct);

%% 方法二：先化为上 Hessenberg 阵，再用 QR 法
fprintf('--- 方法二：上 Hessenberg + QR 法 ---\n');
% 1. 化为上 Hessenberg 阵 H，并得到正交变换阵 Q_hess
[H, Q_hess] = Hess(A_orig); 

% 2. 对 H 进行 QR 迭代
H_iter = H;
Q_total = Q_hess; % 用于累计特征向量的正交变换
for k = 1:14
    [P1, R1] = zqr(H_iter);
    H_iter = R1 * P1;
    Q_total = Q_total * P1; % 更新特征向量矩阵
end

disp('上 Hessenberg 矩阵 H：');
disp(H);
disp('正交变换阵 Q：');
disp(Q_hess);
disp('迭代 14 次后的特征值：');
disp(diag(H_iter));