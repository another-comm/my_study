function draw_phase(m,f,phase)
% 相位谱绘制
% f - 频域
% ppy - 幅值信息
% phase - 相位信息
h=stem(f(1,1:m+1),phase(1,1:m+1)*180/pi,'color',[123/255,159/255,47/255]);
set(h,'LineWidth',3*get(h,'LineWidth'));
axis([0,m+1,min(phase(1,1:m+1)*180/pi)-15,max(phase(1,1:m+1)*180/pi)+15])
title('离散相位谱（侧视图）');
xlabel('频域范围f');
ylabel('相位角（单位：°）');
grid on
end
