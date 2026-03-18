clc;
clear all;
close all;                        % 清理工作空间
clear;                 
 
X=imread('C:\Users\32610\Pictures\Screenshots\屏幕截图 2024-01-12 200049.png');            
X=rgb2gray(X);
subplot(221); imshow(X);             
title('原始图像');                  
%对图像用小波进行层小波分解
[c,s]=wavedec2(X,2,'bior3.7');
%提取小波分解结构中的一层的低频系数和高频系数
cal=appcoef2(c,s,'bior3.7',1);
ch1=detcoef2('h',c,s,1);      %水平方向
cv1=detcoef2('v',c,s,1);      %垂直方向
cd1=detcoef2('d',c,s,1);      %斜线方向

%各频率成份重构
a1=wrcoef2('a',c,s,'bior3.7',1);
h1=wrcoef2('h',c,s,'bior3.7',1);
v1=wrcoef2('v',c,s,'bior3.7',1);
d1=wrcoef2('d',c,s,'bior3.7',1);
c1=[a1,h1;v1,d1];
subplot(222),imshow(c1,[]);
title ('分解后低频和高频信息');
 
%进行图像压缩
%保留小波分解第一层低频信息
%首先对第一层信息进行量化编码
ca1=appcoef2(c,s,'bior3.7',1);
ca1=wcodemat(ca1,440,'mat',0);
%改变图像高度并显示
ca1=0.5*ca1;
subplot(223);imshow(cal,[]);
title('第一次压缩图像');

%保留小波分解第二层低频信息进行压缩
ca2=appcoef2(c,s,'bior3.7',2);
%首先对第二层信息进行量化编码
ca2=wcodemat(ca2,440,'mat',0);
%改变图像高度并显示
ca2=0.25*ca2;
subplot(224);imshow(ca2,[]);
title('第二次压缩图像');