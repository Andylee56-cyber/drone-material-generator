"""
Streamlit性能优化建议
在streamlit_app.py中添加这些优化
"""

# 1. 使用模型缓存（避免重复加载）
import streamlit as st

@st.cache_resource  # 这个装饰器会缓存模型，只加载一次
def load_model():
    """加载模型，只执行一次"""
    # 你的模型加载代码
    # model = torch.load('model.pth')
    return model

# 2. 限制批处理大小
BATCH_SIZE = 1  # 减少批处理大小，降低内存占用

# 3. 使用CPU优化（如果没有GPU）
import torch
if not torch.cuda.is_available():
    torch.set_num_threads(1)  # 限制CPU线程数，避免过载

# 4. 及时释放内存
import gc
# 在处理完一批数据后
gc.collect()

# 5. 使用更小的数据类型
# 如果可能，使用float16而不是float32
# model = model.half()  # 减少一半内存占用

