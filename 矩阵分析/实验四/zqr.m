function [Q,R]=zqr(A)
[m,n]=size(A);
Q=eye(m);
R=A;
for j=1:n
    if j<m
        [v,beta]=householder_vec(R(j:m,j));
        subR=R(j:m,j:n);
        R(j:m,j:n)=subR-beta*v*(v'*subR);
        w=[zeros(j-1,1);v];
        Q=Q-beta*w*(w'*Q);
    end
end
Q=Q';
end