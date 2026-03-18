function L = Cholesky(A)
[n,n]=size(A);
L=zeros(n,n);
L(1,1)=sqrt(A(1,1));
for j=2:n
    L(j,1)=A(j,1)/L(1,1);
end
for k=2:n
    L(k,k)=sqrt(A(k,k)-L(k,1:k-1)*L(k,1:k-1).');
    for j=k+1:n
        L(j,k)=(A(j,k)-L(j,1:k-1)*L(k,1:k-1).')/L(k,k);
    end
end

end