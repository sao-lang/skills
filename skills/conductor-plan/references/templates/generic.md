# 通用场景模板库（standalone 模式）

> 每张模板给出「典型节点骨架 + 动作类型 + 退出判据 + 常见控制流」。
> 规划时**按目标匹配模板，再按用户输入定制**——模板是起点不是答案；匹配不上就用 generic 从零推导。

## 1. 日常任务规划（搬家/活动/准备）

```
research(读约束:时间/资源) → think(拆目标) → action(准备A) → action(准备B)
→ gate(就绪检查:清单逐项?) → action(执行) → gate(完成确认)
常见：parallel(并行准备项)、retry(资源不可用重试)、ask(时间/预算未定)
```

## 2. 业务流程（下单/审批/库存）

```
action(接收请求) → think(校验) → branch(条件判断)
  --通过--> action(执行主流程) → gate(结果确认) → action(通知)
  --不通过--> action(驳回/补件) → loop_back
  --异常--> retry(重试上限) → action(人工介入)
常见：branch 多分支、retry、异常路径、不可逆操作标副作用
```

## 3. 决策分析（选 offer/方案）

```
research(收集选项信息) → think(定判据) → research(补关键数据)
→ branch(按判据打分) → think(权衡) → gate(判据覆盖?)
→ think(结论+风险) → ask(用户是否接受/需补信息)
常见：ask(判据未定先问用户)、branch、subplan(每个选项展开)
```

## 4. 问题排查（非开发：网络/设备/健康）

```
research(收集现象) → think(列可能原因) → action(排查项1) → gate(复现/消失?)
  --未解决--> action(排查项2) → loop_back（带 max_rounds）
  --解决--> action(修复+验证)
  全失败 → ask(用户补充信息) 或 action(求助专家)
常见：loop(排查循环)、retry、noop_limit(连续排查无进展停下)
```

## 5. 项目管理（多阶段/里程碑）

```
subplan(阶段1:需求) → gate(里程碑1评审) → subplan(阶段2:执行)
→ gate(里程碑2) → subplan(阶段3:交付)
常见：subplan(每阶段一张子图)、parallel(并行工作流)、gate(里程碑)
```

## 6. 自动化/运维（定时/批处理）

```
tool(触发:定时/事件) → tool(执行任务) → gate(成功?)
  --失败--> retry(max=3) → loop_back；超限 → tool(告警) → abort
  --成功--> tool(记录日志) → gate(下次调度就绪)
常见：retry、loop、tool 为主、budget.max_rounds 必填
```

## 7. 学习路径（课程/技能）

```
research(评估起点) → ask(时间/目标确认) → think(排阶段依赖)
→ subplan(阶段1:基础) → gate(自测通过?) → subplan(阶段2:进阶)
→ ... → gate(结业验收)
常见：subplan、gate(每阶段自测)、habit(每日时长)、research(找资源)
```

## 8. 对话/谈判策略（面试/沟通）

```
research(了解对方/场景) → think(预测问题分支) → branch(对方可能问X/Y/Z)
  每支 → think(应答要点) → branch(追问?) → think(应对)
→ gate(覆盖高风险问题?) → action(实战)
常见：branch 多分支、think 为主、ask(用户补充背景)
```

## 9. 内容创作（写作/报告/视频）

```
research(收集素材) → think(定结构) → action(大纲) → ask(用户确认大纲)
→ action(初稿) → gate(自审:覆盖要点?) → action(修改) → gate(终稿确认)
常见：ask(大纲确认)、loop(修改循环)、gate
```

## 10. 购物/比价/采购

```
research(列候选) → think(定判据) → research(查价格/评价)
→ branch(筛选) → think(推荐) → ask(用户选) → action(下单)
→ gate(确认收货) 
常见：research、branch、ask、action(不可逆操作标注)
```

## 11. 模糊需求（“帮我搞个东西”）

```
ask(目标产出物?) → ask(对象/范围?) → think(归类到模板1-10)
→ [匹配模板骨架] → ask(关键约束?) → 出图
常见：先澄清后出图；信息不足**禁止出图**，停在 ask
```

## 模板使用纪律

1. 模板是**骨架起点**：按用户输入增删节点、改判定条件、补退出判据。
2. 同一任务可跨模板组合（如“项目+学习”），用 subplan 分层。
3. 每个模板节点的 `exit_criteria` 必须在出图时**具体化**（模板里是占位，图里是判定式）。
4. 模板不含 token 浪费：只展开与本次目标相关的分支，无关分支删除并在声明写“省掉”。
