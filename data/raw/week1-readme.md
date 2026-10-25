# 第 1 周：Fashion-MNIST 图像分类

这是一个用 PyTorch 跑通完整训练流程的学习项目。默认模型是简单的多层感知机（MLP），也提供一个可选的小型 CNN。

## 安装与运行

```powershell
cd "C:\Users\wushe\Documents\ChatGPT\week 1\ai-learning-week1-fashion-mnist"
python -m venv .venv
python -m pip --python .\.venv\Scripts\python.exe install -r requirements.txt --timeout 120
.\.venv\Scripts\python.exe -m src.train
```

也可以运行 CNN：`python -m src.train --model cnn --epochs 3`。首次运行会下载 Fashion-MNIST。默认使用 3 个 epoch、batch size 128、固定随机种子 42，并自动选择 CUDA（若可用）或 CPU。

输出位于 `outputs/mlp/` 或 `outputs/cnn/`：`model_best.pt` 是验证集表现最好的模型，`metrics.json` 保存实际指标，`figures/training_curves.png` 是曲线，`predictions/correct.png` 和 `incorrect.png` 是测试样例。

本次已完成代码静态检查（`python -m compileall src scripts`），并已在项目虚拟环境安装 PyTorch 2.14.0+cpu、torchvision 0.29.0、matplotlib 3.11.2 和 numpy 2.5.3。默认数据地址连接被拒绝后，我从 Fashion-MNIST 官方仓库的 HTTPS raw 镜像下载了四个 gzip 文件，放入 `data/FashionMNIST/raw/`，随后完成了真实训练。

实际 MLP 结果（覆盖后的 10 epoch 实验）：CPU、batch size 128、Adam、学习率 0.001、随机种子 42；训练集 54,000、验证集 6,000、测试集 10,000。最佳 epoch 为 10，测试损失 `0.3347`，测试准确率 `0.8825`（88.25%）。第 10 个 epoch 验证准确率为 88.62%。默认命令仍使用 3 个 epoch，便于快速验证；需要复现博客结果请运行 `python -m src.train --model mlp --epochs 10`。

## 核心概念

- **Batch**：一次送进模型的一小组样本。把数据分成 batch 可以控制内存，并让一次参数更新使用多个样本的平均信息。
- **模型、损失函数、优化器**：模型把图片映射为 10 个类别的分数；损失函数衡量分数和真实标签差多远；优化器根据梯度调整模型参数。
- **`loss.backward()`**：沿着刚才的计算过程反向计算每个参数对损失的梯度，并把梯度存到参数的 `.grad` 中。
- **`optimizer.step()`**：使用这些梯度更新参数。下一批数据前要先 `zero_grad()`，避免梯度累积。
- **训练集、验证集、测试集**：训练集用于更新参数，验证集用于选择模型和调参，测试集只在最后评估一次，尽量估计模型对未见数据的表现。
- **训练准确率高不一定有用**：模型可能记住训练图片，验证集和测试集可以帮助检查泛化能力，因此需要同时观察验证/测试准确率和损失。

## 项目结构

```text
ai-learning-week1-fashion-mnist/
├─ README.md  requirements.txt  .gitignore
├─ notebooks/01_fashion_mnist.ipynb
├─ src/ (config.py, dataset.py, model.py, train.py, evaluate.py)
├─ scripts/run_experiment.py
├─ outputs/mlp/ (CNN 实验另存到 outputs/cnn/)
└─ blog/2026-09-18-fashion-mnist.md
```

## 本周建议阅读顺序

先读 `src/dataset.py`，再读 `src/model.py` 和 `src/train.py`，最后看 `src/evaluate.py` 与 `outputs/mlp/metrics.json`。

## 更多运行方式

可以直接指定虚拟环境中的 Python，PowerShell 执行策略和多版本 Python 不会影响命令调用。

```powershell
.\.venv\Scripts\python.exe scripts/run_experiment.py --model mlp --epochs 3
.\.venv\Scripts\python.exe -m src.train --model cnn --epochs 3
.\.venv\Scripts\python.exe -m src.evaluate --checkpoint outputs/mlp/model_best.pt
.\.venv\Scripts\python.exe -m jupyter notebook notebooks/01_fashion_mnist.ipynb
```

同一模型再次训练会覆盖该模型目录下的旧结果；需要比较配置时，先复制保存旧目录。

## 数据和张量形状

官方训练集 60,000 张按固定种子分为 54,000 张训练、6,000 张验证；官方测试集 10,000 张独立保留。Dataset 返回一张图片及类别编号，DataLoader 把它们组成 batch。像素先从 0–255 转为 0–1，再使用固定参数缩放到 -1–1。验证集和测试集沿用同一组参数。

一个 batch 的图片形状是 `[128, 1, 28, 28]`，依次表示样本数、通道、高和宽；最后一批可能不足 128 张。MLP 将图片展平为 `[128, 784]`，输出 `[128, 10]` 的 logits。标签是 `[128]` 的整数。交叉熵直接接收 logits，无需先做 softmax；`argmax(1)` 选择最高分的类别。

模型是否学到了东西，要一起看损失是否下降、验证表现是否优于未训练时，以及最终测试结果。训练统计在参数更新过程中采集，且启用了 dropout，验证统计在 epoch 结束、关闭 dropout 后计算，训练曲线和验证曲线的采集方式不同。随机种子能减少差异，但不同硬件和库版本可能产生轻微数值差异。



