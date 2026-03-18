function [lambda_max, v_max] = power_method(A, max_iter, tol)
    n = size(A, 1);
    u = ones(n, 1);    
    mu = 0; 
    err = inf; 
    k = 0;
    while err > tol && k < max_iter
        k = k + 1;
        y = A * u;             
        mu_old = mu;       
        mu = norm(y, inf);  
        u = y / mu;         
        if k > 1
            err = abs(mu - mu_old) ;
        end
    end
    lambda_max = mu;
    v_max = u; 
end