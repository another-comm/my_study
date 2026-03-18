%% 主脚本：Haar小波二级分解
clear all;
close all;
clc;

% 1. 读取图像
full_path_to_image = 'C:\Users\32610\Pictures\Screenshots\屏幕截图 2024-01-12 200049.png';
img_original = imread(full_path_to_image);

% 2. 检查图像是否为RGB（彩色）
if size(img_original, 3) == 3
    img_gray = rgb2gray(img_original);
    disp('检测到RGB图像，已自动转换为灰度图。');
else
    img_gray = img_original;
end

% 3. 转换为double类型
img = double(img_gray);

% 4. 裁剪图像以确保m和n是4的倍数
[m, n] = size(img);
m_new = floor(m / 4) * 4;
n_new = floor(n / 4) * 4;

if m ~= m_new || n ~= n_new
    disp(['原始图像尺寸 ' num2str(m) 'x' num2str(n) ' 不适合2级分解。']);
    img = img(1:m_new, 1:n_new);
    [m, n] = size(img);
    disp(['已自动裁剪为 ' num2str(m) 'x' num2str(n)]);
end

% 5. 进行一级分解
% 调用 haar_dwt2D 函数 (haar_dwt2D.m)
[LL, LH, HL, HH] = haar_dwt2D(img);  
img_level1 = [LL, LH; HL, HH];      % 拼接一级分解的结果

% 6. 准备进行二级分解
imgn = zeros(m, n);
m_half = m / 2;
n_half = n / 2;

% 6a. 对 LL 分区进行二级分解
[LL2, LH2, HL2, HH2] = haar_dwt2D(img_level1(1:m_half, 1:n_half));
imgn(1:m_half, 1:n_half) = [LL2, LH2; HL2, HH2];

% 6b. 对 LH 分区进行二级分解
[LL2, LH2, HL2, HH2] = haar_dwt2D(img_level1(1:m_half, n_half+1:n));
imgn(1:m_half, n_half+1:n) = [LL2, LH2; HL2, HH2];

% 6c. 对 HL 分区进行二级分解
[LL2, LH2, HL2, HH2] = haar_dwt2D(img_level1(m_half+1:m, 1:n_half));
imgn(m_half+1:m, 1:n_half) = [LL2, LH2; HL2, HH2];

% 6d. 对 HH 分区进行二级分解
[LL2, LH2, HL2, HH2] = haar_dwt2D(img_level1(m_half+1:m, n_half+1:n));
imgn(m_half+1:m, n_half+1:n) = [LL2, LH2; HL2, HH2];

% 7. 显示最终的二级分解图像
figure;
imshow(imgn);
title('二级Haar小波分解');
