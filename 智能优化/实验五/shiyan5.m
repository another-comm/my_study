clc; clear; close all;

% 1. 参数初始化
w = 1;              
c1 = 2;             
c2 = 2;            
r1_fixed = 0.5;     
r2_fixed = 0.2;    

dim = 2;            
particlesize = 3;  
maxgen = 50;       

x_min = -5;         % 位置下限 
x_max = 5;          % 位置上限 
v_max = 0.2 * (x_max - x_min); % 速度限制

% 2. 种群初始化
x = x_min + (x_max - x_min) * rand(particlesize, dim); 
v = -v_max + 2 * v_max * rand(particlesize, dim);

personalbest_x = x;        
personalbest_faval = zeros(particlesize, 1); 

for i = 1:particlesize
    personalbest_faval(i) = fitness_func(x(i,:));
end

[globalbest_faval, best_index] = min(personalbest_faval); % 寻找全局最优
globalbest_x = personalbest_x(best_index, :); % 全局最优位置

% 用于记录收敛过程
trace = zeros(maxgen, 1); 

% 3. 迭代寻优
for t = 1:maxgen
    
    for i = 1:particlesize
        % --- 速度更新 ---
        % 公式: v = w*v + c1*rand*(pBest-x) + c2*rand*(gBest-x)
        v(i,:) = w * v(i,:) ...
               + c1 * r1_fixed * (personalbest_x(i,:) - x(i,:)) ...
               + c2 * r2_fixed * (globalbest_x - x(i,:));
        
        % 速度越界处理
        for j = 1:dim
            if v(i,j) > v_max
                v(i,j) = v_max;
            elseif v(i,j) < -v_max
                v(i,j) = -v_max;
            end
        end
        
        % --- 位置更新 ---
        % 公式: x = x + v
        x(i,:) = x(i,:) + v(i,:);
        
        % 位置越界处理
        for j = 1:dim
            if x(i,j) > x_max
                x(i,j) = x_max;
            elseif x(i,j) < x_min
                x(i,j) = x_min;
            end
        end
        
        % --- 适应度计算与最优值更新 ---
        f_current = fitness_func(x(i,:));
        
        % 更新个体最优 pBest 
        if f_current < personalbest_faval(i)
            personalbest_faval(i) = f_current;
            personalbest_x(i,:) = x(i,:);
        end
        
        % 更新全局最优 gBest 
        if f_current < globalbest_faval
            globalbest_faval = f_current;
            globalbest_x = x(i,:);
        end
    end
    
    trace(t) = globalbest_faval; % 记录每一代的全局最优值
end

% 4. 结果输出
disp('------------------------------------------------');
disp(['最优解 (x1, x2): ', num2str(globalbest_x)]);
disp(['最小值 (y): ', num2str(globalbest_faval)]);
disp('------------------------------------------------');

% 绘制收敛曲线
figure;
plot(trace, 'LineWidth', 2);
title(['粒子群算法收敛曲线 (y = x1^2 + 2x2 + 3)']);
xlabel('迭代次数');
ylabel('适应度值 (Fitness)');
grid on;

% 5. 目标函数定义 
function y = fitness_func(pos)

    x1 = pos(1);
    x2 = pos(2);
    y = x1^2 + 2*x2 + 3;
end