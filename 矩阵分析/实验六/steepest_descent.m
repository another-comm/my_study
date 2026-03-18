function [x, k,r] = steepest_descent(A, b, x, tol)
    r = b - A * x;
    k = 0;
    while norm(r) > tol
        Ar = A * r;               
        alpha = (r' * r) / (r' * Ar); 
        x = x + alpha * r;        
        r = r - alpha * Ar;   
 
        k = k + 1;
    end
end