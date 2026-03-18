function [Q, R] = zqr(A)
    [m, n] = size(A);
    Q = eye(m);
    R = A;
    for j = 1:min(n, m-1)
        x = R(j:m, j);
        [v, beta] = householder_vec(x);

        subR = R(j:m, j:n);
        R(j:m, j:n) = subR - beta * v * (v' * subR);
        
        w = zeros(m, 1);
        w(j:m) = v;
        Q = Q - beta * (Q * w) * w';
    end
end