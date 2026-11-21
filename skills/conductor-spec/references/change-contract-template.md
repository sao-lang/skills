# Change contract · 六段模板

> 一份契约 = 一次改动的持久快照。文件名建议 `change-contract.md`，放在项目根目录或 `docs/` 下。
> 规则：只写有后续影响的内容；不写流水账；Acceptance 必须可机器验收。

```markdown
# Change: <ID> / <日期> / <状态：draft|confirmed|verified>
## Why
<这次改动要解决什么。写动机与用户意图，不写方案。>

## Delta
<相对上一版基线的具体变化。首个基线写"首个基线，无前序版本"。>
- 

## Invariants
<不能破坏的既有契约：接口签名、数据格式、错误语义、权限边界。>
- 

## Affected
<可能受影响的模块/符号/调用方。直接喂给 conductor-impact 做核实。>
- 

## Acceptance
<可机器验收的条目。每条必须能对应一条命令+退出码或文件:行号。>
- 

## Open
<仍未拍板的事项，每条带需谁拍板；被否决的方案也记在这里。>
- 
```

## 填写口径

- **Why** 不写"加了 X 函数"，写"用户反复遇到 Y，导致 Z"。
- **Delta** 用动词开头：新增 / 删除 / 替换 / 重命名 / 约束。
- **Invariants** 写"不许变"，不写"建议不变"。
- **Affected** 允许是草稿，但必须标注"需 conductor-impact 核实"。
- **Acceptance** 禁写"工作正常"，必须写可执行验证。
- **Open** 非空时，conductor 不得把契约标为 confirmed。
