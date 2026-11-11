---
name: tzkj-student-handbook
description: 台州科技职业学院《学生手册》知识库，内含 521 道校规校纪题目（填空、判断、单选、多选）及答案，覆盖学籍注册与转专业休学、考试与考场纪律、综合素质与德育考评、奖学金助学金与评优、纪律处分、学生公寓、请假考勤与出入校门、行为规范与校园秩序、社团与班集体、图书借阅与阳光长跑、学生资助与勤工助学、征兵入伍等主题。当用户询问台州科技职业学院（台科院）学生手册、校规校纪、学生管理规定、奖惩办法，或需要按校规判断某行为是否违规、查询具体分值比例与办理流程、生成或校对相关练习题时使用。When asked about the student handbook, campus regulations, scholarship/honor rules, disciplinary measures, dormitory or leave policies of Taizhou Vocational College of Science & Technology, use this knowledge base.
---

# 台州科技职业学院学生手册知识库

## 这是什么

一份从学生手册配套题库（521 题）整理出的结构化知识库，用来回答"学校怎么规定"这类问题，也用来出题、判分、核对答案。

- 数据规模：521 题 —— 填空题 136、判断题 141、单选题 103、多选题 141。
- 组织方式：每道题有稳定题号（`TF-001` 填空、`PD-001` 判断、`SC-001` 单选、`MC-001` 多选），按 11 个主题分类。
- 内容边界：题库只覆盖学生手册配套学习范围，**不是手册全文**，也不含最新修订。涉及处分、退学、申诉、奖助金额等实际权益的，以学校正式文件和当年通知为准。

## 怎么用

### 1. 先判断问题落在哪个主题

| 主题 | 典型问法 | 文件 |
|---|---|---|
| 01 学籍与注册 | 怎么注册、转专业时间、休学几次、退学条件、应征入伍保留学籍 | `references/by-topic/01-学籍与注册.md` |
| 02 考试与成绩 | 补考次数、考场能带什么、作弊怎么处理、诚信考场 | `references/by-topic/02-考试与成绩.md` |
| 03 综合素质考评 | 德育分怎么算、满分多少、加分扣分标准、德育学分、体能与阳光长跑 | `references/by-topic/03-综合素质考评.md` |
| 04 奖助学金与评优 | 奖学金条件与比例、三好学生、优秀学生干部、先进班级、优良学风班 | `references/by-topic/04-奖助学金与评优.md` |
| 05 纪律与处分 | 处分种类、旷课多少节给什么处分、打架作弊怎么处分 | `references/by-topic/05-纪律与处分.md` |
| 06 学生公寓与住宿 | 换寝室、违禁电器、空调温度、门禁时间、文明寝室、校外住宿 | `references/by-topic/06-学生公寓与住宿.md` |
| 07 请假、考勤与出入校门 | 请假审批权限、能请多久、补假、校门查验、集体外出审批 | `references/by-topic/07-请假、考勤与出入校门.md` |
| 08 行为规范与校园秩序 | 集会礼仪、升旗、绿色学校、垃圾分类、电动车、校内商户 | `references/by-topic/08-行为规范与校园秩序.md` |
| 09 社团、班集体与学生组织 | 社团成立条件、加入上限、社团经费、班集体考核算法、军训 | `references/by-topic/09-社团、班集体与学生组织.md` |
| 10 图书借阅与体育 | 借书本数与期限、超期与赔偿、期刊、体测与阳光长跑 | `references/by-topic/10-图书借阅与体育.md` |
| 11 学生资助与勤工助学 | 资助对象认定、学费减免、勤工助学时薪工时、困难补助、发展性资助、征兵优待 | `references/by-topic/11-学生资助与勤工助学.md` |

**先查速查表**：常见数字、比例、期限集中在 `references/key-facts.md`，多数问题在那里就能得到答案，不必展开整份题库。

### 2. 用脚本做精确检索（推荐）

```bash
python scripts/search.py 转专业                     # 关键词检索
python scripts/search.py 旷课 处分 -n 6              # 多关键词，按相关度排序
python scripts/search.py 请假 --topic 07            # 限定主题（编号或中文名）
python scripts/search.py 比例 --type 单选题           # 限定题型
python scripts/search.py --id TF-022                 # 按题号取原题
python scripts/search.py --list-topics               # 看主题清单与题量
python scripts/search.py 奖学金 --json               # 机器可读输出
```

没有 Python 环境时，直接读 `references/by-topic/*.md`，或用 `grep` 在 `data/questions.jsonl` 里搜关键词。

### 3. 回答时遵守的规矩

1. **有据可依**：每个结论后面标出题号，如"（TF-001）"。没有题库依据的内容不要写成校规。
2. **优先速查表**：`key-facts.md` 里的数字已做过交叉核对；它没覆盖的再去题库找。
3. **冲突要说明**：题库本身存在少量答案键矛盾，见 `references/conflicts.md`。遇到冲突，说明两种说法及各自题号，给出倾向，并提示以正式文件为准。
4. **不猜**：题目里没写的（如某年最新金额、具体经办人、临时通知），明确说"题库未收录，需查学校最新通知"，不要按常识补全。
5. **区分题型用途**：填空题适合确认表述与关键词；判断题适合确认某说法真假；选择题适合确认数值与范围。

### 4. 文件地图

```
SKILL.md                    本文件：触发说明与使用流程
README.md                   GitHub 说明：来源、安装、许可、更新方法
references/key-facts.md     核心数字与规则速查（按主题，全部带题号）
references/conflicts.md     题库内部矛盾清单与处理建议
references/by-topic/*.md    12 份主题题库（原文照录，含题目与答案解析）
data/questions.jsonl        521 题结构化数据（唯一权威副本）
data/questions.csv          同上，便于表格软件查看
scripts/search.py           题库检索
scripts/build_bank.py       从原始 TXT 重新生成 data 与 by-topic（换新题库时用）
```
