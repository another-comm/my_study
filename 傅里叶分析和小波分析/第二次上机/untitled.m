%% 
% 求解 f(t) = exp(-2|t|) 的傅里叶变换
syms t w % 定义符号变量 t 和 w
f = exp(-2*abs(t))
F = fourier(f)

% 求解单边指数信号 f(t) = exp(-5t)u(t) 的傅里叶变换及频谱
syms t w phase im re
% 注意：heaviside(t) 函数的第一个字母必须小写
f = exp(-5*t) * heaviside(t) 
F = fourier(f)

% 提取幅度和相位
F_abs = abs(F);    % 幅度谱
im = imag(F);      % 虚部
re = real(F);      % 实部
phase = atan(im/re); % 相位谱

% 绘制幅度谱和相位谱
figure; % 创建新图窗
subplot(2,1,1);
ezplot(F_abs, [-20, 20]); % 绘制幅度谱，设置w的显示范围
grid on;
title('单边指数信号的幅度谱 |F(j\omega)|');
xlabel('\omega');
ylabel('|F(j\omega)|');

subplot(2,1,2);
ezplot(phase, [-20, 20]); % 绘制相位谱，设置w的显示范围
grid on;
title('单边指数信号的相位谱 \phi(\omega)');
xlabel('\omega');
ylabel('\phi(\omega)');

%% 

% 1. 信号参数设置
Fs = 1000;         % 采样频率 (Hz)
T = 1/Fs;          % 采样周期
L = 1500;          % 信号长度 (采样点数)
t = (0:L-1)*T;     % 时间向量

% 2. 构造复合信号：包含 50Hz 和 120Hz 的正弦波
f1 = 50;           % 第一个频率分量 (Hz)
f2 = 120;          % 第二个频率分量 (Hz)
x = 0.7*sin(2*pi*f1*t) + sin(2*pi*f2*t); % 叠加信号

% 3. 绘制时域波形
figure;
subplot(2,1,1);
plot(t,x);
title('复合信号 x(t) 的时域波形');
xlabel('时间 t (s)');
ylabel('幅度');
grid on;

% 1. 执行 L 点 FFT
X = fft(x);

% 2. 计算双边频谱 P2
P2 = abs(X/L);

% 3. 计算单边频谱 P1
P1 = P2(1:L/2+1);
P1(2:end-1) = 2*P1(2:end-1); % 非直流分量幅度乘以 2 (能量守恒)

% 4. 构造频率轴 f
f = Fs*(0:(L/2))/L; % 正频率轴

% 5. 绘制单边幅度谱
subplot(2,1,2);
plot(f,P1);
title('信号的单边幅度频谱 (FFT结果)');
xlabel('频率 f (Hz)');
ylabel('|P1(f)|');
grid on;

%% 
%=====================================================
% 图像傅立叶变换实验：正/反变换及频谱可视化（按要求分别显示）
%=====================================================

% 1. 图像读取与预处理
% 实际操作时，请确保文件路径正确，并且 MATLAB 具有读取该路径的权限
I = imread("C:\Users\32610\Pictures\Screenshots\屏幕截图 2024-01-12 200049.png"); % 读取图像

% 确保是灰度图，并转换为 double 类型
if size(I, 3) == 3
    I = rgb2gray(I);
end
I_double = double(I); 

% 2. 傅立叶正变换
F = fft2(I_double);

% 3. 频谱中心化
F_shift = fftshift(F);

% 4. 幅度谱计算与对数变换
M = abs(F_shift); 
M_log = log(1 + M);

% 5. 相位谱计算
Phi = angle(F_shift);

% 6. 傅里叶反变换（验证）
% 逆移位
F_unshift = ifftshift(F_shift); 
% 傅里叶反变换
I_re = ifft2(F_unshift);
% 取实部（ifft2的结果可能存在极小的虚部舍入误差）
I_re_final = real(I_re); 

% === 可视化部分：分别在不同的 Figure 中显示 ===

% 图 1：原始图像
figure('name', '原始图像'); 
imshow(uint8(I_double));
title('原始图像');

% 图 2：幅度谱 (对数变换)
figure('name', '幅度谱 (对数变换)'); 
imshow(M_log, []); % [] 表示自动定标显示
title('幅度谱 (对数变换)');
colormap('jet'); 

% 图 3：相位谱
figure('name', '相位谱'); 
imshow(Phi, []); % 相位谱通常在 [-pi, pi] 之间
title('相位谱');
colormap('gray');

% 图 4：傅里叶反变换重构图像
figure('name', '傅里叶反变换重构图像'); 
imshow(uint8(I_re_final));
title('傅里叶反变换重构图像');

% 清理变量
clear all;