# 安装步骤
1. 创建3.8-3.9版本的python虚拟环境
2. 安装依赖
```shell
pip install -r .\requirements.txt
```
3. 在`datasets`目录创建`lol`(模型数据集名称)，再创建对应的`trainA/B`目录。
4. 将数据集复制到对应目录。

# 运行训练
- 训练模型
```shell
python -m visdom.server
python train.py --dataroot .\datasets\lol --name lol --model cycle_gan --num_threads 0
```
当虚拟内存足够时，可以尝试将`--num_threads 0`参数删除。