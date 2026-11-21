# 待删项残留核对（removal_check）

> 用途：解决"AI 改需求只加不删"——需求变更后旧字段/函数/逻辑/功能还赖在代码里。
> 判据：**改到哪，删干净到哪**；待删项有残留 = Blocker，禁止进 review / 标完成。

## 输入从哪来

优先从 `change-contract.md` 的 **Delta 段**自动提取：含 `删除/移除/替换/废弃/下线/去掉` 动词、
且带反引号符号名的条目。例：

```markdown
## Delta
- 删除 `old_field` 字段（因 new_field 替代）
- 移除 `if legacy_mode:` 分支
```

人工补充用 `--symbols Foo,bar` 或 `--list removals.txt`（每行一个符号）。

**"删除 X"只写中文、不写符号名 = 机器无法核对** → 脚本报错并列出该条目，退回 S2 补登记。

## 门禁命令

```bash
# S4/S5 收尾核对（契约驱动，最常用）
python ../scripts/removal_check.py --contract change-contract.md --path src

# 显式符号清单
python ../scripts/removal_check.py --symbols old_field,LegacyFetcher --path src

# 叠加：契约 + 额外符号
python ../scripts/removal_check.py --contract change-contract.md --symbols extra_fn --path src
```

## 判定

| 退出码 | 含义 | 处置 |
|---|---|---|
| 0 | 所有待删符号已消失 | 留证据入 overview / 台账 |
| 1 | 有待删项残留，或没提取到任何符号 | 修到零残留；补契约登记后重跑 |

输出逐条列出每个待删符号的**定义处与引用处**（`file:line`）。定义来自各语言的
`def/class/fn/const/字段` 声明模式；引用按词边界扫描，排除纯注释行与测试目录。

## 边界与豁免

- **启发式核对，不替代语义判断**：同名但不同语义的符号（如别处的 `id`）会误报——用更精确的符号名，或通过 review 留痕豁免。
- **合法双轨**（用户显式要求且已在契约 Open 段登记的兼容层）：从待删清单移除该项，并在 overview 写明理由；不要试图用注释骗过扫描。
- **字段/配置键**以词边界匹配，改名后的旧键若仍出现在配置/数据文件里会被抓到（扩展名用 `--exts` 覆盖）。
- 本脚本**只判定残留事实**，是否放行由 conductor 决定；与 `source_purity.py`（反假实现/动态类型/双轨信号）互补，可同时跑。
