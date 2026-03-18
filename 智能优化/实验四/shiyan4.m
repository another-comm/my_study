clear; clc; close all;
% 1. 参数设置
m = 20;                 % 蚂蚁数量
Alpha = 1;              % 信息素重要度
Beta = 2;               % 启发式因子重要度
Rho = 0.5;              % 挥发因子
NC_max = 100;           % 最大迭代次数
CityNum = 20;           % 城市数

% 2. 生成地图与距离
CityPos = rand(CityNum, 2) * 100;       % 随机生成坐标
D = zeros(CityNum, CityNum);            % 距离矩阵
for i = 1:CityNum
    for j = 1:CityNum
        if i ~= j
            D(i,j) = norm(CityPos(i,:) - CityPos(j,:));
        else
            D(i,j) = eps;
        end
    end
end
Eta = 1 ./ D;           % 启发式信息 (1/距离)

%% 3. 初始化
Tau = ones(CityNum, CityNum);           % 信息素矩阵初始化
GlobalBestLength = inf;                 % 全局最优距离
GlobalBestRoute = [];                   % 全局最优路径
Length_Best_Record = zeros(NC_max, 1);  % 记录收敛过程

% 4. 迭代主循环
iter = 1;
while iter <= NC_max
    Route = zeros(m, CityNum);          % 路径记录表
    
    % --- 步骤 2.1: 随机起点 ---
    for i = 1:m
        Route(i, 1) = randi(CityNum); 
    end
    
    % --- 步骤 2.2: 蚂蚁构建路径 ---
    for i = 1:m
        for step = 2:CityNum
            Current = Route(i, step-1);
            Visited = Route(i, 1:step-1);
            
            % 确定待访问城市
            Unvisited = 1:CityNum;
            Unvisited(ismember(Unvisited, Visited)) = []; 
            
            % 计算转移概率 (题目公式1)
            P = zeros(1, length(Unvisited));
            for k = 1:length(Unvisited)
                Next = Unvisited(k);
                P(k) = (Tau(Current, Next)^Alpha) * (Eta(Current, Next)^Beta);
            end
            
            % 轮盘赌选择
            P = P / sum(P);
            Pcum = cumsum(P);
            Select = find(Pcum >= rand, 1);
            Route(i, step) = Unvisited(Select);
        end
    end
    
    % --- 计算路径长度 ---
    Length = zeros(m, 1);
    for i = 1:m
        L = 0;
        for j = 1:CityNum-1
            L = L + D(Route(i,j), Route(i,j+1));
        end
        L = L + D(Route(i,CityNum), Route(i,1)); % 回路
        Length(i) = L;
    end
    
    % --- 更新最优解 ---
    [MinLength, MinIndex] = min(Length);
    if MinLength < GlobalBestLength
        GlobalBestLength = MinLength;
        GlobalBestRoute = Route(MinIndex, :);
    end
    Length_Best_Record(iter) = GlobalBestLength;
    
    % --- 步骤 3: 信息素更新 (题目公式2) ---
    Delta_Tau = zeros(CityNum, CityNum);
    Tau = (1 - Rho) .* Tau;             % 挥发
    
    for i = 1:m
        for j = 1:CityNum-1
            p1 = Route(i, j); p2 = Route(i, j+1);
            Delta_Tau(p1, p2) = Delta_Tau(p1, p2) + 1/Length(i); % 累加
            Delta_Tau(p2, p1) = Delta_Tau(p2, p1) + 1/Length(i);
        end
        p1 = Route(i, CityNum); p2 = Route(i, 1); % 闭合回路
        Delta_Tau(p1, p2) = Delta_Tau(p1, p2) + 1/Length(i);
        Delta_Tau(p2, p1) = Delta_Tau(p2, p1) + 1/Length(i);
    end
    Tau = Tau + Delta_Tau;              % 叠加新信息素
    
    fprintf('第 %d 代: 最优长度 = %.4f\n', iter, GlobalBestLength);
    iter = iter + 1;
end

% 5. 绘图
figure(1);
subplot(1, 2, 1);
plot(CityPos(:,1), CityPos(:,2), 'ro', 'MarkerFaceColor', 'r'); hold on;
BestPlot = [GlobalBestRoute, GlobalBestRoute(1)];
plot(CityPos(BestPlot,1), CityPos(BestPlot,2), 'b-');
title(['最优路径 (L=' num2str(GlobalBestLength) ')']); grid on;

subplot(1, 2, 2);
plot(Length_Best_Record, 'k-', 'LineWidth', 1.5);
title('收敛曲线'); xlabel('迭代'); ylabel('长度'); grid on;