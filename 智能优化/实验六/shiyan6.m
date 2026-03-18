clc; clear; close all;

% 1. 数据准备
load fisheriris;          
data = meas;
% 归一化处理
data = (data - min(data)) ./ (max(data) - min(data)); 
[num_data, num_d] = size(data);

% 2. 参数设置
cluster_n = 3;           
iter = 100;               
m = 2;                   
epsilon = 1e-5;           

% 3. 初始化
U = rand(cluster_n, num_data);
U = U ./ sum(U, 1);       % 归一化隶属度
J = zeros(1, iter);

% 4. FCM主循环
for i = 1:iter
    U_old = U; 
    
    % --- 更新聚类中心 ---
    c = zeros(cluster_n, num_d);
    for j = 1:cluster_n
        u_m = U(j,:).^m;
        c(j,:) = (u_m * data) ./ sum(u_m);
    end
    
    % --- 计算目标函数 ---
    current_J = 0;
    for j = 1:cluster_n
        for k = 1:num_data
            dist_sq = norm(data(k,:) - c(j,:))^2;
            current_J = current_J + (U(j,k)^m) * dist_sq;
        end
    end
    J(i) = current_J;
    
    % --- 更新隶属度 ---
    for j = 1:cluster_n
        for k = 1:num_data
            d_jk = norm(data(k,:) - c(j,:));
            d_jk = max(d_jk, 1e-10); % 避免除零
            
            sum_val = 0;
            for l = 1:cluster_n
                d_lk = norm(data(k,:) - c(l,:));
                d_lk = max(d_lk, 1e-10);
                sum_val = sum_val + (d_jk / d_lk)^(2/(m-1));
            end
            U(j,k) = 1 / sum_val;
        end
    end
    
    % --- 判断收敛 ---
    if max(abs(U - U_old), [], 'all') < epsilon
        J(i+1:end) = [];
        break;
    end
end

% 5. 绘图
figure('Position', [100, 100, 1200, 600], 'Name', 'FCM聚类结果');

% --- 左图：隶属度折线图 ---
subplot(1, 2, 1);
plot(1:num_data, U(1,:), 'r.-', 'LineWidth', 0.5, 'MarkerSize', 5); hold on;
plot(1:num_data, U(2,:), 'g.-', 'LineWidth', 0.5, 'MarkerSize', 5);
plot(1:num_data, U(3,:), 'b.-', 'LineWidth', 0.5, 'MarkerSize', 5);
xlabel('样本序号 (Sample Index)');
ylabel('隶属度 (Membership)');
title('各样本对3个类别的隶属度');
legend('Cluster 1', 'Cluster 2', 'Cluster 3');
grid on;

% --- 右图：聚类散点图 ---
[max_val, label] = max(U); % 最大隶属原则确定分类 [cite: 311]
subplot(1,2,2);
gscatter(data(:,1), data(:,2), label); hold on;
plot(c(:,1), c(:,2), 'kX', 'MarkerSize', 12, 'LineWidth', 3);
title(['聚类结果 (J = ' num2str(J(end), '%.4f') ')']); 
xlabel('Feature 1'); ylabel('Feature 2');
grid on;

% 6. 输出隶属度 
fprintf('\n================ 聚类完成 ================\n');
fprintf('迭代次数: %d, 最终目标函数 J: %.4f\n', length(J), J(end));

% 创建表格用于显示
% 转置U，因为U是 (类别x样本)，表格通常是 (样本x类别)
Table_U = array2table(U', 'VariableNames', {'Cluster_1', 'Cluster_2', 'Cluster_3'});
SampleID = (1:num_data)';
Table_U = addvars(Table_U, SampleID, 'Before', 'Cluster_1');
Table_U = addvars(Table_U, label', 'NewVariableNames', 'Final_Class');

fprintf('\n--- 隶属度矩阵示例 (前15个样本) ---\n');
disp(Table_U(1:15, :));

fprintf('\n--- 隶属度矩阵示例 (中间样本 70-80, 模糊区域) ---\n');
disp(Table_U(70:80, :));

fprintf('注：完整隶属度数据保存在变量 Table_U 或 U 中。\n');