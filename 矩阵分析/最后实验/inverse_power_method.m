function [lambda_min, v_min] = inverse_power_method(A, max_iter, tol)
    n = size(A, 1);
    [L, U] = lu_dp(A); 
    u = ones(n, 1);    
    mu = 0; 
    err = inf; 
    k = 0;  
    while err > tol && k < max_iter
        k = k + 1;
        z = fwd_sub(L, u);   
        y = back_sub(U, z);  
        mu_old = mu;          
        mu = norm(y, inf);             
        u = y / mu;                   
        if k > 1
            err = abs(mu - mu_old) ;
        end
    end
    
    lambda_min = 1 / mu;      
    v_min = u;                 
end