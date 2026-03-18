clc; clear; close all;
A = [5, -2, -5, -1;
     1,  0, -3,  2;
     0,  2,  2, -3;
     0,  0,  1, -2];
% 上 Hessenberg 分解
[Hess, H] = hessenberg(A);
fprintf('输出：上 Hessenberg 阵 :\n');
disp(Hess);
fprintf('输出：正交变换阵 H:\n');
disp(H);

% QR 迭代 (收敛到 Real Schur Form)
T = Hess;      
U = H;      
max_iter = 100;
tol = 1e-8;

for k = 1:max_iter
    %由于有复特征值，我们直接跑满100次
    [Q_k, R_k] = zqr(T);  
    T = R_k * Q_k;    
    U = U * Q_k;    
end
fprintf('收敛后的矩阵 T (Real Schur Form):\n');
disp(T);

% 提取特征值并计算所有特征向量
n = size(A, 1);
i = n; 
while i >= 1

    is_2x2 = false;
    if i > 1 && abs(T(i, i-1)) > 1e-5
        is_2x2 = true;
    end
    
    if ~is_2x2
        lambda = T(i, i);
        y = zeros(n, 1);
        y(i) = 1;     
        if i > 1
            Top = T(1:i-1, 1:i-1) - lambda * eye(i-1);
            rhs = -T(1:i-1, i);
            y(1:i-1) = Top \ rhs; 
        end
        v = U * y;
        v = v / norm(v);   
        fprintf('\n-> 实特征值 %.4f 的特征向量:\n', lambda);
        disp(v');     
        i = i - 1; 
    else
        % ===  复数特征值 (2x2 块) ===
        blk_start = i-1;
        blk_end = i;
        B = T(blk_start:blk_end, blk_start:blk_end);      
        tr = B(1,1) + B(2,2);
        dt = B(1,1)*B(2,2) - B(1,2)*B(2,1);
        delta = tr^2 - 4*dt;      
        mu(1) = (tr + sqrt(delta)) / 2;
        mu(2) = (tr - sqrt(delta)) / 2;
        for k = 1:2
            lambda = mu(k);          
            % 1. 先解 2x2 块内部的特征向量 v_loc
            M = B - lambda * eye(2);
            if norm(M(1,:)) > norm(M(2,:))
                v_loc = [-M(1,2); M(1,1)];
            else
                v_loc = [-M(2,2); M(2,1)];
            end     
            % 2. 构造整体向量 y
            y = zeros(n, 1);
            y(blk_start:blk_end) = v_loc;   
            % 3. 向上回代求解剩余部分
            if blk_start > 1
                % (T_top - lambda*I) * y_top = - T_top_right * v_loc
                Top = T(1:blk_start-1, 1:blk_start-1) - lambda * eye(blk_start-1);
                rhs = -T(1:blk_start-1, blk_start:blk_end) * v_loc;
                y(1:blk_start-1) = Top \ rhs;
            end  
            % 4. 转换回 A 坐标系
            v = U * y;
            v = v / norm(v);    
            fprintf('\n-> 复特征值 %.4f%+.4fi 的特征向量:\n', real(lambda), imag(lambda));
            disp(v.'); 
        end
        i = i - 2; % 向上移动 2 格
    end
end