import pathlib
local_dir = pathlib.Path.home() / ".cache" / "rag_models" / "bge-reranker-v2-m3"
print("模型目录:", local_dir)
print("目录内文件:")
for f in local_dir.iterdir():
    print(" ", f.name, f.stat().st_size // 1024 // 1024, "MB")
from FlagEmbedding import FlagReranker
print("开始加载...")
m = FlagReranker(str(local_dir), use_fp16=False)
print("加载成功!")
