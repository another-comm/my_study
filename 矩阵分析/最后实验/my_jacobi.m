function [x, k, res] = my_jacobi(A, b, x0, tol, max_it)
    n = length(b);
    x = x0;
    invD = diag(1 ./ diag(A));
    L_plus_U = A - diag(diag(A));
    B_jac = -invD * L_plus_U;
    g_jac = invD * b;
    res = norm(b - A*x, 2);
    for k = 1:max_it
        x = B_jac * x + g_jac;
        curr_res = norm(b - A*x, 2);
        res = [res; curr_res];
        if curr_res <= tol
            return;
        end
    end
end