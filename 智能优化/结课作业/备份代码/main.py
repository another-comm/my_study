import torch
import numpy as np
import time
from torch.cuda.amp import autocast, GradScaler
from config import CFG
from models import vector_to_model, get_model_size
from optimizers import StandardPSO, EntropyPSO
from problems import BrachistochroneProblem
from physics import PhysicsEngine

def get_optimizer_instance(algo_type, dim):
    if algo_type == 'PSO':
        return StandardPSO(dim, CFG.NUM_PARTICLES, CFG.MAX_ITER)
    elif algo_type == 'EntropyPSO':
        return EntropyPSO(dim, CFG.NUM_PARTICLES, CFG.MAX_ITER)
    else:
        raise ValueError(f"Unknown algo: {algo_type}")

def run_hybrid_optimization():
    print("=" * 60)
    print("复杂力场约束下的机器人时间最优轨迹规划")
    print("Time-Optimal Trajectory Planning under Complex Field Constraints")
    print("=" * 60)
    print(f"🌟 当前任务: {CFG.PROBLEM_TYPE}")
    print(f"📊 模型类型: {CFG.MODEL_TYPE}")
    print(f"⚙️  物理参数: μ={CFG.MU}, 阻力={CFG.DRAG_COEFF}, 向心力={CFG.ENABLE_CENTRIFUGAL}")
    
    # 1. 实例化问题
    if CFG.PROBLEM_TYPE == 'Brachistochrone':
        problem = BrachistochroneProblem()
    else:
        raise ValueError("Unknown Problem Type")
        
    model = problem.get_model().to(CFG.DEVICE)
    # 确保模型参数需要梯度（get_loss 方法需要计算梯度）
    for param in model.parameters():
        param.requires_grad = True
    dim = get_model_size(model)
    
    print(f"🧬 基因维度: {dim}")
    print(f"🚀 [Phase 1] 全局探索 (Global Exploration) - {CFG.ALGO_TYPE}...")
    
    # === Phase 1: PSO 全局搜索 ===
    optimizer = get_optimizer_instance(CFG.ALGO_TYPE, dim)
    history = []
    
    start_time = time.time()
    
    for it in range(CFG.MAX_ITER):
        scores = []
        # 粒子群评估（批量，留梯度，减少 host<->device 往返）
        for start in range(0, CFG.NUM_PARTICLES, CFG.BATCH_PARTICLES):
            end = min(CFG.NUM_PARTICLES, start + CFG.BATCH_PARTICLES)
            for i in range(start, end):
                vector_to_model(optimizer.particles[i], model)
                loss = problem.get_loss(model)
                scores.append(loss.detach())
            
        scores_t = torch.stack(scores)
        optimizer.update_pbest(scores_t)
        optimizer.step(it)
        
        history.append(optimizer.gbest_score)
        
        if it % 10 == 0:
            print(f"  PSO Gen {it:3d} | Best Loss: {optimizer.gbest_score:.6f}")

    print(f"✅ Phase 1 完成. 最佳损失: {optimizer.gbest_score:.6f}")
    
    # === Phase 2: Gradient Descent 局部精调 ===
    if CFG.ENABLE_HYBRID:
        print(f"🔧 [Phase 2] 局部开发 (Local Exploitation) - Adam优化器, {CFG.GRAD_STEPS} 步...")
        
        # 加载 PSO 找到的最佳权重
        best_vec = optimizer.gbest_pos
        vector_to_model(best_vec, model)
        
        # 开启梯度优化
        grad_optim = torch.optim.Adam(model.parameters(), lr=CFG.LEARNING_RATE)
        scaler = GradScaler(enabled=(CFG.DEVICE.type == "cuda" and CFG.ENABLE_AMP))
        
        for step in range(CFG.GRAD_STEPS):
            grad_optim.zero_grad()
            
            with autocast(enabled=(CFG.DEVICE.type == "cuda" and CFG.ENABLE_AMP)):
                loss = problem.get_loss(model)
            scaler.scale(loss).backward()
            scaler.step(grad_optim)
            scaler.update()
            
            current_loss = loss.item()
            history.append(current_loss)
            
            if step % 20 == 0:
                print(f"  Grad Step {step:3d} | Loss: {current_loss:.6f}")
                
        print(f"✅ 混合优化完成. 最终损失: {history[-1]:.6f}")
    
    total_time = time.time() - start_time
    print(f"⏱️  总耗时: {total_time:.2f}s")
    
    # === 可视化 ===
    print("📈 生成可视化结果...")
    problem.visualize(model, history)

    # === 最终指标输出 ===
    # 确保模型参数需要梯度（如果启用了混合优化）
    if CFG.ENABLE_HYBRID:
        for param in model.parameters():
            param.requires_grad = True
    # 训练使用带惩罚的损失，最终报告物理时间（不含惩罚）
    final_metric = PhysicsEngine.evaluate_time_physical(model).detach().item()
    if CFG.PROBLEM_TYPE == 'Brachistochrone':
        print("=" * 60)
        print(f"🏁 最速曲线最短时间: {final_metric:.6f} s")
        print("=" * 60)
    else:
        print(f"🏁 最终指标: {final_metric:.6f}")

if __name__ == "__main__":
    run_hybrid_optimization()