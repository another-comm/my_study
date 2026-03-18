%% 基于小波变换的图像融合实验 (高清修正版)
%  功能：读取两幅图像，统一调整为最大分辨率，进行小波融合
%  融合规则：低频采用区域方差加权，高频采用绝对值取大
clc; clear; close all;

% ==========================================================
%  1. 图像读取与智能预处理
% ==========================================================

% 请根据实际文件名修改这里
image_name1 = 'pic1.jpg'; 
image_name2 = 'pic2.jpg';

% 检查文件是否存在
if exist(image_name1, 'file') && exist(image_name2, 'file')
    I1 = imread(image_name1);
    I2 = imread(image_name2);
    disp(['成功读取文件：' image_name1 ' 和 ' image_name2]);
else
    disp('未找到指定图片，正在生成高分辨率测试图片进行演示...');
    % 生成测试图片 (512x512 高清)
    I1 = zeros(512, 512);
    I1(:, 1:256) = rand(512, 256) * 255; % 左侧噪点
    I1 = uint8(I1);
    
    I2 = zeros(512, 512);
    I2(:, 257:end) = rand(512, 256) * 255; % 右侧噪点
    I2 = uint8(I2);
end

% 转换为灰度图
if size(I1, 3) > 1, I1 = rgb2gray(I1); end
if size(I2, 3) > 1, I2 = rgb2gray(I2); end

% --- 核心修改：智能调整尺寸 (解决模糊问题) ---
[r1, c1] = size(I1);
[r2, c2] = size(I2);

% 取两幅图中最大的行数和列数，防止高清图被压缩变糊
max_r = max(r1, r2);
max_c = max(c1, c2);

% 只有当尺寸不符合最大尺寸时才调整
if (r1 ~= max_r) || (c1 ~= max_c)
    fprintf('正在放大图像1至 [%d, %d]...\n', max_r, max_c);
    I1 = imresize(I1, [max_r, max_c]);
end

if (r2 ~= max_r) || (c2 ~= max_c)
    fprintf('正在放大图像2至 [%d, %d]...\n', max_r, max_c);
    I2 = imresize(I2, [max_r, max_c]);
end
disp('图像预处理完成，清晰度已保留。');


% ==========================================================
%  2. 小波分解
% ==========================================================
st = cputime;  % 计时开始

dim = 2; % 分解层数 (对于大图，2或3均可)

disp('正在进行小波分解...');
y1 = mywavedec2(double(I1), dim);
y2 = mywavedec2(double(I2), dim);


% ==========================================================
%  3. 图像融合
% ==========================================================
[r, c] = size(y1);
y3 = zeros(r, c);

% --- 规则1：高频系数融合 (最大绝对值规则) ---
% 这一步处理了整个矩阵，包括低频位置，稍后低频会被覆盖
for i = 1:r
    for j = 1:c
        if abs(y1(i, j)) >= abs(y2(i, j))
            y3(i, j) = y1(i, j);
        else
            y3(i, j) = y2(i, j);
        end
    end
end

% --- 规则2：低频系数融合 (区域方差加权规则) ---
% 计算低频部分的索引范围
low_r = r / (2^dim);
low_c = c / (2^dim);

LLa = y1(1:low_r, 1:low_c);
LLb = y2(1:low_r, 1:low_c);

disp('正在进行低频部分融合(基于区域方差)...');
% 调用专门的低频融合函数
y3(1:low_r, 1:low_c) = lowfrefus(LLa, LLb);


% ==========================================================
%  4. 图像重构
% ==========================================================
disp('正在重构融合图像...');
yr = mywaverec2(y3, dim);

et = cputime - st; % 计算耗时


% ==========================================================
%  5. 评价指标与显示
% ==========================================================
disp('正在计算评价指标...');
% 计算熵
e1 = averEntropy(I1);
e2 = averEntropy(I2);
er = averEntropy(yr);

% 计算梯度
g1 = avegrad(I1);
g2 = avegrad(I2);
gr = avegrad(yr);

% 输出结果到控制台
fprintf('\n----------------------------------------\n');
fprintf(' 程序运行时间: %.4f 秒\n', et);
fprintf('----------------------------------------\n');
fprintf(' 图像        信息熵(Entropy)   平均梯度(Gradient)\n');
fprintf(' 源图像A     %8.4f          %8.4f\n', e1, g1);
fprintf(' 源图像B     %8.4f          %8.4f\n', e2, g2);
fprintf(' 融合图像    %8.4f          %8.4f\n', er, gr);
fprintf('----------------------------------------\n');

% --- 修改：分别弹出三个独立的大窗口显示 ---

% 显示源图像A
figure('Name', '源图像 A', 'NumberTitle', 'off');
imshow(uint8(I1)); 
title('源图像 A (已统一尺寸)');

% 显示源图像B
figure('Name', '源图像 B', 'NumberTitle', 'off');
imshow(uint8(I2)); 
title('源图像 B (已统一尺寸)');

% 显示融合图像
figure('Name', '融合图像', 'NumberTitle', 'off');
imshow(uint8(yr)); 
title('基于小波变换的融合图像');


%% =========================================================
%  以下是局部函数定义 (无需修改，保持原算法逻辑)
%  =========================================================

% --- 低频融合策略：基于区域方差 ---
function y = lowfrefus(A, B)
    [row, col] = size(A);
    y = zeros(row, col);
    alpha = 0.5; % 阈值
    
    for i = 1:row
        for j = 1:col
            [m2p, Ga, Gb] = area_var_match(A, B, [i, j]);
            
            % 计算加权系数
            if alpha == 1
                Wmin = 0;
            else
                Wmin = 0.5 - 0.5 * ((1 - m2p) / (1 - alpha));
            end
            Wmax = 1 - Wmin;
            
            if m2p < alpha
                % 匹配度低，选择方差大的（信息量大的）
                if Ga >= Gb
                    y(i, j) = A(i, j);
                else
                    y(i, j) = B(i, j);
                end
            else
                % 匹配度高，进行加权融合
                if Ga >= Gb
                    y(i, j) = Wmax * A(i, j) + Wmin * B(i, j);
                else
                    y(i, j) = Wmin * A(i, j) + Wmax * B(i, j);
                end
            end
        end
    end
end

% --- 计算区域方差匹配度 ---
function [m2p, Ga, Gb] = area_var_match(A, B, p)
    level = 1; % 邻域半径 (1表示3x3窗口)
    [subA, mpa, npa] = submat(A, p, level);
    [subB, mpb, npb] = submat(B, p, level);
    
    [r, c] = size(subA);
    w = weivec(subA, [mpa, npa]); % 获取高斯权重
    
    averA = sum(sum(subA)) / (r * c);
    averB = sum(sum(subB)) / (r * c);
    
    % 计算区域方差
    Ga = sum(sum(w .* (subA - averA).^2));
    Gb = sum(sum(w .* (subB - averB).^2));
    
    if (Ga == 0) && (Gb == 0)
        m2p = 0;
    else
        m2p = 2 * sum(sum(w .* abs(subA - averA) .* abs(subB - averB))) / (Ga + Gb);
    end
end

% --- 生成高斯权重 ---
function w = weivec(x, p)
    [r, c] = size(x);
    p1 = p(1); p2 = p(2);
    sig = 1;
    w = zeros(r, c);
    for i = 1:r
        for j = 1:c
            gauss_i = exp(-(i - p1)^2 / (2 * sig^2));
            gauss_j = exp(-(j - p2)^2 / (2 * sig^2));
            w(i, j) = 0.5 * (gauss_i + gauss_j);
        end
    end
end

% --- 获取子矩阵 ---
function [smat, mp, np] = submat(x, p, level)
    [row, col] = size(x);
    m = p(1); n = p(2);
    
    up = m - level; down = m + level;
    left = n - level; right = n + level;
    
    % 边界处理 (镜像延拓)
    if left < 1, right = right + 1 - left; left = 1; end
    if right > col, left = left + col - right; right = col; end
    if up < 1, down = down + 1 - up; up = 1; end
    if down > row, up = up + row - down; down = row; end
    
    smat = x(up:down, left:right);
    mp = m - up + 1; np = n - left + 1;
end

% --- 二维小波分解主函数 ---
function y = mywavedec2(x, dim)
    x = modmat(x, dim); 
    [m, n] = size(x);
    xd = double(x);
    
    % 使用全尺寸矩阵存储所有系数
    total_coeff = xd;
    curr_LL = xd;
    
    for i = 1:dim
        [dLL, dHL, dLH, dHH] = mydwt2(curr_LL);
        [r_curr, c_curr] = size(dLL);
        
        % 更新整个系数矩阵
        total_coeff(1:r_curr, 1:c_curr) = dLL;
        total_coeff(1:r_curr, c_curr+1:2*c_curr) = dHL;
        total_coeff(r_curr+1:2*r_curr, 1:c_curr) = dLH;
        total_coeff(r_curr+1:2*r_curr, c_curr+1:2*c_curr) = dHH;
        
        curr_LL = dLL; % 下一层
    end
    y = total_coeff;
end

% --- 二维小波重构主函数 ---
function y = mywaverec2(x, dim)
    xr = double(x);
    [row, col] = size(xr);
    
    for i = dim:-1:1
        curr_r = row / 2^(i-1);
        curr_c = col / 2^(i-1);
        
        half_r = curr_r / 2;
        half_c = curr_c / 2;
        
        rLL = xr(1:half_r, 1:half_c);
        rHL = xr(1:half_r, half_c+1:curr_c);
        rLH = xr(half_r+1:curr_r, 1:half_c);
        rHH = xr(half_r+1:curr_r, half_c+1:curr_c);
        
        tmp = myidwt2(rLL, rHL, rLH, rHH);
        xr(1:curr_r, 1:curr_c) = tmp;
    end
    y = xr;
end

% --- 单层二维分解 ---
function [LL, HL, LH, HH] = mydwt2(x)
    lpd = [1/2, 1/2]; hpd = [-1/2, 1/2];
    [row, col] = size(x);
    
    tmp_row = zeros(row, col);
    for j = 1:row
        [ca1, cd1] = mydwt(x(j, :), lpd, hpd, 1);
        tmp_row(j, :) = [ca1, cd1];
    end
    
    tmp_col = zeros(row, col);
    for k = 1:col
        [ca2, cd2] = mydwt(tmp_row(:, k)', lpd, hpd, 1);
        tmp_col(:, k) = [ca2, cd2]';
    end
    
    LL = tmp_col(1:row/2, 1:col/2);
    LH = tmp_col(row/2+1:row, 1:col/2);
    HL = tmp_col(1:row/2, col/2+1:col);
    HH = tmp_col(row/2+1:row, col/2+1:col);
end

% --- 单层二维重构 ---
function y = myidwt2(LL, HL, LH, HH)
    lpr = [1, 1]; hpr = [1, -1];
    tmp_mat = [LL, HL; LH, HH];
    [row, col] = size(tmp_mat);
    yt = zeros(row, col);
    
    for k = 1:col
        ca1 = tmp_mat(1:row/2, k)';
        cd1 = tmp_mat(row/2+1:row, k)';
        yt(:, k) = myidwt(ca1, cd1, lpr, hpr)';
    end
    
    y_final = zeros(row, col);
    for j = 1:row
        ca2 = yt(j, 1:col/2);
        cd2 = yt(j, col/2+1:col);
        y_final(j, :) = myidwt(ca2, cd2, lpr, hpr);
    end
    y = y_final;
end

% --- 一维分解 ---
function [cA, cD] = mydwt(x, lpd, hpd, dim)
    cA = x; cD = [];
    for i = 1:dim
        cvl = conv(cA, lpd);
        dnl = downspl(cvl);
        cvh = conv(cA, hpd);
        dnh = downspl(cvh);
        cA = dnl;
        cD = [cD, dnh];
    end
end

% --- 一维重构 ---
function y = myidwt(cA, cD, lpr, hpr)
    lca = length(cA);
    upl = upspl(cA);
    cvl = conv(upl, lpr);
    cvl = cvl(1:2*lca); 
    uph = upspl(cD);
    cvh = conv(uph, hpr);
    cvh = cvh(1:2*lca);
    y = cvl + cvh;
end

% --- 辅助函数：尺寸规范化 ---
function y = modmat(x, dim)
    [row, col] = size(x);
    rt = row - mod(row, 2^dim);
    ct = col - mod(col, 2^dim);
    y = x(1:rt, 1:ct);
end

% --- 辅助函数：上采样 ---
function y = upspl(x)
    N = length(x);
    M = 2 * N - 1;
    y = zeros(1, M);
    y(1:2:end) = x;
end

% --- 辅助函数：下采样 ---
function y = downspl(x)
    y = x(2:2:end);
end

% --- 评价指标：信息熵 ---
function AVERENTROPY = averEntropy(img)
    I1 = double(img);
    I1(I1 == 0) = [];
    I1 = I1 ./ numel(I1);
    Entropy = -sum(I1 .* log2(I1));
    AVERENTROPY = sum(Entropy);
end

% --- 评价指标：平均梯度 ---
function AVEGRAD = avegrad(img)
    img = double(img);
    [M, N] = size(img);
    diffX = img - [img(:, 2:N), img(:, N)];
    diffY = img - [img(2:M, :); img(M, :)];
    diffX(:, N) = 0; diffY(M, :) = 0;
    AVEGRAD = sum(sum(sqrt(diffX.^2 + diffY.^2))) / ((M - 1) * (N - 1));
end