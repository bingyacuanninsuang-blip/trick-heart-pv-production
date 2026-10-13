# 复用与恢复边界

## 可独立使用的工具

```bash
python tools/validate_bundle.py
python -m pip install -r requirements.txt
python tools/export_video.py --frames PATH_TO_PNGS --audio PATH_TO_AUDIO --output output.mp4 --fps 24 --count 3768 --ffmpeg PATH_TO_FFMPEG
```

validate_bundle.py 只依赖 Python 标准库，用清单验证资料完整性。export_video.py 读取从 00000.png 开始的连续图像，先编码视频，再独立复制完整音轨，验证完整解码帧数及音轨压缩数据哈希。输出路径已存在时拒绝覆盖。

输入必须是已授权的媒体。帧率和帧数由本片设定传入，下一片应使用自己的真实规格。FFmpeg 需支持 libx264 和输入音轨在 MP4 中的封装。Windows 字体需自行配置；仓库不分发系统字体。

## 历史实现快照

history/original-tools 和 history/revisions 保留具体算法、镜头表、注册坐标和修订入口。它们经过本机路径脱敏，**不是已迁移的一键执行工程**。

要在另一环境重建完整 v11，还需要原片、完整原音轨、相应 v6–v10 无损基准帧，以及统一后的输入/资产路径与字体。先迁移路径、确认每个导入的读写目录，再依次生成受影响帧。不能用有损 MP4 解出的帧冒充历史逐字节相同的 PNG 基准。

本库的最终成片哈希和验证记录可用于比对保留的交付视频。生成模型、字体版本或编码器改变都会影响输出；再生成图片不会自动复现原稿。

## 素材重新生成

引用姿态参考时写明其只负责构图、朝向、手腕和道具接触；造型参考负责身份、服装、发型和配色。每次生成记录参考角色、目标镜头、完整提示词、采用状态、注册框与资产哈希。完整提示词无法取得时，只能标注为重建 brief。
