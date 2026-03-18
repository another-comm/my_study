clc
clear
close all
%% create samples:
for i=1:100  
    x1(i) = rand()*5;      %人为保证差异性  
    y1(i) = rand()*5;    
    x2(i) = rand()*5 + 3; %人为保证差异性  
    y2(i) = rand()*5 + 3;
end  
x = [x1,x2];  
y = [y1,y2];  
data = [x;y];
data = data';%一般数据每一行代表一个样本
%plot(data(:,1),data(:,2),'*');  %画出来 
%%---
cluster_n = 2;%类别数
iter = 50;%迭代次数
m = 2;%指数

num_data = size(data,1);%样本个数
num_d = size(data,2);%样本维度
%--初始化隶属度u，条件是每一列和为1
U = rand(cluster_n,num_data);
col_sum = sum(U);
U = U./col_sum(ones(cluster_n,1),:);
%% 循环--规定迭代次数作为结束条件
for i = 1:iter
    %更新c
    for j = 1:cluster_n
        u_ij_m = U(j,:).^m;
        sum_u_ij = sum(u_ij_m);
        sum_1d = u_ij_m./sum_u_ij; 
        c(j,:) = u_ij_m*data./sum_u_ij;
    end
    %-计算目标函数J
    temp1 = zeros(cluster_n,num_data);
    for j = 1:cluster_n
        for k = 1:num_data
            temp1(j,k) = U(j,k)^m*(norm(data(k,:)-c(j,:)))^2;
        end
    end
    J(i) = sum(sum(temp1));
    %更新U
    for j = 1:cluster_n
        for k = 1:num_data
            sum1 = 0;
            for j1 = 1:cluster_n
                temp = (norm(data(k,:)-c(j,:))/norm(data(k,:)-c(j1,:))).^(2/(m-1));
                sum1 = sum1 + temp;
            end
            U(j,k) = 1./sum1;
        end
    end
end
figure;
subplot(1,2,1),plot(J);
[~,label] = max(U); %找到所属的类
subplot(1,2,2);
gscatter(data(:,1),data(:,2),label)
