function [LL, LH, HL, HH] = haar_dwt2D(img)

    [m, n] = size(img);
    img_temp = zeros(m, n);
    
    % 1. 对每一行进行一维Haar分解
    for i = 1:m
        [L, H] = haar_dwt(img(i, :)); % 调用 haar_dwt 函数
        img_temp(i, :) = [L, H];
    end

    img_out = zeros(m, n);
    
    % 2. 对变换后的每一列进行一维Haar分解
    for j = 1:n
       [L, H] = haar_dwt(img_temp(:, j)'); % 注意：输入必须是行向量
       img_out(:, j) = [L, H]'; % 转置回来
    end

    m_half = m / 2;
    n_half = n / 2;

    % 3. 分离四个子带
    % 本来分解不应该加mat2gray的，不过为了有好的显示效果就加上了
    LL = mat2gray(img_out(1:m_half, 1:n_half));          % 行列都是低频  
    LH = mat2gray(img_out(1:m_half, n_half+1:n));        % 行低频列高频
    HL = mat2gray(img_out(m_half+1:m, 1:n_half));        % 行高频列低频
    HH = mat2gray(img_out(m_half+1:m, n_half+1:n));      % 行列都是高频
end

