# Agent 音频转谱开发

[English](README.md) | [简体中文](README.zh-CN.md)

本目录记录音频输入扩展。识谱由调用方 Agent 完成；CLI/MCP 软件适配器负责
写入和编辑音乐，不调用软件自带的音频转 MIDI 功能识谱。

当前阶段实现音频解码与准备、来源时间关联、频谱证据、音符事件记录和可复现评分。
尚未实现音频自动生成 MSCZ、MusicXML、PDF、多轨 MIDI 和 DAW 工程的完整交付。

## 复现第一批测量

```bash
python -m pip install -e '.[audio]'
python scripts/make_audio_benchmark.py --output work/controls --seed SEED
# 安装 MuseScore 和 ffmpeg 后，可生成采样音色测试：
python scripts/make_audio_benchmark.py --output work/sampled --seed SEED --musescore /path/to/mscore
scorebridge prepare-audio work/sampled/inputs/polyphonic.wav --output work/evidence
# 使用未知音符时长与休止的对照样例：
python scripts/make_audio_benchmark.py --output work/irregular --seed SEED --irregular-melody
```

Agent 只读取 `inputs/` 和准备后的证据，先保存识别记录，再用 `evaluate-audio`
与独立保存的 `answers/` 比较。查看答案后不修改识别记录。生成器创建原创的四小节
短片段；合成对照音不能证明乐器识别。采样测试由 MuseScore 渲染声音，不由它识谱。
仓库不包含第三方专有采样或版权乐曲。

[validation.json](validation.json) 保存首次判断、参考事件、随机种子、识别记录哈希和
测量结果。这是开发自测：同一个 Agent 已知生成方法及节奏模板，但写下判断前未读取
随机音高答案。鼓模板已知，匹配结果不证明独立鼓类识别。乐器推断、任意速度与拍号、
自由演奏、真实录音和密集管弦乐尚未通过此评测。短样例分数不是产品整体准确率。

| 来源 | 匹配的有音高事件 / 参考事件 |
| --- | --- |
| 合成单旋律 | 12 / 12 |
| 合成和弦 | 24 / 24 |
| 合成混音 | 25 / 32 |
| 采样单旋律 | 12 / 12 |
| 采样钢琴和弦 | 23 / 24 |
| 采样钢琴、低音和鼓混音 | 25 / 32 |
| 随机休止与时长的合成单旋律 | 10 / 10 |

不规则对照样例的音高和时序在读取答案前从图像识别，仍属于同 Agent 合成自测。
另一次 MuseScore 扩展执行将采样单旋律的识别记录保存成 MSCZ，回读的 12 个音高
与冻结的 Agent 记录一致。长笛音色模板来自测试设置，不代表独立乐器推断已通过。

## 固定开发里程碑

1. Agent 音频证据与事件识别测量（本阶段）。
2. 统一音乐计划：来源时间、演奏时间、记谱、乐器、打击乐及书面音高与实际音高关系。
3. 同一计划输出 MSCZ、MusicXML、PDF 和多轨 MIDI。
4. 首个 DAW 适配器：可编辑音符轨道、实际音源配置、原生工程保存。
5. CLI/MCP/Skill 共用流程、准确定位目标工程、恢复执行。
6. 干净安装验收、代表性音频测试、同步双语文档。

新增软件适配器属于后续版本，不临近交付扩大本次验收范围。下一批识别测试要使用
未知节奏、休止、重叠声部与鼓型，不能拿本次已知模板结果证明这些能力。
