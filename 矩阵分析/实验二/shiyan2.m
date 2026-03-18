%% 1
n=100;
A=diag(8*ones(n,1),0)+diag(1*ones(n-1,1),1)+diag(1*ones(n-1,1),-1);
b=ones(n,1);
L=Cholesky(A);
y=fwd_sub(L,b);
x=back_sub(L',y);
disp(x);

%% 2
clear;
n=10;
R = rand(n);
L = tril(R);
I = eye(n);
L_inv = zeros(n, n);

for j = 1:n
    b_j = I(:, j);
    x_j = fwd_sub(L, b_j);
    L_inv(:, j) = x_j;
end
disp(L_inv);

disp(inv(L));