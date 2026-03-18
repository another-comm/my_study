
clc; clear; close all;

%% 0. 模式选择 
% -------------------------------------------------------------------------
% true  = 方案A: DWT-SVD 
% false = 对照组: 纯 DWT 
USE_SVD = true; 

if USE_SVD
    disp('当前模式：DWT-SVD (方案A)');
else
    disp('当前模式：纯 DWT (对照组)');
end

%% 1. 核心参数调整 
Params.Q_base = 45;      
Params.Q_slope = 0;      
Params.Arnold_Iter = 10; 
Params.Block_Size = 2;   

% --- 图像读取 ---
target_host = 'pic1.png';
raw_img = imread(target_host);
if size(raw_img, 3) == 3, raw_img = rgb2gray(raw_img); end
% 保存原始图像用于显示
Host_Img_Original = raw_img;
Host_Img = double(raw_img);
if max(Host_Img(:)) <= 1.0, Host_Img = Host_Img * 255; end
Host_Img = imresize(Host_Img, [512, 512]);
Host_Img(Host_Img < 0) = 0;
Host_Img(Host_Img > 255) = 255;

target_water = 'pic2.png';
water_raw = imread(target_water);
if size(water_raw, 3) == 3, water_raw = rgb2gray(water_raw); end
% 保存原始水印图像用于显示
Watermark_Img_Original = water_raw;

% 改进的水印预处理：提高清晰度，特别是文字部分
[h, w] = size(water_raw);
target_size = 64;

% 方法1：先锐化原图，增强边缘和文字
water_sharp = imsharpen(water_raw, 'Radius', 2, 'Amount', 1.5);

% 方法2：使用更大的放大倍数，然后高质量缩小
% 计算缩放比例，保持宽高比
scale = min(target_size / h, target_size / w);
new_h = round(h * scale);
new_w = round(w * scale);

% 先放大到更高分辨率（8倍）
temp_h = h * 8;
temp_w = w * 8;
Watermark_Img = imresize(water_sharp, [temp_h, temp_w], 'bicubic');

% 缩小到目标尺寸
Watermark_Img = imresize(Watermark_Img, [new_h, new_w], 'bicubic');

% 方法3：使用自适应阈值进行二值化，更好地保留文字细节
% 先转换为0-1范围
Watermark_Img = mat2gray(Watermark_Img);
% 使用自适应阈值（Otsu方法）
threshold = graythresh(Watermark_Img);
Watermark_Img = imbinarize(Watermark_Img, threshold);
Watermark_Img = double(Watermark_Img);

% 创建64x64的白色背景，将水印居中放置
Watermark_Img_Final = ones(target_size, target_size);
start_h = round((target_size - new_h) / 2) + 1;
start_w = round((target_size - new_w) / 2) + 1;
Watermark_Img_Final(start_h:start_h+new_h-1, start_w:start_w+new_w-1) = Watermark_Img;
Watermark_Img = Watermark_Img_Final;

%% 2. 嵌入过程
% -------------------------------------------------------------------------
fprintf('正在嵌入水印 (Q=%d)...\n', Params.Q_base);
Watermark_Scrambled = arnold_map(Watermark_Img, Params.Arnold_Iter, 0);

[LL1, HL1, LH1, HH1] = dwt2(Host_Img, 'db4');
[LL2, HL2, LH2, HH2] = dwt2(LL1, 'db4');

[rows, cols] = size(HL2); 
blk = Params.Block_Size;
cnt = 1;
HL2_W = HL2; 
W_vec = Watermark_Scrambled(:);
Max_Bits = length(W_vec);

for r = 1:blk:(rows - blk + 1)
    for c = 1:blk:(cols - blk + 1)
        if cnt > Max_Bits; break; end
        
        Block = HL2(r:r+blk-1, c:c+blk-1);
        
        % ================= 【分支逻辑：获取特征值】 =================
        if USE_SVD
            [U, S, V] = svd(Block);
            feat_val = S(1,1); % 方案A：取最大奇异值
        else
            % 对照组：直接取 DWT 系数 (取绝对值以防止负数干扰量化)
            feat_val = abs(Block(1,1)); 
        end
        % ==========================================================
        
        % Q 计算 (保持不变)
        Block_Var = std2(Block)^2; 
        Q_step = Params.Q_base + Params.Q_slope * log(1 + Block_Var);
        
        % QIM 嵌入 (保持不变)
        k = floor(feat_val / Q_step);
        bit = W_vec(cnt);
        if bit == 1
            feat_new = k * Q_step + 0.75 * Q_step;
        else
            feat_new = k * Q_step + 0.25 * Q_step;
        end
        
        % ================= 【分支逻辑：写回特征值】 =================
        if USE_SVD
            S(1,1) = feat_new;
            Block_Out = U * S * V';
        else
            % 对照组：恢复符号并写回系数
            s_sign = sign(Block(1,1));
            if s_sign == 0, s_sign = 1; end
            Block_Out = Block;
            Block_Out(1,1) = feat_new * s_sign;
        end
        HL2_W(r:r+blk-1, c:c+blk-1) = Block_Out;
        % ==========================================================
        
        cnt = cnt + 1;
    end
end

LL1_New = idwt2(LL2, HL2_W, LH2, HH2, 'db4');
LL1_New = LL1_New(1:size(HL1,1), 1:size(HL1,2)); 
Host_Watermarked = idwt2(LL1_New, HL1, LH1, HH1, 'db4');
Host_Watermarked = Host_Watermarked(1:512, 1:512);
Host_Watermarked(Host_Watermarked < 0) = 0;
Host_Watermarked(Host_Watermarked > 255) = 255;

% === 【修改】计算不可感知性指标 (PSNR & SSIM) 并展示 ===
psnr_val = psnr(uint8(Host_Watermarked), uint8(Host_Img));
ssim_val = ssim(uint8(Host_Watermarked), uint8(Host_Img)); % 计算 SSIM

fprintf('嵌入完成。\n');
fprintf('不可感知性测试 -> PSNR: %.2f dB | SSIM: %.4f\n', psnr_val, ssim_val);

%% 3. 攻击与提取
% -------------------------------------------------------------------------
Attack_List = {'No Attack', 'Gaussian Noise', 'JPEG Compression', 'Cropping', 'Rotation'};
% 调整一下位置，防止窗口重叠
figure('Name', ['鲁棒性测试 - ' (ternary(USE_SVD, 'DWT-SVD', '纯DWT'))], 'NumberTitle', 'off', 'Position', [100, 100, 1200, 700]);

% 在第一行显示三个原图（使用原始图像）
subplot(3, 5, 1); 
imshow(Host_Img_Original); 
title('原载体图像');

subplot(3, 5, 2); 
imshow(Watermark_Img_Original); 
title('原水印图像');

subplot(3, 5, 3); 
imshow(uint8(Host_Watermarked)); 
title(['加水印后 (PSNR=' num2str(psnr_val, '%.2f') 'dB)']);

for i = 1:length(Attack_List)
    type = Attack_List{i};
    Attacked_Img = Host_Watermarked;
    
    switch type
        case 'Gaussian Noise'
            Attacked_Img = imnoise(uint8(Attacked_Img), 'gaussian', 0, 0.005);
            Attacked_Img = double(Attacked_Img);
        case 'JPEG Compression'
            imwrite(uint8(Attacked_Img), 'temp.jpg', 'Quality', 40); 
            Attacked_Img = double(imread('temp.jpg'));
        case 'Cropping'
            Attacked_Img(1:128, 1:128) = 0; 
        case 'Rotation'
            Attacked_Img = double(imrotate(Attacked_Img, 2, 'bilinear', 'crop'));
    end
    
    % --- 盲提取 ---
    [LL1_A, HL1_A, LH1_A, HH1_A] = dwt2(Attacked_Img, 'db4');
    [LL2_A, HL2_A, LH2_A, HH2_A] = dwt2(LL1_A, 'db4');
    [rows_a, cols_a] = size(HL2_A);
    
    Extracted_Vec = zeros(Max_Bits, 1);
    cnt = 1;
    
    for r = 1:blk:(rows_a - blk + 1)
        for c = 1:blk:(cols_a - blk + 1)
            if cnt > Max_Bits; break; end
            
            Block = HL2_A(r:r+blk-1, c:c+blk-1);
            
            % ================= 【分支逻辑：提取特征】 =================
            if USE_SVD
                [~, S, ~] = svd(Block);
                feat_val = S(1,1);
            else
                feat_val = abs(Block(1,1)); % 对照组：直接取 DWT 系数绝对值
            end
            % ==========================================================
            
            Block_Var = std2(Block)^2;
            Q_step = Params.Q_base + Params.Q_slope * log(1 + Block_Var);
            
            if mod(feat_val, Q_step) >= 0.5 * Q_step
                Extracted_Vec(cnt) = 1; 
            else
                Extracted_Vec(cnt) = 0; 
            end
            cnt = cnt + 1;
        end
    end
    
    Extracted_Scrambled = reshape(Extracted_Vec, [64, 64]);
    Extracted_Watermark = arnold_map(Extracted_Scrambled, Params.Arnold_Iter, 1);
    nc = calc_nc(Watermark_Img, Extracted_Watermark);
    
    subplot(3, 5, 5+i); imshow(uint8(Attacked_Img)); title(type);
    subplot(3, 5, 10+i); imshow(Extracted_Watermark, []); title(['NC: ', num2str(nc, '%.2f')]);
    
    fprintf('攻击类型: %-18s | NC值: %.4f\n', type, nc);
end

% ---------------- 辅助函数 ----------------
function out = arnold_map(in, iter, inv)
    [h, w] = size(in); out = zeros(h, w); tmp = in;
    for k=1:iter
        for y=1:h, for x=1:w
            if inv==0, xx=mod(x+y-2,w)+1; yy=mod(x+2*y-3,h)+1;
            else, xx=mod(2*(x-1)-(y-1),w)+1; yy=mod(-(x-1)+(y-1),h)+1; end
            out(yy,xx)=tmp(y,x);
        end, end, tmp=out;
    end
end
function nc = calc_nc(i1, i2), i1=double(i1); i2=double(i2); nc=sum(sum(i1.*i2))/sqrt(sum(sum(i1.^2))*sum(sum(i2.^2))); if isnan(nc), nc=0; end, end

% 简单的三元运算符替代
function val = ternary(cond, T, F)
    if cond, val = T; else, val = F; end
end