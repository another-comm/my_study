function [x, k,P,r] = conjugate_gradient(A, b, x, tol)
    r = b - A * x;
    p = r;
    k = 0;
    P = [];
    while norm(r) > tol
        P = [P, p];
        Ap = A * p;                
        rr_old = r' * r;        
        
        alpha = rr_old / (p' * Ap);   
        x = x + alpha * p;            
        r = r - alpha * Ap;          
        
        beta = (r' * r) / rr_old;     
        p = r + beta * p;           
        k = k + 1;
    end
end