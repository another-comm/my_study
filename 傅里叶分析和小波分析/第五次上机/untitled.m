clc; clear; close all;

% --- 1. 读取图像 ---
% 读取原始载体图像
[fname, pname] = uigetfile({'*.bmp;*.jpg;*.png', 'Image Files'}, '请选择原始图片：');
if fname == 0, return; end
ori_pic = imread(fullfile(pname, fname));
% 如果是彩色图，转换为灰度图以方便处理
if size(ori_pic, 3) == 3
    ori_pic = rgb2gray(ori_pic);
end

figure('Name', '数字水印实验结果');
subplot(2,3,1);
imshow(ori_pic);
title('1. 原图像');

% 读取水印图像
[fname, pname] = uigetfile({'*.bmp;*.jpg;*.png', 'Image Files'}, '请选择水印图片：');
if fname == 0, return; end
watermark = imread(fullfile(pname, fname));
if size(watermark, 3) == 3
    watermark = rgb2gray(watermark);
end

subplot(2,3,2);
imshow(watermark);
title('2. 水印图像');

% --- 2. 小波分解 ---
% 数据类型转换为 double 进行数学运算
ori_pic_trans = double(ori_pic);
watermark_trans = double(watermark);

% 水印图像：1级分解
[Cwr, Swr] = wavedec2(watermark_trans, 1, 'haar');
% 载体图像：2级分解
[Cr, Sr] = wavedec2(ori_pic_trans, 2, 'haar');

% --- 3. 水印嵌入 ---
a = 0.06; % 嵌入强度因子 (Alpha)

% 这里的逻辑是将水印系数平铺嵌入到载体的高频部分
% 注意：这种循环嵌入利用了不同分辨率子带的大小关系
for k = 0 : 1 : size(Cr,2)/size(Cwr,2)-1
    % 处理水平、垂直、对角分量
    idx1 = 1 + size(Cr,2)/4 + k*size(Cwr,2)/4;
    idx2 = size(Cr,2)/4 + (k+1)*size(Cwr,2)/4;
    
    % 嵌入到不同频带
    Cr(idx1 : idx2) = Cr(idx1 : idx2) + a * Cwr(1 + size(Cwr,2)/4 : size(Cwr,2)/2);
    
    idx1_2 = 1 + size(Cr,2)/2 + k*size(Cwr,2)/4;
    idx2_2 = size(Cr,2)/2 + (k+1)*size(Cwr,2)/4;
    Cr(idx1_2 : idx2_2) = Cr(idx1_2 : idx2_2) + a * Cwr(1 + size(Cwr,2)/2 : 3*size(Cwr,2)/4);
    
    idx1_3 = 1 + 3*size(Cr,2)/4 + k*size(Cwr,2)/4;
    idx2_3 = 3*size(Cr,2)/4 + (k+1)*size(Cwr,2)/4;
    Cr(idx1_3 : idx2_3) = Cr(idx1_3 : idx2_3) + a * Cwr(1 + 3*size(Cwr,2)/4 : size(Cwr,2));
end

% 处理低频部分 (Approximation coefficients)
Cr(1:size(Cwr,2)/4) = Cr(1:size(Cwr,2)/4) + a * Cwr(1:size(Cwr,2)/4);

% --- 4. 重构含水印图像 ---
ori_pic_watermarked = waverec2(Cr, Sr, 'haar');
output = uint8(round(ori_pic_watermarked));

subplot(2,3,3);
imshow(output, []);
title('3. 嵌入水印后的图像');

% --- 5. 攻击测试（椒盐噪声） ---
embed_noise = imnoise(output, 'salt & pepper', 0.04);
subplot(2,3,4);
imshow(embed_noise);
title('4. 加椒盐噪声后的图像');

% --- 6. 水印提取 ---
% 6.1 从“无噪声”含水印图像中提取
[Ca, Sa] = wavedec2(ori_pic_watermarked, 2, 'haar'); % 分解含水印图
[Ca1, Sa1] = wavedec2(double(ori_pic), 2, 'haar');   % 分解原图

% 提取公式：(含水印系数 - 原图系数) / a
Cwr_extract = Cwr; % 初始化
Cwr_extract(1:size(Cwr,2)/4) = (Ca(1:size(Cwr,2)/4) - Ca1(1:size(Cwr,2)/4)) / a;
% 注意：此处仅演示了低频部分的简单逆运算，实际应包含所有频带的逆运算

watermark_extracted = waverec2(Cwr_extract, Swr, 'haar');
output_w1 = uint8(round(watermark_extracted));

subplot(2,3,5);
imshow(output_w1, []);
title('5. 提取的水印(无攻击)');

% --- 6.2 从“加噪声”图像中提取 (优化版) ---
[Ca2, Sa2] = wavedec2(double(embed_noise), 2, 'haar'); % 分解噪声图

% 提取水印系数
Cwr_extract_noise = Cwr;
Cwr_extract_noise(1:size(Cwr,2)/4) = (Ca2(1:size(Cwr,2)/4) - Ca1(1:size(Cwr,2)/4)) / a;

% 重构水印
watermark_extracted_noise = waverec2(Cwr_extract_noise, Swr, 'haar');
output_w2 = uint8(round(watermark_extracted_noise));

% ================= 新增优化步骤 =================
% 1. 中值滤波：去除由于攻击产生的“雪花”噪点
output_w2_filtered = medfilt2(output_w2, [3 3]); 

% 2. (可选) 二值化处理：将灰度图强行变为只有黑/白，让水印更清晰
% 如果觉得滤波后还不够清晰，可以取消下面这行的注释
output_w2_filtered = uint8(imbinarize(output_w2_filtered) * 255);
% ==============================================

subplot(2,3,6);
imshow(output_w2_filtered, []); 
title('6. 提取水印(抗噪+滤波优化)');