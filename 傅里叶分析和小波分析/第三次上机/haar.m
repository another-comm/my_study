%% 
clc;  
clear;  
% 获取噪声信号  
load leleccum;  
indx = 1:3450;  
noisez = leleccum(indx);  
  
%信号的分解  
wname = 'haar';   
lev = 3;  
[c,l] = wavedec(noisez,lev,wname);  
  
%求取阈值  
sigma = wnoisest(c,l,1);%使用库函数wnoisest提取第一层的细节系数来估算噪声的标准偏差  
N = numel(noisez);%整个信号的长度  
thr = sigma*sqrt(2*log(N));%最终阈值  
  
%全局阈值处理  
keepapp = 1;%近似系数不作处理  
denoisexs = wdencmp('gbl',c,l,wname,lev,thr,'s',keepapp);  
denoisexh = wdencmp('gbl',c,l,wname,lev,thr,'h',keepapp);  
  
% 作图  
subplot(311),   
plot(noisez), title('原始噪声信号');  
subplot(312),  
plot(denoisexs), title('matlab软阈值去噪信号') ;  
subplot(313),  
plot(denoisexh), title('matlab硬阈值去噪信号') ;  

