function [v,beta]=householder_vec(x)
m=length(x);
sigma=x(2:m)'*x(2:m);
v=[1;x(2:m)];
if sigma==0&&x(1)>=0
    beta=0;
elseif sigma==0&&x(1)<0
    beta=-2;
else 
    mu=sqrt(x(1)^2+sigma);
    if x(1)<=0
        v(1)=x(1)-mu;
    else 
        v(1)=-sigma/(x(1)+mu);
    end
    beta = 2 * v(1)^2 / (sigma + v(1)^2);
    v = v / v(1);
end

end