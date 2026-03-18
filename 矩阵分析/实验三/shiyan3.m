
%% 1
n = 84;
A = diag(6*ones(n,1)) + diag(1*ones(n-1,1),1) + diag(8*ones(n-1,1),-1);
b = 15*ones(n,1);
b(1) = 7; 
b(n) = 14;
[L0, U0, P0] = gauss1(A);
y0 = fwd_sub(L0, P0*b);
x0 = back_sub(U0, y0);
disp(x0);
[L1,U1,P1] = gauss2(A);
y1 = fwd_sub(L1, P1*b);
x1 = back_sub(U1, y1);

disp(x1);

x=ones(n,1);
disp(norm(x0-x,inf));
disp(norm(x1-x,inf));
condA2 = cond(A, 2);   % 2范数条件数
disp(condA2);
%% 3
clear;
n = 40;
A = zeros(n);
for i = 1:n
    for j = 1:n
        A(i,j) = 1 / (i + j - 1);
    end
end

b = zeros(n,1);
for i = 1:n
    b(i) = sum( 1 ./ (i + (1:n) - 1) );
end

[L,U,P] = gauss2(A);
y = fwd_sub(L, P*b);
x = back_sub(U, y);
disp(x);

xe = ones(n,1);
err = norm(x - xe, inf);
disp(err);
%% 4
clear; clc;
c = zeros(16,1);

for n = 5:20
    H = hilb(n);
    nH = max(sum(abs(H),2));
    Hinv = inv(H);
    nHinv = max(sum(abs(Hinv),2));
    c(n-5+1) = nH * nHinv;
end

for n = 5:20
    fprintf('%d %.4e\n', n, c(n-5+1));
end






