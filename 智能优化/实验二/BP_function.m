function [W1_new, B1_new, W2_new, B2_new, intermediate] = ...
    BP_function(X, T, W1, B1, W2, B2, l)
    
    % 1. 定义 Sigmoid 激活函数
    sigmoid = @(u) 1 ./ (1 + exp(-u));

    % --- 2. 前向传播 ---
    % 计算隐藏层输入 (U_h) 和输出 (O_h)
    U_h = W1 * X + B1;
    O_h = sigmoid(U_h);
    
    % 计算输出层输入 (U_o) 和输出 (O_o)
    U_o = W2 * O_h + B2;
    O_o = sigmoid(U_o);

    % --- 3. 反向传播 ---
    % 计算输出层误差 (E_o)
    E_o = O_o .* (1 - O_o) .* (T - O_o);
    
    % 计算隐藏层误差 (E_h)，将输出层误差 E_o 反向传播
    E_h = (O_h .* (1 - O_h)) .* (W2' * E_o);

    % --- 4. 更新权值和阈值 ---
    % 更新阈值(偏置)
    B1_new = B1 + l * E_h;
    B2_new = B2 + l * E_o;
    
    % 更新权值 (l * 误差 * 输入')
    W2_new = W2 + l * (E_o * O_h'); 
    W1_new = W1 + l * (E_h * X'); 

    % --- 5. 保存中间值用于验证 ---
    intermediate.O_h = O_h;
    intermediate.O_o = O_o;
    intermediate.E_h = E_h;
    intermediate.E_o = E_o;
end