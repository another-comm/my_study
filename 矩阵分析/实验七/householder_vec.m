function [v,beta]=householder_vec(x)
    x = x(:);
    m = length(x);
    if m > 1
        sigma = x(2:m)' * x(2:m);
    else
        sigma = 0;
    end
    v = [1; zeros(m-1, 1)];
    if m > 1
        v(2:m) = x(2:m);
    end
    
    if sigma == 0 && x(1) >= 0
        beta = 0;
    elseif sigma == 0 && x(1) < 0
        beta = 2;
    else 
        mu = sqrt(x(1)^2 + sigma);
        if x(1) <= 0
            v(1) = x(1) - mu;
        else 
            v(1) = -sigma / (x(1) + mu);
        end
        beta = 2 * v(1)^2 / (sigma + v(1)^2);
        v = v / v(1);
    end
end