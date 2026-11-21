# 安装与验证方法（conductor-sync 本器官方法）

## 1. 为什么是"复制"而不是链接

- Windows 默认无符号链接权限；全局安装（`~/.workbuddy/skills/`）采用**整树复制**，两份独立。
- 项目 `skills/` 是**唯一真相源**：所有修改只落在项目内，改完跑 `sync-global.py` 推到全局。
- 全局副本只服务运行时加载；禁止直接改全局文件（会被下次同步覆盖或造成漂移）。

## 2. 同步规则

| 场景 | 命令 | 行为 |
|---|---|---|
| 日常更新 | `python ../scripts/sync-global.py` | 同步 conductor 家族（conductor + 全部 conductor-*） |
| 全量安装 | `python ../scripts/sync-global.py --all` | 同步 skills/ 下全部 skill（含协作 skill） |
| 只看差异 | 加 `--dry-run` | 列出将复制/多余的文件，不实际复制 |

- **增量复制**：内容一致（字节级比较）的文件跳过，只复制有差异的。
- **stale 文件**：全局存在但源已删除的文件**不会自动删除**——先逐个人工确认（可能是别的入口还在用），确认后手动删除。
- 首次安装 = 同步行为本身（目录不存在会自动创建）。

## 3. 三道完整性测试（同步后必跑）

| 测试 | 验证什么 | 通过判据 |
|---|---|---|
| `organ_contract_test.py` | 每个 conductor-* 器官存在、frontmatter/name 匹配、输入/输出/降级章节齐备、方法文档自包含、注册表覆盖 | 全 PASS |
| `organ_effect_test.py` | 方法型器官关键步骤齐备；脚本型器官真实输入→输出冒烟 | 全 PASS |
| `script_parity_test.py` | conductor 本体 6 个重复入口是薄 shim（runpy 转发、无完整实现）、目标可编译、`--help` 可转发 | 全 PASS |

- 三测试与同步是一套：**只同步不验证 = 未完成**；测试失败必须修复后重跑，不得带病交付。
- 测试断言了器官数量与关键文件名——新增/改名器官时**先改测试再改文档**，让测试先行暴露断链。

## 4. 协作 skill 审计（低频）

`collaboration_skill_audit.py` 按"是否被工作流调用 / 是否产出门禁证据 / 是否与器官重复 / 体积开销"给候选 skill 打分，
用于决定收编（改名并入器官）、保留或废弃。历史结论已固化在 conductor 的 organ-registry 第三节，日常不重跑。
