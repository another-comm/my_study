
clear;
clc;
close all;

%% 1. 初始化参数
M = 30;     % 城市数量 
N = 100;    % 种群规模
MAX_GEN = 50000; % 最大迭代次数
Pc = 0.9;   % 交叉概率
Pm = 0.05;  % 变异概率 

fprintf('正在初始化...\n');

%% 2. 随机生成30个城市坐标 
cities = rand(M, 2) * 100; % 坐标范围 [0, 100]

%% 3. 定义距离矩阵 
D = zeros(M, M);
for i = 1:M
    for j = i+1:M
        % 计算欧氏距离
        dist = sqrt(sum((cities(i,:) - cities(j,:)).^2));
        D(i,j) = dist;
        D(j,i) = dist;
    end
end

%% 4. 产生初始群体 
pop = zeros(N, M);
for i = 1:N
    pop(i,:) = randperm(M);
end

%% 5. 存储全局最优解
global_best_path = zeros(1, M); % 存储最优路线 
global_min_length = inf;        % 存储最优长度
generation_best_len = zeros(MAX_GEN, 1); % 存储每代的最优长度

fprintf('开始遗传算法迭代...\n');

%% 6. 遗传算法主循环 
p = 1;
while(p <= MAX_GEN)
    
    % a. 计算当前种群所有个体的路径长度 
    path_lengths = zeros(N, 1);
    for i = 1:N
        current_path = pop(i,:);
        len_i = 0;
        for j = 1:M-1
            len_i = len_i + D(current_path(j), current_path(j+1));
        end
        % 加上从最后一个城市回到起点的距离
        len_i = len_i + D(current_path(M), current_path(1));
        path_lengths(i) = len_i;
    end

    % b. 最好的路径保留 
    [current_min_len, idx] = min(path_lengths);
    
    % 更新全局最优解 
    if current_min_len < global_min_length
        global_min_length = current_min_len;
        global_best_path = pop(idx,:);
    end
    generation_best_len(p) = global_min_length;

    % c. 适应度评价 
    fitness = 1 ./ path_lengths;
    prob = fitness / sum(fitness);
    
    % d. 累积概率, 为轮盘赌做准备
    cum_prob = cumsum(prob);
    
    % e. 选择操作 
    new_pop = zeros(N, M);
    % 精英主义: 第1个个体直接复制全局最优解 
    new_pop(1,:) = global_best_path; 
    
    for i = 2:N % 轮盘赌选择 N-1 个个体
        r = rand;
        sel_idx = find(cum_prob > r, 1);
        if isempty(sel_idx)
            sel_idx = N; % 应对可能的浮点数精度问题
        end
        new_pop(i,:) = pop(sel_idx,:);
    end

    % f. 交叉操作 
    % (使用更标准的顺序交叉 (OX1), 保证路径的有效性)
    parents_idx = randperm(N); % 随机配对
    for i = 1:2:N-1
        if rand < Pc
            p1 = new_pop(parents_idx(i), :);
            p2 = new_pop(parents_idx(i+1), :);
            
            % 随机选择交叉点
            cut_points = sort(randi(M, [1, 2]));
            c1 = cut_points(1);
            c2 = cut_points(2);
            
            % 子代1 (p1中段 + p2剩余)
            child1_middle = p1(c1:c2);
            child1_others = p2(~ismember(p2, child1_middle));
            child1 = [child1_others(1:c1-1), child1_middle, child1_others(c1:end)];
            
            % 子代2 (p2中段 + p1剩余)
            child2_middle = p2(c1:c2);
            child2_others = p1(~ismember(p1, child2_middle));
            child2 = [child2_others(1:c1-1), child2_middle, child2_others(c1:end)];
            
            % 替换
            new_pop(parents_idx(i), :) = child1;
            new_pop(parents_idx(i+1), :) = child2;
        end
    end

    % g. 变异操作
    for i = 2:N % (i=1 是精英, 不变异)
         if(rand < Pm)
             % 随机选两个位置
             u_idx = sort(randi(M, [1, 2]));
             u1 = u_idx(1);
             u2 = u_idx(2);
             % 交换 
             temp = new_pop(i, u1);
             new_pop(i, u1) = new_pop(i, u2);
             new_pop(i, u2) = temp;
         end
    end
    
    % h. 更新种群并进入下一代
    pop = new_pop;
    
    % (可选) 打印进度
    if mod(p, 50) == 0
        fprintf('Generation %d / %d: Best Length = %.2f\n', p, MAX_GEN, global_min_length);
    end
    
    p = p + 1;
end

fprintf('迭代完成。\n');

%% 7. 绘制最终结果
fprintf('绘制最终路径和收敛曲线...\n');

% 绘制收敛曲线 (仿照 figure(3) plot(fmin))
figure;
plot(1:MAX_GEN, generation_best_len, 'LineWidth', 2);
title('遗传算法收敛曲线 (30城市)');
xlabel('迭代次数 (p)');
ylabel('最短路径长度 (fmin)');
grid on;

% 绘制最终路径图 (仿照 figure(2) ... plot(A2(:,1),A2(:,2),'-'))
figure;
% 将路径闭合 (最后一个点连接回第一个点)
final_path_indices = [global_best_path, global_best_path(1)];
final_path_coords = cities(final_path_indices, :);

plot(final_path_coords(:,1), final_path_coords(:,2), 'o-', 'LineWidth', 2, 'MarkerSize', 8, 'Color', [0.1, 0.4, 0.8]);
hold on;
% 标记起点
plot(cities(global_best_path(1), 1), cities(global_best_path(1), 2), ...
    'r*', 'MarkerSize', 15, 'LineWidth', 2); 
title(['遗传算法TSP最优路径 (30城市)']);
xlabel('X 坐标');
ylabel('Y 坐标');
legend('最优路径', '起点');
grid on;
box on;

fprintf('找到的最短路径长度为: %.4f\n', global_min_length);