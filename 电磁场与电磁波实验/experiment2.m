%% 实验2：同轴线恒定磁场分布分析
clear; clc; close all;

fprintf('========== 实验2：同轴线恒定磁场分布分析 ==========\n\n');

%% 基础参数设置
I = 1;           % 电流 (A)
a = 0.375;       % 内导体半径 (mm) - 2a = 0.75mm
b = 3.625;       % 内导体到外导体内半径 (mm) - 2b = 7.25mm
c = 3.75;        % 外导体外半径 (mm) - 2c = 7.5mm
mu_r1 = 2;       % 介质1相对磁导率
mu_r2 = 1;       % 介质2相对磁导率

% 将单位转换为米
a_m = a * 1e-3;      % mm -> m
b_m = b * 1e-3;      % mm -> m
c_m = c * 1e-3;      % mm -> m

% 真空磁导率
mu0 = 4 * pi * 1e-7;  % H/m

fprintf('基本参数：\n');
fprintf('  电流 I = %.2f A\n', I);
fprintf('  内导体半径 a = %.3f mm\n', a);
fprintf('  外导体内半径 b = %.3f mm\n', b);
fprintf('  外导体 外半径 c = %.3f mm\n', c);
fprintf('  介质1相对磁导率 μ_r1 = %.2f\n', mu_r1);
fprintf('  介质2相对磁导率 μ_r2 = %.2f\n', mu_r2);

%% ==================== 磁场计算 ====================
fprintf('\n========== 磁场分布计算 ==========\n');

% 磁导率
mu1 = mu_r1 * mu0;
mu2 = mu_r2 * mu0;

% 定义半径范围
% 区域1: 0 <= rho <= a (内导体)
% 区域2: a <= rho <= b (介质1)
% 区域3: b <= rho <= c (介质2/外导体)
% 区域4: rho > c (同轴外部)

rho = linspace(0.001, 10, 1000) * 1e-3;  % 半径从0.001mm到10mm

% 各区域的磁场强度和磁感应强度
H = zeros(size(rho));
B = zeros(size(rho));

for i = 1:length(rho)
    r = rho(i);
    if r <= a_m
        % 区域1: 内导体 (假设均匀分布)
        H(i) = I * r / (2 * pi * a_m^2);
        B(i) = mu1 * H(i);
    elseif r <= b_m
        % 区域2: 介质1
        H(i) = I / (2 * pi * r);
        B(i) = mu1 * H(i);
    elseif r <= c_m
        % 区域3: 介质2
        H(i) = I / (2 * pi * r);
        B(i) = mu2 * H(i);
    else
        % 区域4: 同轴外部
        H(i) = NaN;
        B(i) = NaN;
    end
end

% 过滤掉NaN值用于绘图
valid_idx = ~isnan(H);
rho_plot = rho(valid_idx) * 1e3;  % 转换为mm
H_plot = H(valid_idx);
B_plot = B(valid_idx);

fprintf('\n磁场分布计算完成\n');

%% ==================== 外自感计算 ====================
fprintf('\n========== 外自感计算 ==========\n');

% 外自感公式 (单位长度)
% 对于同轴线，外自感主要取决于内外导体之间的磁场
L_external = (mu1 + mu2) / (4 * pi);  % 简化估算

% 更精确的计算：考虑介质分布
% 内导体产生的磁通
Phi_inner = (mu1 * I) / (2 * pi) * log(b_m / a_m);

% 外导体内部的磁通
Phi_outer = (mu2 * I) / (2 * pi) * log(c_m / b_m);

% 总外自感 (单位H/m)
L_total = (Phi_inner + Phi_outer) / I;

fprintf('内导体区域自感贡献: %.6e H/m\n', Phi_inner / I);
fprintf('外导体区域自感贡献: %.6e H/m\n', Phi_outer / I);
fprintf('单位长度总外自感: %.6e H/m\n', L_total);
fprintf('单位长度总外自感: %.4f uH/m\n', L_total * 1e6);

%% ==================== 磁导率变化对外自感的影响 ====================
fprintf('\n========== 磁导率变化分析 ==========\n');

% mu_r1 从 1 变化到 2 (与 mu_r2 趋于一致)
mu_r1_range = 1:0.1:2;
L_varying = zeros(size(mu_r1_range));

fprintf('\n情况: μ_r1 从 1 变化到 2, μ_r2 = 1\n');
for i = 1:length(mu_r1_range)
    mu_r1_i = mu_r1_range(i);
    mu1_i = mu_r1_i * mu0;
    
    Phi_inner_i = (mu1_i * I) / (2 * pi) * log(b_m / a_m);
    Phi_outer_i = (mu2 * I) / (2 * pi) * log(c_m / b_m);
    L_total_i = (Phi_inner_i + Phi_outer_i) / I;
    L_varying(i) = L_total_i * 1e6;  % 转换为 uH/m
end

fprintf('当 μ_r1 = 1 时, L = %.4f uH/m\n', L_varying(1));
fprintf('当 μ_r1 = 2 时, L = %.4f uH/m\n', L_varying(end));

%% ==================== 绘图 ====================
figure('Units', 'centimeters', 'Position', [5, 5, 16, 12]);

% 图1: 磁场强度随半径变化
subplot(2, 2, 1);
plot(rho_plot, H_plot * 1e-3, 'b-', 'LineWidth', 1.5);  % H转换为 kA/m
hold on;
% 标注区域
ymin = min(H_plot * 1e-3);
ymax = max(H_plot * 1e-3);
plot([a, a], [ymin, ymax], 'r--', 'LineWidth', 1);
plot([b, b], [ymin, ymax], 'g--', 'LineWidth', 1);
plot([c, c], [ymin, ymax], 'm--', 'LineWidth', 1);
xlabel('半径 \rho (mm)');
ylabel('磁场强度 \itH (kA/m)');
title('磁场强度 H 随半径 \rho 的变化');
legend('H(\rho)', '内导体边界', '介质1/2边界', '外导体边界', 'Location', 'best');
grid on;

% 图2: 磁感应强度随半径变化
subplot(2, 2, 2);
plot(rho_plot, B_plot * 1e3, 'b-', 'LineWidth', 1.5);  % B转换为 mT
hold on;
Bmin = min(B_plot * 1e3);
Bmax = max(B_plot * 1e3);
plot([a, a], [Bmin, Bmax], 'r--', 'LineWidth', 1);
plot([b, b], [Bmin, Bmax], 'g--', 'LineWidth', 1);
plot([c, c], [Bmin, Bmax], 'm--', 'LineWidth', 1);
xlabel('半径 \rho (mm)');
ylabel('磁感应强度 \itB (mT)');
title('磁感应强度 B 随半径 \rho 的变化');
legend('B(\rho)', '内导体边界', '介质1/2边界', '外导体边界', 'Location', 'best');
grid on;

% 图3: 外自感随mu_r1变化
subplot(2, 2, 3);
plot(mu_r1_range, L_varying, 'b-o', 'LineWidth', 1.5);
xlabel('相对磁导率 \mu_{r1}');
ylabel('外自感 \itL (\muH/m)');
title('外自感随磁导率\mu_{r1}的变化 (\mu_{r2}=1)');
grid on;

% 图4: 同轴线结构示意图
subplot(2, 2, 4);
theta = linspace(0, 2*pi, 100);

% 绘制同心圆
r_inner = a * 1000;  % mm
r_mid1 = b * 1000;   % mm
r_mid2 = c * 1000;   % mm

% 只绘制四分之一圆
theta_half = linspace(0, pi, 50);

% 填充区域
fill(r_inner * cos(theta_half), r_inner * sin(theta_half), [0.8, 0.8, 0.8], 'EdgeColor', 'k', 'LineWidth', 1.5);
hold on;
fill([r_inner * cos(theta_half), fliplr(r_mid1 * cos(theta_half))], ...
     [r_inner * sin(theta_half), fliplr(r_mid1 * sin(theta_half))], [0.6, 0.8, 1], 'EdgeColor', 'k', 'LineWidth', 1.5);
fill([r_mid1 * cos(theta_half), fliplr(r_mid2 * cos(theta_half))], ...
     [r_mid1 * sin(theta_half), fliplr(r_mid2 * sin(theta_half))], [1, 0.8, 0.6], 'EdgeColor', 'k', 'LineWidth', 1.5);

% 标注
text(r_inner/2, 0.2, '内导体', 'FontSize', 10);
text((r_inner + r_mid1)/2, 0.5, '介质1', 'FontSize', 10);
text((r_mid1 + r_mid2)/2, 0.3, '介质2', 'FontSize', 10);
text(r_mid2 + 0.3, 0.2, '外导体', 'FontSize', 10);

% 绘制半径标注线
plot([0, r_mid2], [0, 0], 'k-', 'LineWidth', 1);
plot([a*1000, a*1000], [-0.3, 0.3], 'r--', 'LineWidth', 1);
plot([b*1000, b*1000], [-0.3, 0.3], 'g--', 'LineWidth', 1);
plot([c*1000, c*1000], [-0.3, 0.3], 'm--', 'LineWidth', 1);

% 标注半径值
text(a*1000, -0.5, 'a', 'HorizontalAlignment', 'center', 'FontSize', 10);
text(b*1000, -0.5, 'b', 'HorizontalAlignment', 'center', 'FontSize', 10);
text(c*1000, -0.5, 'c', 'HorizontalAlignment', 'center', 'FontSize', 10);

axis equal;
axis off;
title('同轴线结构示意图');
xlim([-0.5, 5]);

%% 保存数据
save('exp2_data.mat', 'rho', 'H', 'B', 'mu_r1_range', 'L_varying', 'L_total');

fprintf('\n========== 计算完成 ==========\n');
fprintf('数据已保存到 exp2_data.mat\n');
fprintf('图片已生成\n');