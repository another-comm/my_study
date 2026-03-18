function [L,U,P] = gauss2(A)
    n = size(A,1);
    U = A;
    L = eye(n);
    P = eye(n);

    for k = 1:n-1
        [~, idx] = max(abs(U(k:n, k)));
        r = idx + k - 1;   
        if r ~= k
            U([k r], :) = U([r k], :);    
            P([k r], :) = P([r k], :);           
            if k > 1
                L([k r], 1:k-1) = L([r k], 1:k-1);   
            end
        end

        for i = k+1:n
            m = U(i,k) / U(k,k);
            L(i,k) = m;
            U(i, k:n) = U(i,k:n) - m * U(k,k:n);
        end
    end
end
