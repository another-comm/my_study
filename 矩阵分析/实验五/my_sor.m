function [x, k] = my_sor(A, b, x0, w, tol, max_it)
    n = length(b);
    x = x0;
    
    for k = 1:max_it
        x_old = x;
        
        for i = 1:n
            sigma = 0;
            for j = 1:n
                if j ~= i                    
                    sigma = sigma + A(i,j) * x(j);
                end
            end          
            x_gs = (b(i) - sigma) / A(i,i);            
            % SOR 加权更新
            x(i) = (1 - w) * x(i) + w * x_gs;
        end        
        if norm(x - x_old, inf) < tol
            return;
        end
    end
    k = max_it;
end