# 第二周：CNN、数据增强与实验对比

本项目在第一周 Fashion-MNIST 基线上继续实验，比较 MLP、普通 CNN 和带数据增强的 CNN。代码会保存训练曲线、测试集混淆矩阵、正确/错误预测样例和每个类别的召回率。

## 快速开始

```powershell
python -m venv .venv
python -m pip --python .\.venv\Scripts\python.exe install -r requirements.txt --timeout 120
.\.venv\Scripts\python.exe -m scripts.run_comparison --epochs 3
```

首次运行会下载数据。想先快速检查代码，可加 `--limit-train 4000`。单独运行一个实验：

```powershell
.\.venv\Scripts\python.exe -m src.train --model cnn --augment --epochs 3
```

## 实验设计

| 实验 | 模型 | 增强 | 用途 |
| --- | --- | --- | --- |
| `mlp` | 展平像素的 MLP | 无 | 第一周基线 |
| `cnn` | BatchNorm CNN | 无 | 测量卷积结构的收益 |
| `cnn_aug` | BatchNorm CNN | 随机平移、水平翻转、权重衰减 | 观察泛化与过拟合 |

`outputs/<实验名>/metrics.json` 保存配置、曲线、测试准确率和按类别召回率；`figures/confusion_matrix.png` 用来观察哪些类别仍然容易混淆。

## 项目结构

```text
ai-learning-week2-cnn-augmentation/
├─ src/                 # 数据、模型和训练入口
├─ scripts/run_comparison.py
├─ outputs/             # 运行后生成，不提交大文件
├─ blog/                # 博客副本
└─ requirements.txt
```

## 本周要回答的问题

1. CNN 的局部感受野和池化是否比直接 Flatten 更适合图片？
2. 数据增强如何改变训练准确率与验证准确率之间的差距？
3. 只看总体准确率时，是否会忽略某些类别的系统性错误？
