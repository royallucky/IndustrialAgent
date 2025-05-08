import pandas as pd
import random
import uuid

# 定义表头
headers = ["ID", "检测点", "采集周期(ms)", "数据准确率(%)", "缺陷检出率(%)", "硬件成本占预算(%)"]

# 生成数据
data = []
for _ in range(10000):
    row = [
        str(uuid.uuid4()),                  # 唯一ID
        f"Point-{random.randint(1, 100)}",  # 检测点
        random.randint(100, 1000),          # 采集周期
        round(random.uniform(80, 100), 2),  # 数据准确率
        round(random.uniform(70, 99), 2),   # 缺陷检出率
        round(random.uniform(5, 20), 2)     # 硬件成本占预算
    ]
    data.append(row)

# 转为 DataFrame
df = pd.DataFrame(data, columns=headers)

# 查看前几行
print(df.head())

# 保存为 CSV（如果需要）
df.to_csv("test_data.csv", index=False)
