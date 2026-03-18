clc; clear; close all;

% 定义参数
N = 1000;                    % 截断阶数，画系数时更大一点
k = -N:N;                   % k的取值
c_k = zeros(size(k));       % 储存系数

% 计算傅里叶系数
for idx = 1:length(k)
    kk = k(idx);
    if kk == 0
        c_k(idx) = 0;
    elseif mod(kk,2) ~= 0   % 奇数
        c_k(idx) = (2*1i)/(pi*kk);
    else
        c_k(idx) = 0;       % 偶数
    end
end

% ========== 1) 画傅里叶系数 ==========
figure;
stem(k, abs(c_k), 'filled');
xlabel('k'); ylabel('|c_k|'); 
title('傅里叶系数幅值');
grid on;

% ========== 2) 信号重构 ==========
x = linspace(0,4*pi,2000);  % 横轴拉长: 2个周期
f_recon = zeros(size(x));
for idx = 1:length(k)
    f_recon = f_recon + c_k(idx)*exp(1i*k(idx)*x);
end

figure;
plot(x, real(f_recon), 'LineWidth', 1.5); hold on;
% 原信号（多个周期）
f_true = -ones(size(x));
f_true(mod(x,2*pi) >= pi) = 1;
plot(x, f_true, '--','LineWidth',1.5);
xlabel('x'); ylabel('f(x)');
legend('重构信号','原信号');
title(['傅里叶级数重构 (N = ' num2str(N) ', 2个周期)']);
grid on;

% ========== 3) Parseval恒等式 ==========
% Parseval: (1/2pi)∫|f(x)|^2 dx = sum |c_k|^2
% 左边：能量积分 (一个周期)
x1 = linspace(0,2*pi,2000);
f_true1 = -ones(size(x1));
f_true1(x1>=pi) = 1;
LHS = (1/(2*pi)) * trapz(x1, abs(f_true1).^2);

% 右边：系数平方和
RHS = cumsum(abs(c_k).^2);  % 逐步累加
k_idx = 1:length(RHS);

figure;
plot(k_idx, RHS, 'LineWidth', 1.5);
hold on;
yline(LHS, 'r--','LineWidth',1.5);
xlabel('阶数累积'); ylabel('能量');
legend('右边：Σ|c_k|^2','左边：∫|f|^2');
title('Parseval 恒等式验证');
grid on;

% ========== 4) Parseval恒等式：固定 N 对比 ==========
% 直接比较 LHS 和 sum|c_k|^2（固定 N）

RHS_fixedN = sum(abs(c_k).^2);   % 已经算好的 c_k，直接取和

figure;
bar([1,2],[LHS, RHS_fixedN],0.4);   % 柱状图
set(gca,'xticklabel',{'LHS','RHS'});
ylabel('能量数值');
title(['Parseval 恒等式对比 (固定 N = ' num2str(N) ')']);
grid on;


