# 4.0.1 导出格式修复

- 视频：H.264 Main Profile Level 4.1，`avc1` 标签
- 像素格式：8-bit `yuv420p`
- 帧率：固定 30 fps，时间基 30000
- 音频：AAC-LC，48 kHz，双声道，192 kbps
- 容器：MP4，`mp42` 主品牌，faststart
- 清除 DJI 原片 timecode 数据轨与源元数据，避免部分播放器误判
- 文件名未填写扩展名时自动添加 `.mp4`
- 完成提示前自动验证文件大小、H.264 编码与文件尾部可解码性

DJI 三源 4.5 秒兼容性样片已验证为 H.264 Main、yuv420p、30.0 fps、AAC 双声道，尾部校验通过。
