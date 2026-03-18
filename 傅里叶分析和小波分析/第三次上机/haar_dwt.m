function [L, H] = haar_dwt(f)
   n = length(f);    
    % 确保 n 是偶数
    if mod(n, 2) ~= 0
        error('输入向量 f 的长度必须是偶数。');
    end
    
    n_half = n / 2;
    L = zeros(1, n_half);   % 低频分量 (均值)
    H = zeros(1, n_half);   % 高频分量 (差值)
    
    sqrt2 = sqrt(2); % 预计算 sqrt(2)

    for i = 1:n_half
        L(i) = (f(2*i - 1) + f(2*i)) / sqrt2;
        H(i) = (f(2*i - 1) - f(2*i)) / sqrt2;
    end
end

