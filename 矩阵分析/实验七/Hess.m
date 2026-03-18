function [H, Q] = Hess(A)
    n = size(A, 1);
    Q = eye(n);
    for k = 1:n-2
        [v, beta] = householder_vec(A(k+1:n, k));
        Q1 = eye(n-k) - beta * (v * v');
        Q2 = zeros(n,n);
        Q2(1:k,1:k)=eye(k);
        Q2(k+1:n, k+1:n) = Q1;

        Q = Q * Q2;      
        A(k+1:n, k:n) = Q1 * A(k+1:n, k:n);
        A(1:n, k+1:n) = A(1:n, k+1:n) * Q1;
    end
    H = A;
end