clc; clear;

%% --- 第一题：幂法 ---
A1 = [1, -3, 2; 4, 4, -1; 6, 3, 5];
[lam1, v1] = power_method(A1, 100, 1e-8);

fprintf('题1 (幂法)按模最大特征值: %.6f\n', lam1);
fprintf('对应特征向量: [%.4f, %.4f, %.4f]^T\n', v1);

%% --- 第二题：反幂法 ---
A2 = [2, 3, 4; 4, 4, 5; 0, 3, 6];
[lam2, v2] = inverse_power_method(A2, 100, 1e-8);

fprintf('题2 (反幂法) 按模最小特征值: %.6f\n', lam2);
fprintf('对应特征向量: [%.4f, %.4f, %.4f]^T\n', v2);


