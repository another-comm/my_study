function [L,U] = lu_dp(A)
[n,~]=size(A);
L=eye(n);
U=A;
for k=1:n-1
    for i=k+1:n
        L(i,k)=U(i,k)/U(k,k);
        U(i,k:n)=U(i,k:n)-L(i,k)*U(k,k:n);
    end
end    
end