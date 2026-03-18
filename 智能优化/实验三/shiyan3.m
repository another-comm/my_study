clear ;
clc;

% 定义输入数据和参数
X = [1; 2; 4; 5; 6];      
Y = [1; 1; -1; -1; 1];    
C = 100;                  
n = length(Y);           

% 计算核矩阵 ，构建二次规划所需的 H 矩阵
K = zeros(n, n);
for i = 1:n
    for j = 1:n
        K(i,j) = (X(i) * X(j) + 1)^2;
    end
end

H = (Y * Y') .* K; 

% 定义二次规划的参数
% 目标函数: min 0.5*alpha'*H*alpha + f'*alpha
f = -ones(n, 1);          % 对应公式中的 -sum(alpha) 

% 约束条件 1: Aeq * alpha = beq (即 sum(alpha_i * y_i) = 0) 
Aeq = Y';
beq = 0;

% 约束条件 2: lb <= alpha <= ub (0 <= alpha_i <= C) 
lb = zeros(n, 1);
ub = C * ones(n, 1);

% 调用 quadprog 求解 alpha
options = optimoptions('quadprog', 'Display', 'off');
alpha = quadprog(H, f, [], [], Aeq, beq, lb, ub, [], options);

% 计算偏置 b
% 选择一个支持向量 (0 < alpha < C) 来计算 b
epsilon = 1e-5;
sv_indices = find(alpha > epsilon & alpha < (C - epsilon));

if isempty(sv_indices)
    % 如果没有严格在间隔边界上的点，取所有支持向量
    sv_indices = find(alpha > epsilon);
end

% 利用第一个符合条件的支持向量计算 b [cite: 28]
% b = y_k - sum(alpha_i * y_i * K(x_i, x_k))
k = sv_indices(1); 
sum_wx = 0;
for i = 1:n
    sum_wx = sum_wx + alpha(i) * Y(i) * K(i, k);
end
b = Y(k) - sum_wx;

% 输出结果
disp('求解得到的 alpha:');
disp(alpha);
disp(['求解得到的 b: ', num2str(b)]);

X_test = [3; 8];
disp('--- 测试结果 ---');

for j = 1:length(X_test)
    x_target = X_test(j);
    
    % 计算决策函数值 f(x) = sum(alpha_i * y_i * K(x_i, x)) + b 
    decision_value = 0;
    for i = 1:n
        % 核函数 K(x_i, x_target)
        k_val = (X(i) * x_target + 1)^2; 
        decision_value = decision_value + alpha(i) * Y(i) * k_val;
    end
    decision_value = decision_value + b;
    
    % 判定类别
    if decision_value >= 0
        predicted_class = 1;
    else
        predicted_class = 2; 
    end
    
    fprintf('测试样本 X=%d, 决策函数值=%f, 预测类别=Class %d\n', ...
        x_target, decision_value, predicted_class);
end

%% --- 2. 可视化与测试部分  ---

% 创建画布
figure('Name', 'SVM非线性分类可视化', 'Color', 'w', 'Position', [100, 100, 800, 600]);
hold on; box on; grid on;

% (1) 绘制决策函数曲线 f(x)
% 定义绘图的精细网格 (覆盖训练数据和测试数据的范围)
x_plot = 0:0.05:9; 
f_plot = zeros(size(x_plot));

for j = 1:length(x_plot)
    x_val = x_plot(j);
    % 计算 f(x) = sum(alpha_i * y_i * K(x_i, x)) + b
    wx = 0;
    for i = 1:n
         k_val = (X(i) * x_val + 1)^2; 
         wx = wx + alpha(i) * Y(i) * k_val;
    end
    f_plot(j) = wx + b;
end

% 绘制曲线
plot(x_plot, f_plot, 'k-', 'LineWidth', 2, 'DisplayName', '决策函数 f(x)');

% (2) 绘制辅助线
yline(0, 'k--', 'LineWidth', 1.5, 'DisplayName', '决策边界 (f(x)=0)');
% 绘制间隔边界 (f(x) = 1 和 f(x) = -1)
plot(x_plot(abs(f_plot - 1) < 0.5), ones(size(x_plot(abs(f_plot - 1) < 0.5))), 'b:', 'LineWidth', 1, 'HandleVisibility', 'off');
plot(x_plot(abs(f_plot + 1) < 0.5), -ones(size(x_plot(abs(f_plot + 1) < 0.5))), 'r:', 'LineWidth', 1, 'HandleVisibility', 'off');

% (3) 绘制训练样本点
% 为了直观，我们将样本点画在纵坐标 y = 0 的位置（特征轴上）
% Class 1 (Label = 1)
idx1 = find(Y == 1);
plot(X(idx1), zeros(size(idx1)), 'bo', 'MarkerFaceColor', 'b', 'MarkerSize', 8, 'DisplayName', '训练样本 (Class 1)');

% Class 2 (Label = -1)
idx2 = find(Y == -1);
plot(X(idx2), zeros(size(idx2)), 'rs', 'MarkerFaceColor', 'r', 'MarkerSize', 8, 'DisplayName', '训练样本 (Class 2)');

% (4) 圈出支持向量
plot(X(sv_indices), zeros(size(sv_indices)), 'ko', 'MarkerSize', 14, 'LineWidth', 1.5, 'DisplayName', '支持向量');

% (5) 绘制测试数据并输出结果
X_test = [3; 8];
test_f_vals = zeros(size(X_test));
disp('--- 测试结果 ---');

for j = 1:length(X_test)
    x_target = X_test(j);
    
    % 计算测试点的 f(x)
    decision_value = 0;
    for i = 1:n
        k_val = (X(i) * x_target + 1)^2; 
        decision_value = decision_value + alpha(i) * Y(i) * k_val;
    end
    decision_value = decision_value + b;
    test_f_vals(j) = decision_value;
    
    % 判定类别
    if decision_value >= 0
        predicted_class = 1;
    else
        predicted_class = 2; 
    end
    
    fprintf('测试样本 X=%d, 决策函数值=%f, 预测类别=Class %d\n', ...
        x_target, decision_value, predicted_class);
end

% 将测试数据标记在函数曲线上
plot(X_test, test_f_vals, 'mh', 'MarkerSize', 12, 'MarkerFaceColor', 'm', 'DisplayName', '测试数据 (预测值)');

% (6) 图表设置
xlabel('特征值 X');
ylabel('决策函数值 f(x)');
title(['SVM 多项式核(d=2) 分类结果 (C=' num2str(C) ')']);
legend('Location', 'best');
ylim([-5, 12]); % 设置纵坐标范围以便观察整体趋势

hold off;