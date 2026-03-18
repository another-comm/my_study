function [x, k] = my_jacobi(A, b, x0, tol, max_it)
    n = length(b);
    x = x0;
    x_new = x;
    
    for k = 1:max_it
        for i = 1:n
            sigma = 0;
            for j = 1:n
                if j ~= i
                    sigma = sigma + A(i,j) * x(j);
                end
            end
            x_new(i) = (b(i) - sigma) / A(i,i);
        end
        
        if norm(x_new - x, inf) < tol
            x = x_new;
            return;
        end
        
        x = x_new; 
    end
    k = max_it; 
end