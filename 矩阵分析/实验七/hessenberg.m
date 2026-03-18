function [H, Q] = hessenberg(A)
    n = size(A, 1);
    H = A;       
    Q = eye(n);    
    
    for k = 1 : n-2
        x = H(k+1:n, k);
        [v, beta] = householder_vec(x);
        m_dim = length(v);       
        I = eye(m_dim);    
        P = I - beta * (v * v'); 
        H(k+1:n, k:n) = P * H(k+1:n, k:n);       
        H(1:n, k+1:n) = H(1:n, k+1:n) * P;  
        Q(1:n, k+1:n) = Q(1:n, k+1:n) * P;
    end
end