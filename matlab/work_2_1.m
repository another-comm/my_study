clc; clear; close all;

%% 参数定义
board_L = 3000; board_W = 1500;
product_types = containers.Map({1,3}, {[406 229], [406 229]});
num_products = 60;

% 遗传算法参数
pop_size = 40; max_gen = 1000;
crossover_rate = 0.6; mutation_rate = 0.1;

% 初始化种群
pop_GP1 = zeros(pop_size, num_products);
pop_GP2 = zeros(pop_size, num_products);

for i = 1:pop_size
    order = randperm(num_products);
    signs = ones(1,num_products);
    signs(rand(1,num_products) > 0.5) = -1;
    pop_GP1(i,:) = order .* signs;
    pop_GP2(i,:) = randsample([1,3], num_products, true);
end

%% 主函数调用
best_fit = 0; best_GP1 = []; best_GP2 = []; best_gen = 0;
solution_pool = struct('fit', {}, 'GP1', {}, 'GP2', {});

for gen = 1:max_gen
    fitness = zeros(pop_size,1);
    for i=1:pop_size
        fitness(i) = fitness_func(pop_GP1(i,:), pop_GP2(i,:), board_L, board_W, product_types, gen);
    end

    [cur_best, idx_best] = max(fitness);

    % 检查是否为新方案
    found = false;
    for k = 1:length(solution_pool)
        if abs(solution_pool(k).fit - cur_best) < 1e-6
            found = true; break;
        end
    end
    if ~found
        solution_pool(end+1).fit = cur_best;
        solution_pool(end).GP1 = pop_GP1(idx_best,:);
        solution_pool(end).GP2 = pop_GP2(idx_best,:);
    end

    % 更新全局最优
    if cur_best > best_fit
        best_fit = cur_best;
        best_GP1 = pop_GP1(idx_best,:);
        best_GP2 = pop_GP2(idx_best,:);
        best_gen = gen;
    end

    fprintf('第 %d 代，当前最优利用率: %.4f\n', gen, best_fit);

    % 选择
    fit_adj = fitness - min(fitness) + 1e-6;
    prob = fit_adj / sum(fit_adj);
    cum_prob = cumsum(prob);
    new_GP1 = zeros(size(pop_GP1));
    new_GP2 = zeros(size(pop_GP2));

    for i = 1:pop_size
        r = rand;
        sel = find(cum_prob >= r,1);
        new_GP1(i,:) = pop_GP1(sel,:);
        new_GP2(i,:) = pop_GP2(sel,:);
    end

    % 交叉
    for i = 1:2:pop_size-1
        if rand < crossover_rate
            [c1_GP1, c1_GP2] = crossover(new_GP1(i,:), new_GP2(i,:), new_GP1(i+1,:), new_GP2(i+1,:));
            [c2_GP1, c2_GP2] = crossover(new_GP1(i+1,:), new_GP2(i+1,:), new_GP1(i,:), new_GP2(i,:));
            new_GP1(i,:) = c1_GP1; new_GP2(i,:) = c1_GP2;
            new_GP1(i+1,:) = c2_GP1; new_GP2(i+1,:) = c2_GP2;
        end
    end

    % 变异
    for i = 1:pop_size
        if rand < mutation_rate
            [new_GP1(i,:), new_GP2(i,:)] = mutation(new_GP1(i,:), new_GP2(i,:));
        end
    end

    pop_GP1 = new_GP1;
    pop_GP2 = new_GP2;
end

fprintf('\n最终最佳利用率: %.4f（第 %d 代）\n', best_fit, best_gen);

%% 输出前10种不同高利用率方案
[~, sort_idx] = sort([solution_pool.fit], 'descend');
top_k = min(10, length(sort_idx));
fprintf('\n前 %d 种不同高利用率方案如下：\n', top_k);

for i = 1:top_k
    idx = sort_idx(i);
    fprintf('第 %d 名：利用率 %.4f\n', i, solution_pool(idx).fit);
    visualize_layout(solution_pool(idx).GP1, solution_pool(idx).GP2, board_L, board_W, product_types, -i); % -i表示Top i
end

%% 可视化函数
function visualize_layout(GP1, GP2, board_L, board_W, product_types, gen)
    figure('Name', sprintf('布局 - %d', gen), 'NumberTitle', 'off'); 
    hold on; axis equal;
    xlim([0 board_L]); ylim([0 board_W]);
    if gen < 0
        title(sprintf('Top %d 排布方案 (利用率排名)', -gen));
    else
        title(sprintf('最佳布局 (第 %d 代)', gen));
    end
    xlabel('Length'); ylabel('Width');

    R = [0,0,board_L,board_W]; cut_dir = 0;

    for i = 1:length(GP1)
        if ~isKey(product_types, GP2(i)), continue; end
        size_p = product_types(GP2(i));
        if GP1(i)<0, size_p = fliplr(size_p); end
        Lp = size_p(1); Wp = size_p(2);

        if mod(gen,2)==1
            [~, idx_sort] = sortrows(R(:,1:2), [1 2]);
        else
            [~, idx_sort] = sortrows(R(:,1:2), [-1 -2]);
        end
        R = R(idx_sort,:);

        idx_fit = -1;
        for j = 1:size(R,1)
            if R(j,3)>=Lp && R(j,4)>=Wp
                idx_fit = j; break;
            end
        end
        if idx_fit==-1, continue; end

        x = R(idx_fit,1); y = R(idx_fit,2);
        rectangle('Position', [x,y,Lp,Wp], 'FaceColor',[.8 .9 1], 'EdgeColor','k');

        old = R(idx_fit,:); R(idx_fit,:) = [];
        if cut_dir==0
            if old(4)>Wp
                R = [R; old(1), old(2)+Wp, old(3), old(4)-Wp];
            end
            if old(3)>Lp
                R = [R; old(1)+Lp, old(2), old(3)-Lp, Wp];
            end
        else
            if old(3)>Lp
                R = [R; old(1)+Lp, old(2), old(3)-Lp, old(4)];
            end
            if old(4)>Wp
                R = [R; old(1), old(2)+Wp, Lp, old(4)-Wp];
            end
        end
        cut_dir = 1 - cut_dir;
    end
    hold off;
end

%% 适应度函数
function fit = fitness_func(GP1, GP2, board_L, board_W, product_types, gen)
    n = length(GP1);
    rects = zeros(n,4); placed = false(1,n);
    R = [0,0,board_L,board_W];
    cut_dir = 0;

    areas = zeros(1,n);
    for i = 1:n
        if ~isKey(product_types, GP2(i))
            warning('非法产品编号 %d，跳过', GP2(i));
            continue;
        end
        size_p = product_types(GP2(i));
        if GP1(i) < 0, size_p = fliplr(size_p); end
        areas(i) = size_p(1) * size_p(2);
    end
    [~, idx_order] = sort(areas, 'descend');
    GP1 = GP1(idx_order); GP2 = GP2(idx_order);

    for i = 1:n
        if ~isKey(product_types, GP2(i)), continue; end
        size_p = product_types(GP2(i));
        if GP1(i) < 0, size_p = fliplr(size_p); end
        Lp = size_p(1); Wp = size_p(2);

        if mod(gen,2)==1
            [~, idx_sort] = sortrows(R(:,1:2), [1 2]);
        else
            [~, idx_sort] = sortrows(R(:,1:2), [-1 -2]);
        end
        R = R(idx_sort,:);

        idx_fit = -1;
        for j = 1:size(R,1)
            if R(j,3) >= Lp && R(j,4) >= Wp
                idx_fit = j; break;
            end
        end
        if idx_fit == -1, continue; end

        x_c = R(idx_fit,1) + Lp/2;
        y_c = R(idx_fit,2) + Wp/2;
        rects(i,:) = [x_c, y_c, Lp, Wp];
        placed(i) = true;

        old = R(idx_fit,:); R(idx_fit,:) = [];
        if cut_dir==0
            if old(4) > Wp
                R = [R; old(1), old(2)+Wp, old(3), old(4)-Wp];
            end
            if old(3) > Lp
                R = [R; old(1)+Lp, old(2), old(3)-Lp, Wp];
            end
        else
            if old(3) > Lp
                R = [R; old(1)+Lp, old(2), old(3)-Lp, old(4)];
            end
            if old(4) > Wp
                R = [R; old(1), old(2)+Wp, Lp, old(4)-Wp];
            end
        end
        cut_dir = 1 - cut_dir;
    end

    fit = sum(rects(placed,3).*rects(placed,4)) / (board_L * board_W);
end

%% 交叉函数
function [c1, c2] = crossover(p1, t1, p2, t2)
    n = length(p1); pt = randi([1 n-1]);
    c1 = [p1(1:pt), p2(pt+1:end)];
    c2 = [t1(1:pt), t2(pt+1:end)];
end

%% 变异函数
function [mut_GP1, mut_GP2] = mutation(GP1, GP2)
    n = length(GP1); mut_GP1 = GP1; mut_GP2 = GP2;
    idx = randi(n); mut_GP1(idx) = -mut_GP1(idx);
    idx2 = randi(n);
    valid_types = [1 3];
    cur_type = GP2(idx2);
    new_types = setdiff(valid_types, cur_type);
    if ~isempty(new_types)
        mut_GP2(idx2) = new_types(randi(length(new_types)));
    end
end
