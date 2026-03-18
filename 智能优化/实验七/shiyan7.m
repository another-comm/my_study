close all;clc;clear;

%% 参数初始化】
D = 5;              % 免疫个体维度 
NP = 100;           % 免疫个体数目
Xs = 10;            % 取值上限
Xx = -10;           % 取值下限
G = 500;            % 最大免疫代数
pm = 0.7;           % 变异概率
alfa = 1;           % 激励度系数
belta = 1;          % 激励度系数
detas = 0.2;        % 相似度阈值
gen = 0;            % 免疫代数
Nc1 = 10;           % 克隆个数
deta0 = 1 * Xs;     % 邻域范围初值

%% 初始种群
f = rand(D, NP) * (Xs - Xx) + Xx;

% 预分配空间用于计算
MSLL = zeros(1, NP);
ND = zeros(1, NP);

while gen < G
    %% 计算个体浓度和激励度
    % 1. 计算亲和度（目标函数值）
    for np = 1:NP
        MSLL(np) = func2(f(:, np));
    end
    
    % 2. 计算抗体浓度
    for np = 1:NP
        nd = zeros(1, NP);
        for j = 1:NP
            % 欧氏距离计算
            dist = sqrt(sum((f(:, np) - f(:, j)).^2));
            if dist < detas
                nd(j) = 1;
            else
                nd(j) = 0;
            end
        end
        ND(np) = sum(nd) / NP; % 抗体浓度
    end
    
    % 3. 计算抗体激励度
    MSLL = alfa * MSLL + belta * ND;
    
    %% 选择与克隆操作
    % 排序激励度
    [SortMSLL, Index] = sort(MSLL);
    Sortf = f(:, Index);
    
    % 存储当前最优
    gen = gen + 1;
    trace(gen) = func2(Sortf(:, 1));
    
    % 选择激励度排名前 NP/2 的个体进行克隆
    af = []; % 存储变异后的子代
    aMSLL = [];
    
    % 原始种群保存用于后面合并（bf & bMSLL）
    bf = Sortf(:, 1:NP/2);
    bMSLL = SortMSLL(1:NP/2);
    
    for i = 1:NP/2
        a = Sortf(:, i);
        Na = repmat(a, 1, Nc1); % 复制 Nc1 个抗体
        deta = deta0 / gen;     % 随代数收缩变异范围
        
        for j = 1:Nc1
            for ii = 1:D
                % 高频变异
                if rand < pm
                    Na(ii, j) = Na(ii, j) + (rand - 0.5) * deta;
                end
                
                % 边界条件处理
                if (Na(ii, j) > Xs) || (Na(ii, j) < Xx)
                    Na(ii, j) = rand * (Xs - Xx) + Xx;
                end
            end
        end
        % 保留克隆源个体（截图逻辑）
        Na(:, 1) = Sortf(:, i);
        
        % 收集克隆变异后的种群
        af = [af, Na];
    end
    
    %% 种群刷新
    % 计算子代亲和度用于后续合并排序
    for k = 1:size(af, 2)
        % 这里计算子代的新激励度（简化处理）
        temp_MSLL(k) = func2(af(:, k)); 
    end
    
    % 免疫种群与记忆种群合并（截图逻辑：f1=[af, bf]）
    f1 = [af, bf];
    new_MSLL = [temp_MSLL, bMSLL];
    
    % 重新排序并选出下一代 NP 个个体
    [SortMSLL_final, Index_final] = sort(new_MSLL);
    Sortf_final = f1(:, Index_final);
    
    % 更新种群为下一代循环做准备
    f = Sortf_final(:, 1:NP);
    
end

%% 输出结果
Bestf = Sortf(:, 1);
fprintf('最优变量值为：\n');
disp(Bestf);
fprintf('最小函数值为：%.4f\n', trace(end));

% 绘制收敛曲线
figure;
plot(trace, 'LineWidth', 1.5);
xlabel('进化代数');
ylabel('目标函数值');
title('免疫算法收敛曲线');
grid on;
%% 
function y = func2(x)
    % 目标函数：sum(xi^2) - 2，维度为 5
    y = sum(x.^2) - 2;
end
