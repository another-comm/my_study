clear;
clc;
format long; 

l = 1;      % 学习率
x_vec = [1; 0]; % 输入向量 
T_vec = [1];     % 期望输出 

% 初始权值 
w.w11 = 0;
w.w12 = 2;
w.w21 = 2;
w.w22 = 1;
w.w13 = 1;
w.w23 = 1;

% 初始阈值 
th.th1 = 0;
th.th2 = 0;
th.th3 = 0;
% --- 转换为矩阵 ---
W1 = [w.w11, w.w21; 
      w.w12, w.w22];
B1 = [th.th1; 
      th.th2];
W2 = [w.w13, w.w23];
B2 = [th.th3];

% 2. 调用BP更新函数 
[W1_new, B1_new, W2_new, B2_new, intermediate] = ...
    BP_function(x_vec, T_vec, W1, B1, W2, B2, l);

fprintf('\n--- 神经元误差计算结果 ---\n');
fprintf('神经元 ① 的误差 (E1): %f\n', intermediate.E_h(1));
fprintf('神经元 ② 的误差 (E2): %f\n', intermediate.E_h(2));
fprintf('神经元 ③ 的误差 (E3): %f\n', intermediate.E_o(1));

fprintf('\n--- 结果分解  ---\n');
fprintf('w11_new: %f\n', W1_new(1,1));
fprintf('w12_new: %f\n', W1_new(2,1));
fprintf('w21_new: %f\n', W1_new(1,2));
fprintf('w22_new: %f\n', W1_new(2,2));
fprintf('w13_new: %f\n', W2_new(1,1));
fprintf('w23_new: %f\n', W2_new(1,2));
fprintf('theta1_new: %f\n', B1_new(1));
fprintf('theta2_new: %f\n', B1_new(2));
fprintf('theta3_new: %f\n', B2_new(1));