# ScoreBridge

[English](README.md) | [简体中文](README.zh-CN.md)

由 Agent 主导的识谱与 MuseScore 操作工具。调用工具的 Agent 阅读
PDF/PNG/JPG/TIFF/WebP 原谱，整理音乐内容，通过制谱工具生成可编辑、
可播放的 **MSCZ**。Audiveris 是可选的辅助工具。

## 默认工作流

```text
PDF / 图片 → 源文件准备 → Agent 识谱
→ 内部乐谱 / 命令计划 → MuseScore 制谱 → MSCZ
```

Agent 阅读原谱并提供施工计划。ScoreBridge 通过 MuseScore 官方的
`--extension` 接口执行计划，保存原生 MSCZ。
参见[命令详情与支持的记谱内容](skills/scorebridge/references/editor-plan.md)。

## 创建乐谱

Agent 识谱后，提供乐谱基本信息和制谱步骤：

```bash
.venv/bin/scorebridge build-score examples/native-plan.json --output my-score.mscz
```

对应的 MCP 工具：`musescore_build_score(specification, steps, output_path)`。
后续修改时，将返回的准确目标信息放入计划，使用
`musescore_apply_plan` 或 `scorebridge apply-plan PLAN.json --input SCORE.mscz`。
扩展在临时副本上执行，并在 MSCZ 中写入本次运行的执行记录。
失败或目标不匹配的批次不会替换源文件或已有输出。
执行成功后，交付一个原生 MSCZ 文件。

文件后端已在 **macOS / MuseScore Studio 4.7.4** 上验证。
已提供 Linux 和 Windows 的扩展路径，但尚未完成这些平台的实际软件验收。
可以用 `SCOREBRIDGE_EXTENSION_DIR` 指定扩展安装路径。
MuseScore 需要支持 `--extension`。Sibelius/Cubase 适配器属于后续版本。

## 安装

```bash
git clone https://github.com/achou666666-code/ScoreBridge.git
cd ScoreBridge
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[mcp,image,websocket,test]'
.venv/bin/scorebridge doctor
```

单独安装 MuseScore。`doctor` 检查依赖；默认扩展流程不需要 WebSocket
监听服务。`editor-status` 检查可选的实时插件。Audiveris 为可选依赖，
未安装它不会导致环境检查失败。将 `skills/scorebridge` 技能目录安装到
Agent 的技能目录，并使用虚拟环境的 Python 可执行文件以及
`mcp_server/server.py` 的绝对路径配置 MCP 服务：

```bash
.venv/bin/python mcp_server/server.py
```

## 可选的 WebSocket 实时编辑

以下配置仅适用于已经打开的交互式乐谱，`build-score` 和 `apply-plan`
不需要这些操作。`editor-connect` 检查监听服务，不操作屏幕；
需要实时编辑时，在 MuseScore 中启用一次插件。

兼容的 MuseScore QML 插件位于 `plugins/`。macOS 上的安装命令：

```bash
bash scripts/install_musescore_plugin.sh
```

在 MuseScore 中打开乐谱，选择 `Plugins > MuseScore API Server`
（旧版本重新加载后可能显示文件名 `musescore-mcp-websocket`）。
ScoreBridge 发送编辑命令期间，保持插件运行。
使用 `.venv/bin/scorebridge editor-status` 检查实时连接。

ScoreBridge 包含兼容的 MuseScore 编辑插件和 WebSocket 客户端。
其他实现，例如 [mcp-score](https://github.com/tskovlund/mcp-score) 和
[mcp-musescore](https://github.com/ghchen99/mcp-musescore)，使用不同的
命令集和通信格式。实时编辑需要运行仓库附带的插件。
用 `SCOREBRIDGE_MUSESCORE_WS` 设置自定义地址，默认是 `ws://localhost:8765`。
协议检测使用只读 ping；`SCOREBRIDGE_MUSESCORE_PROTOCOL` 可以强制选择
`action` 或 `command`。写入操作超时后不会自动重试。
`scorebridge editor-status` 读取插件声明的命令列表，不修改乐谱。
更新插件后重启 MuseScore，重新加载 QML。
状态响应区分已验证的 `commands` 和在 MuseScore 4.7.4 上暂不可用的
`reserved_commands`。
播放静音和任意音频资源分配命令仍被保留，尚不可用。
`setStaffVisible` 控制谱面可见性，不代表播放静音。
插件 2.5 增加了用于诊断的 `getMidiChannels`，以及
`setPartInstrument({part: 0, instrumentId: "flute"})`，可以用标准 MuseScore
乐器模板替换声部，同时更新默认记谱设置和播放音色。
直接改变 MIDI program 不能视作完成音色分配：MuseScore 4 在修改 MIDI
program 后可能仍使用原来的音频资源。

实时桥接用于编辑并保存已经打开的乐谱。ScoreBridge 通过已测试的 CLI
适配器创建初始 MSCZ。调用 `musescore_create_score`，传入标题、小节数、
拍号和声部；它创建内部 MusicXML 框架，转换为经过验证的 MSCZ，
也可以打开文件以进行实时 MCP 编辑。任意 MuseSound/VST 资源选择尚未实现。
QML 中的生命周期命令名仍被保留；调用时明确返回不支持的结果。

`musescore_open` 用于打开已有 MSCZ 或 MusicXML 文件。
它启动 MuseScore 并返回进程 ID；Agent 应等待
`musescore_websocket_status` 确认插件连接后再发送编辑命令。
对应 CLI 是 `scorebridge create-score SPEC --output
SCORE.mscz --open` 和 `scorebridge open-score INPUT`。

每个新创建的乐谱框架都有内部 `scorebridgeTargetId`。
创建结果中的 `target` 对象包含该 ID、乐谱名称、标题、小节数和谱表数。
将这个对象原样复制到后续命令计划中。
`musescore_execute_plan` 在首次写入前读取实时乐谱身份；任何字段不一致，
都会返回 `wrong_target`，不发送编辑命令。
绑定已有编辑器时，调用 `musescore_bind_score(input_path, target)`，或：

```bash
scorebridge bind-score score.mscz --target create-result.json
```

macOS 上仅在监听服务已经对应目标乐谱时复用连接；否则返回 `wrong_target`，
不会打开或编辑文件。没有监听服务时，返回 `needs_live_plugin`，
不会点击菜单或启动未绑定的编辑器；此时使用默认文件后端。
仅在插件回读的目标身份完全一致时，才报告 `bound`。
进程 ID、窗口标题或文件打开请求成功，均不能单独证明绑定成功。
导出或修改播放设置前，对内部乐谱计划调用 `score_instrument_audit`。
它报告未解析的乐器 ID，并检测意外回退为钢琴的情况；声部名称本身
不能证明播放音色正确。
插件 2.1 支持单独调用 `addDynamic`、`addTechniqueText`，也支持在
`processSequence` 中使用。MuseScore 4.7.4 的实时批次已验证范围选择、
标准 `mp` 力度、谱表文字，以及保存为 MSCZ。
力度标记包含控制播放的语义数值和谱面符号。
演奏法文字保留原谱指示，但文字本身不会切换拨弦、弱音等播放技法。

插件 2.2 支持批量添加 `addArticulation`（跳音、强音、保持音）和 `addSlur`。
先选择一个明确的谱表范围；奏法标记需要音符，圆滑线需要同一声部内
至少两个和弦位置。实时测试验证了保存的符号、圆滑线端点，
以及修改不会影响其他谱表。
奏法操作会切换已有标记，不能盲目重复执行批次。
跨谱表和跨声部圆滑线不在该命令的支持范围内。

插件 2.3 增加 `setKeySignature({staff: 1, measure: 2, fifths: -1})`。
按原谱的书面调号设置：负数表示降号个数，正数表示升号个数，零表示无升降号。
谱表索引从零开始，小节编号从一开始。
插件根据乐器移调关系推导实音调号并写入两者，不改变音符音高。
它在小节起点修改一个谱表的调号，替换已有调号；设置相同时跳过。
需要启用书面音高显示。支持七个降号到七个升号的标准调号，
不支持自定义微分音调号。

插件 2.4 增加 `getPageLayout`、`setPageLayout` 和 `setLayoutBreak`。
页面尺寸和边距以毫米为单位；奇偶页使用相同的左、上、下边距。
用 `setLayoutBreak({measure: 4, type: "line"})` 在指定小节之后换行，
小节编号从一开始；`page` 表示换页，`none` 表示移除布局断点。
保留已有分节符，重复设置相同断点不会累积。
这些是 Agent 的布局控制工具，不会自动匹配原谱排版。

插件 2.5 增加 `setPartInstrument`。声部索引从零开始，
使用真实 MuseScore 乐器 ID，例如 `flute`、`oboe`、`bb-clarinet`、`horn`
或 `piano`。命令验证实际生成的乐器 ID 后才报告成功；相同设置会跳过。
实时验证将长笛替换为双簧管，生成了不同的音频；恢复长笛后，
生成的 WAV 与原 WAV 逐字节一致。这验证了标准模板的播放音色分配，
不代表支持任意 MuseSounds、VST 或 SoundFont 的选择。

插件 2.6 增加精确定位的 `addChord` 和 `addTie`。
`addChord` 接受从零开始的谱表和声部索引、绝对 tick、以全音符为单位的
时值分数、MIDI 音高，以及可选的书面 TPC 值。
支持单音、和弦、附点时值以及空的次要声部。
`addTie` 将同一谱表、同一声部中的某个音高连接到紧接着的和弦，
拒绝不匹配的目标。实时验证保存了两个书面 TPC 准确的附点四分音符三和弦、
C 到 C 的延音线，以及独立的第二声部音符；其他四个谱表保持不变。

插件 2.7 使 `addRest` 和 `addTuplet` 支持精确定位。
两者都接受明确的谱表、声部、绝对 tick 和以全音符为单位的时值。
`addRest` 验证生成的休止符，支持空的次要声部。
`addTuplet` 还接受明确的比例，例如 3:2，验证生成的连音比例，
并报告实际总时值。MuseScore 4.7.4 实时验证在第三声部保存了四分休止符，
在第四声部保存了总时值为四分音符的八分音符三连音。

插件 2.8 增加精确定位的 `addGraceNote`。
按谱表、声部和绝对 tick 定位主音符，创建带有 MuseScore 语义的装饰音和弦，
再设置并回读其 MIDI 音高、可选书面 TPC、位置和音符类型。
支持 MuseScore 提供的全部八种前置、后置装饰音类型。
MuseScore 4.7.4 实时验证保存了全部八种 XML 标签并渲染了乐谱。
实际验证范围见 `tests/LIVE_EDITOR_RESULTS.md`。

插件 2.9 增加只读命令 `getScoreIdentity`，返回乐谱框架的内部目标 ID、
当前名称、标题、小节数和谱表数，用于写入前的绑定检查。
它不会根据可见文件名推测乐谱身份。

## Agent 入口

通过 MCP 调用 `score_transcribe(input_path, output_dir)`，或：

```bash
scorebridge prepare INPUT --output WORKDIR
```

这一步准备与源文件关联的页面，并返回 `awaiting_agent`。
随后由**调用工具的多模态 Agent** 阅读图片；程序不会暗中执行 OMR
或调用第二个模型。工作目录保留原图、渲染图、增强图及其页码映射。
文件名排序只是辅助；Agent 检查实际页序，并识别非乐谱页面。

Agent 将确定的乐谱基本信息和制谱步骤记录在一个计划中：

```bash
scorebridge build-score PLAN.json --output score.mscz
```

`examples/native-plan.json` 用原创演示音乐展示 `score` 和 `steps` 字段。
对应的 MCP 工具是 `musescore_build_score(specification, steps, output_path)`。
一次调用即可创建原生乐谱、执行 Agent 的制谱步骤并检查执行结果。
执行计划前需要安装 MuseScore。

后续修改时，将返回的 `target` 原样保留在编辑计划中：

```bash
scorebridge apply-plan EDITS.json --input score.mscz
```

对应的 MCP 工具是 `musescore_apply_plan(plan_path, input_path)`。
每个步骤都有唯一 ID。批次在临时副本上执行，
只有目标匹配且执行记录完整时才交付 MSCZ。
失败后修正所报告的步骤并重新提交；原来的文件保留。
`pass` 说明所提供的计划已执行，不代表测得了原谱识别准确率。

`musescore_execute_plan` 和 `musescore_websocket_command` 仍可用于
[可选的实时后端](#可选的-websocket-实时编辑)，默认流程不需要它们。

## MSCZ 交付

`score_finalize` 仍适用于旧版 Score IR 能表达的乐谱。
它生成内部 MusicXML，通过 MuseScore 创建 MSCZ，并将临时 XML 和结构检查
保存在 `.scorebridge/` 下。默认不再导出 MIDI 或 PDF。
MSCZ 导出失败返回 `error`，重新打开转换失败返回 `incomplete`。
这类检查不证明与原谱一致或实际听到的音色正确。

旧版 IR 无法表达全部记谱内容。不能为了让编译通过，
悄悄丢弃尚不支持的歌词、连线、奏法或演奏语义。
使用已支持的原生命令，或扩展编辑适配器；缺少的命令必须明确报告。

## 可选 OMR 与开发工具

仅在选择旧版 Audiveris → MusicXML → Score IR → 复核流程时使用
`score_transcribe(..., mode="omr")`。`omr_run`、`review_create` 和
`review_apply` 仍保留，供该可选流程使用。
Agent 主导的任务不需要第二次识谱或人工逐小节复核。

`score_validate`、`score_compile`、`score_apply_patch`、`score_inspect`、
`score_build_mscz` 和 `musescore_convert` 是底层开发工具；
它们生成的中间文件不是默认交付给用户的文件。

## 测试

```bash
.venv/bin/pytest -q
```

检查另一台电脑从 Git 获取的项目是否可用：

```bash
python3 scripts/check_clean_install.py
```

脚本将 HEAD 导出到临时目录，创建新的虚拟环境，安装软件包及测试依赖，
然后使用已安装的软件包运行导出的测试。
它排除未提交的源代码修改和已有的可编辑安装。
安装依赖需要联网；QML JavaScript 测试需要 Node.js。
GitHub Actions 在推送和提交 PR 时运行这项检查。
仅存在于本地的管弦乐验证材料缺失时，相应测试会跳过；
真实 MuseScore 应用和听音测试与安装检查分开进行。

测试包含用于两种通信格式的本地 WebSocket 服务、嵌套插件错误、
部分计划失败后避免重复执行、无需 OMR 的输入准备，以及编译检查。
这些协议测试与实际 MuseScore 编辑和听音测试不同。

## 演示

`demos/image-to-score/` 用于小型图片转可编辑乐谱演示。
`demos/pirates/` 用于后续多页管弦乐案例、截图和验证报告。
公开的 Twinkle 测试结果位于 `demos/image-to-score/output/twinkle-run/`，
包含源文件关联材料、Audiveris MusicXML、Score IR 和 MuseScore 往返转换文件。
视频录制完成后再加入仓库；原始 PDF 及其他受版权保护的材料不放入公开仓库。

## 首版验收与后续工作

首版验收包括实际 MCP 执行、特殊记谱、打击乐、管弦乐前五小节回归，
以及干净安装检查。参见[固定验收清单](DELIVERY.md)和
[实际运行验证记录](tests/LIVE_EDITOR_RESULTS.md)。

后续工作包括双音震音、跨谱表圆滑线、播放技法切换、
Windows/Linux 的实际软件验收，以及 Sibelius/Cubase 适配器。

## 文档更新

在同一次修改中更新两种语言版本。功能、安装步骤、命令、示例、
验证结果和支持范围应保持一致。
