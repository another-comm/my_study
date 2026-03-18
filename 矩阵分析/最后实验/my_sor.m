function [x, k, res] = my_sor(A, b, x0, w, tol, max_it)
    n = length(b);
    x = x0;
    D = diag(diag(A));
    L = tril(A, -1);
    U = triu(A, 1);
    M = D + w * L;
    N = (1 - w) * D - w * U;
    P = w * b;
    res = norm(b - A*x, 2);
    for k = 1:max_it
        x = M \ (N * x + P);
        curr_res = norm(b - A*x, 2);
        res = [res; curr_res]; 
        if curr_res <= tol
            return;
        end
    end
end