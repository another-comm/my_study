clear;
close all;
p=1;

a=zeros(30,2);
for i=1:30
    a(i,:)=[rand(1,1)*60,rand(1,1)*60];
end

N=90;%种群数
h=2;
load city_location
a=citys;
m=size(a,1);
d=zeros(m,m);
fmax=zeros(10000,1);%存储适应函数最大值
exce=zeros(10000,m);%存储每次的最优路线
%% 定义距离矩阵
for i=1:m
    for j=1:m
        d(i,j)=sqrt(sum((a(i,:)-a(j,:)).^2));
    end
end
%% 产生初始群体
A=zeros(N,m);
for i=1:N
    A(i,:)=randperm(m);
end
w=A;
figure(1)
title('初始路径');
B = [A(1,:),A(1,1)];
A1 = a(B,:);
figure(1)
plot(A1(:,1),A1(:,2),'-');
A2 = A;
%生成染色体 
%随机数=种群初始个体
while(p<=100)
for i=1:N
    F(i)=0;
   for j=1:m-1
        F(i)=F(i)+d(A(i,j),A(i,j+1));
   end
        F(i)=F(i)+d(A(i,m),A(i,1));
end
%% 最好的路径保留
 len = F';
 [pm,z]=min(len);%pm对应最短路径值 z是对应的第几个个体
 fmin(p,:)=pm;
 exce(p,:)=A(z,:);
 if p>1  
     if pm>fmin(p-1,:)
         fmin(p,:)=fmin(p-1,:);
         exce(p,:)=exce(p-1,:);
     end
 end

%%适应度评价
 fitness=1./F;
 f2=sum(fitness);
 f3=fitness./f2;

% maxlen=max(len);
% minlen=min(len);
% for i=1:N
% f3(i)=(1-(F(i)-minlen)/(maxlen-minlen+0.0001)).^h;
% end
%%累积概率 为轮盘赌选择操作做准备
f1=cumsum(f3);


%根据适应值筛选
for i=1:N-1
    c=rand;
    k1(i)=find(f1>c,1);
    A(i,:)=A(k1(i),:);%每次选择一个个体，保证种群规模
end
    %[fmax,indmax]=max(fitness);%求当代最佳个体
    A(N,:)=exce(p,:);

Pc=0.95;
B=[randperm(N),randperm(N)];
for i = 1:2*N-1
 if rand<Pc 
%         如果随机生成的数小于交叉概率，即进行交叉操作
%         提取交叉个体
        a1 =A(B(i),:);
        a2 =A(B(i+1),:);
        %交叉操作假设发生在两个相邻的个体
        %单点交叉
        s1 = ceil(rand(1,1)*3);
        s2 = ceil(rand(1,1)*3);
        g = m - max(s1,s2);
        %执行交叉
        a3=A(B(i),s1:s1+g);
        a4=A(B(i+1),s2:s2+g);
        for j=1:g+1
            m1=find(a4(j)==a1);
            a1(m1)=[];
        end
         A(B(i),:)=[a4,a1];
         for j=1:g+1
            m2=find(a3(j)==a2);
           a2(m2)=[];
        end
         A(B(i+1),:)=[a3,a2];    
        % [a1,a2]=cross(a1,a2);
  %      popm_sel(nnper(1),:)=A;
  %      popm_sel(nnper(2),:)=B; 
        % A(B(i),:)=a1;
        % A(B(i+1),:)=a2;

 end
end
%变异
Pb=0.05;
for i=1:N
     if(rand<Pb)
         u1=ceil(rand(1,1)*m);
         u2=ceil(rand(1,1)*m);
         u3=A(i,u1);
         A(i,u1)=A(i,u2);
         A(i,u2)=u3;
     end
end
 p=p+1;
 A2=A;
 end
%[kk,zz]=min(fmax);
figure(2)
title('优化后的最优路径');
A2=a(exce(p-1,:),:);
A2 = [A2;A2(1,:)];     
plot(A2(:,1),A2(:,2),'-');
figure(3)
plot(fmin)