%% 实验1：平行板电容器电场分布分析
clear; clc; close all;

%% 基础参数设置
U = 1;          % 电压 (V)
S = 100;        % 面积 (mm^2)
d1 = 2;         % 介质1厚度 (mm)
d2 = 4;         % 介质2厚度 (mm)

% 将单位转换为米
S_m = S * 1e-6;       % mm^2 -> m^2
d1_m = d1 * 1e-3;      % mm -> m
d2_m = d2 * 1e-3;      % mm -> m

fprintf('========== 实验1：平行板电容器电场分布分析 ==========\n\n');
fprintf('基本参数：\n');
fprintf('  电压 U = %.2f V\n', U);
fprintf('  面积 S = %.2f mm^2\n', S);
fprintf('  介质1厚度 d1 = %.2f mm\n', d1);
fprintf('  介质2厚度 d2 = %.2f mm\n', d2);

%% ==================== 第一部分：忽略介质导电性 ====================
fprintf('\n========== 第一部分：忽略介质导电性 (静电场) ==========\n');

% 真空介电常数
eps0 = 8.854e-12;  % F/m

% 固定 er1 = 1, er2 从 1 变化到 10
er1_fixed = 1;
er2_range = 1:0.1:10;
C_part1 = zeros(size(er2_range));

fprintf('\n情况(1): ε_r1 = 1, ε_r2 从 1 变化到 10\n');
for i = 1:length(er2_range)
    er2 = er2_range(i);
    eps1 = er1_fixed * eps0;
    eps2 = er2 * eps0;
    C = (eps1 * eps2 * S_m) / (eps1 * d2_m + eps2 * d1_m);
    C_part1(i) = C * 1e12;  % 转换为 pF
end

% 固定 er2 = 1, er1 从 1 变化到 10
er2_fixed = 1;
er1_range = 1:0.1:10;
C_part2 = zeros(size(er1_range));

fprintf('情况(2): ε_r2 = 1, ε_r1 从 1 变化到 10\n');
for i = 1:length(er1_range)
    er1 = er1_range(i);
    eps1 = er1 * eps0;
    eps2 = er2_fixed * eps0;
    C = (eps1 * eps2 * S_m) / (eps1 * d2_m + eps2 * d1_m);
    C_part2(i) = C * 1e12;  % 转换为 pF
end

% 计算电场强度
er1 = 1; er2 = 1;  % 取典型值
eps1 = er1 * eps0;
eps2 = er2 * eps0;
D = U / (d1_m/eps1 + d2_m/eps2);
E1 = D / eps1;
E2 = D / eps2;

fprintf('\n当 ε_r1 = ε_r2 = 1 时:\n');
fprintf('  电位移 D = %.6e C/m^2\n', D);
fprintf('  介质1电场强度 E1 = %.2f V/m\n', E1);
fprintf('  介质2电场强度 E2 = %.2f V/m\n', E2);
fprintf('  电容 C = %.4f pF\n', C_part1(1));

%% ==================== 第二部分：考虑介质导电性 ====================
fprintf('\n========== 第二部分：考虑介质导电性 (恒定电场) ==========\n');

% 固定参数
sigma2_fixed = 0.1;  % S/m

% 情况(1): sigma1 从 0.01 到 0.1 S/m, sigma2 = 0.1 S/m
sigma1_range = 0.01:0.01:0.1;
G_part1 = zeros(size(sigma1_range));

fprintf('\n情况(1): σ_1 从 0.01 到 0.1 S/m, σ_2 = 0.1 S/m\n');
for i = 1:length(sigma1_range)
    sigma1 = sigma1_range(i);
    sigma2 = sigma2_fixed;
    G = (sigma1 * sigma2 * S_m) / (sigma1 * d2_m + sigma2 * d1_m);
    G_part1(i) = G * 1e6;  % 转换为 uS
end

% 情况(2): sigma1 从 0.01 到 0.1 S/m, sigma2 从 0.01 到 0.3 S/m
sigma1_v2 = 0.01:0.01:0.1;
sigma2_v2 = 0.01:0.03:0.3;
G_part2 = zeros(length(sigma1_v2), length(sigma2_v2));

fprintf('情况(2): σ_1 从 0.01 到 0.1 S/m, σ_2 从 0.01 到 0.3 S/m\n');
for i = 1:length(sigma1_v2)
    for j = 1:length(sigma2_v2)
        sigma1 = sigma1_v2(i);
        sigma2 = sigma2_v2(j);
        G = (sigma1 * sigma2 * S_m) / (sigma1 * d2_m + sigma2 * d1_m);
        G_part2(i, j) = G * 1e6;  % 转换为 uS
    end
end

% 计算典型情况下的电场
sigma1 = 0.05; sigma2 = 0.1;
J = U / (d1_m/sigma1 + d2_m/sigma2);
E1_sigma = J / sigma1;
E2_sigma = J / sigma2;

fprintf('\n当 σ_1 = 0.05 S/m, σ_2 = 0.1 S/m 时:\n');
fprintf('  电流密度 J = %.6e A/m^2\n', J);
fprintf('  介质1电场强度 E1 = %.2f V/m\n', E1_sigma);
fprintf('  介质2电场强度 E2 = %.2f V/m\n', E2_sigma);
fprintf('  电导 G = %.4f uS\n', G_part1(5));

%% ==================== 绘图 ====================
figure('Units', 'centimeters', 'Position', [5, 5, 16, 12]);

% 图1: 电容随介电常数变化
subplot(2, 2, 1);
plot(er2_range, C_part1, 'b-', 'LineWidth', 1.5);
hold on;
plot(er1_range, C_part2, 'r--', 'LineWidth', 1.5);
xlabel('相对介电常数 \it\epsilon_r');
ylabel('电容 \itC (pF)');
title('电容随相对介电常数变化曲线');
legend('\epsilon_{r2} 变化 (\epsilon_{r1}=1)', '\epsilon_{r1} 变化 (\epsilon_{r2}=1)', 'Location', 'best');
grid on;

% 图2: 电导随电导率变化 (情况1)
subplot(2, 2, 2);
plot(sigma1_range * 1e3, G_part1, 'b-', 'LineWidth', 1.5);
xlabel('电导率 \sigma_1 (mS/m)');
ylabel('电导 \itG (\muS)');
title('电导随电导率\sigma_1变化 (\sigma_2=0.1 S/m)');
grid on;

% 图3: 电导随两种电导率变化 (情况2)
subplot(2, 2, 3);
[X, Y] = meshgrid(sigma2_v2 * 1e3, sigma1_v2 * 1e3);
surf(X, Y, G_part2);
xlabel('电导率 \sigma_2 (mS/m)');
ylabel('电导率 \sigma_1 (mS/m)');
zlabel('电导 \itG (\muS)');
title('电导随两种电导率变化');
view(45, 30);
grid on;

% 图4: 电场强度分布示意图
subplot(2, 2, 4);
% 简化模型：平行板电场分布
x = 0:0.01:1;
region1 = x <= 0.33;
region2 = (x > 0.33) & (x <= 0.67);
region3 = x > 0.67;

E_dist = zeros(size(x));
E_dist(region1) = E1;
E_dist(region2) = E2;
E_dist(region3) = E1;

% 使用条形图
bar(x, E_dist, 1, 'EdgeColor', 'k');
xlabel('位置 x (归一化)');
ylabel('电场强度 \itE (V/m)');
title('电场强度分布 (ε_{r1}=ε_{r2}=1)');
% 添加区域标注
text(0.16, E1*1.1, '介质1', 'HorizontalAlignment', 'center', 'FontSize', 9);
text(0.5, E2*1.1, '介质2', 'HorizontalAlignment', 'center', 'FontSize', 9);
text(0.84, E1*1.1, '介质1', 'HorizontalAlignment', 'center', 'FontSize', 9);
grid on;
ylim([0, max(E1, E2)*1.3]);

%% 保存数据到工作空间
save('exp1_data.mat', 'er1_range', 'er2_range', 'C_part1', 'C_part2', ...
    'sigma1_range', 'sigma2_v2', 'G_part1', 'G_part2', 'E1', 'E2');

fprintf('\n========== 计算完成 ==========\n');
fprintf('数据已保存到 exp1_data.mat\n');
fprintf('图片已生成\n');