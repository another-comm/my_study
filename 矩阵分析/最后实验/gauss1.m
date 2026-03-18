function [L,U,P] = gauss1(A)
    n = size(A,1);
    L = eye(n);
    U = A;
    P = eye(n);  
    for k = 1:n-1
        for i = k+1:n
            m = U(i,k)/U(k,k);
            L(i,k) = m;
            U(i,k:n) = U(i,k:n) - m * U(k,k:n);
        end
    end
end