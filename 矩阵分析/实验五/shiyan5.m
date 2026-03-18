    %% 实验内容 1
    clear; clc; format long;
    
    A = [0.78 -0.02 -0.12 -0.14;
        -0.02  0.86 -0.04  0.06;
        -0.12 -0.04  0.72 -0.08;
        -0.14  0.06 -0.08  0.74];
    
    x0 = zeros(4, 1);
    tol = 1e-6;
    max_iter = 10000;
    b1 = [0.76; 0.08; 1.12; 0.68];

    [x_jac, k_jac] = my_jacobi_matrix(A, b1, x0, tol, max_iter);
    fprintf('迭代次数: %d\n', k_jac);
    disp('解向量:'); disp(x_jac');
    fprintf('残差范数: %.10e\n', norm(A*x_jac - b1));

    disp('------------------------------------');
    disp('2. Gauss-Seidel 迭代法 (相当于 SOR 且 omega=1)');
    [x_gs, k_gs] = my_sor_matrix(A, b1, x0, 1.0, tol, max_iter);
    fprintf('迭代次数: %d\n', k_gs);
    disp('解向量:'); disp(x_gs');
    fprintf('残差范数: %.10e\n', norm(A*x_gs - b1));

    disp('------------------------------------');
    disp('3. SOR 迭代法 (omega = 1.03)');
    omega1 = 1.03;
    [x_sor1, k_sor1] = my_sor_matrix(A, b1, x0, omega1, tol, max_iter);
    fprintf('迭代次数: %d\n', k_sor1);
    disp('解向量:'); disp(x_sor1');
    fprintf('残差范数: %.10e\n', norm(A*x_sor1 - b1));

    %% 实验内容 2
    disp('------------------------------------');
    disp('实验 2: 不同松弛因子的对比');
    omegas = [0.6, 0.8, 1, 1.1, 1.15, 1.25, 1.3, 1.5, 1.8];
    
    b2 = [0.85653, 0.42076, -0.23948, -0.60632]'; 
    
    fprintf('%-10s %-10s %-15s\n', 'Omega', 'Iter', 'Residual');
    for w = omegas
        [x_W, k_W] = my_sor_matrix(A, b2, x0, w, tol, max_iter);
        fprintf('%-10.2f %-10d %-15.5e\n', w, k_W, norm(A*x_W - b2));
    end


function [x, k] = my_jacobi_matrix(A, b, x0, tol, max_it)
    % Jacobi 迭代公式 (矩阵形式):
    % x(k+1) = D^(-1) * (b - (L + U)*x(k))
    
    n = length(b);
    x = x0;
    
    % 提取矩阵分量
    D = diag(diag(A));      % 对角矩阵
    L = tril(A, -1);        % 严格下三角矩阵
    U = triu(A, 1);         % 严格上三角矩阵

    invD = diag(1 ./ diag(A)); 

    B_jac = -invD * (L + U);
    g_jac = invD * b;
    
    for k = 1:max_it
        x_new = B_jac * x + g_jac;
        
        if norm(x_new - x, inf) < tol
            x = x_new;
            return;
        end
        x = x_new;
    end
    k = max_it;
end

function [x, k] = my_sor_matrix(A, b, x0, w, tol, max_it)

    
    n = length(b);
    x = x0;
    
    % 提取矩阵分量
    D = diag(diag(A));      % 对角矩阵
    L = tril(A, -1);        % 严格下三角矩阵
    U = triu(A, 1);         % 严格上三角矩阵
    
    % 预计算左侧矩阵 M 和右侧矩阵 N
    % M * x_new = N * x_old + P
    M = D + w * L;
    N = (1 - w) * D - w * U;
    P = w * b;
    
    for k = 1:max_it
        % 求解线性方程组 M * x_new = RHS
        % 在 MATLAB 中推荐用左除 \ 而不是 inv(M)
        RHS = N * x + P;
        x_new = M \ RHS;
        
        if norm(x_new - x, inf) < tol
            x = x_new;
            return;
        end
        x = x_new;
    end
    k = max_it;
end