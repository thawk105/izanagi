## 所見

### 1. P1 — scope 選定

- **file:line**: `docs/archive/worklog-phase3-0818-651.md:34-39,595-599`、`docs/archive/worklog-phase3-0819-671.md:555-557`、`output/insights/2026-08-15_t396-hole-allowlist-refuted/README.md:108-117`
- **real/refuted 見込み**: brief の事実認識は **refuted（正しい）**。ratified 文言は対象ファイルを名指しせず、起票の直接動機は role 契約の禁止文を削除して pin を再整合できる M6 である。
- **反証対象**: `s1-brief.md:14-19` の認識自体への反証はない。ただし、`s2-plan-output.md:111-116` の test-only 変更で role 契約 pin/M6 が解決したとは言えない。
- **scope**: `DENY_TABLE` 局所修復は scope 内。role-contract-text と source pin の意味的検査は scope 外。
- **含意**: 完了報告は「DENY_TABLE の縮小検出を実装した」に限定し、T-1357 全体または M6 の解決済みとは報告不可。

### 2. P2 — stale なテスト参照

- **file:line**: `orchestrator/tests/test_coder_effect_gate.py:151-171`、`docs/archive/worklog-phase3-0818-651.md:34-39`、`dc87fff7`
- **real/refuted 見込み**: P2 の核心は **refuted（brief が正しい）**。現行 `:151` は `test_explicit_unconditional_loop_headers_are_rejected` の decorator であり、旧 `test_ordinary_for_range_for_and_data_dependent_loops_pass` は `dc87fff7` で削除済み。`git log --oneline -- <path>` と `git show dc87fff7 --stat` も一致する。
- **反証対象**: `s1-brief.md:22-29` の stale 訂正は妥当。ただし「無関係な別テスト」はやや強く、現行テストも loop policy を扱う点は補正すべき。
- **scope**: scope 内の記述訂正。production 変更は不要。

### 3. D96 と decisions.md

- **file:line**: `docs/decisions.md:4269-4284`、`s1-brief.md:3-6,31-36`、`s2-plan-output.md:42-43`
- **real/refuted 見込み**: 「今回が D96 の必須手続対象外」という判断は **real（妥当）**。production の `DENY_TABLE`、`scan_host_effects`、候補の受理/拒否集合を変更せず、test-only の repository 不変条件を追加するだけである。test-only census を成果物受理集合変更ではないと扱う先例も `docs/decisions.md:19686-19691` にある。
- **反証対象**: brief/plan の「production 不変」主張への反証なし。
- **scope**: D96 適用判断は scope 内。新 D の要否は任意の裁定パッケージ候補。

判断は次のとおり。

- **推奨 A**: 新 D は起こさず、段7の worklog に「D96対象外、DENY_TABLE限定の test-only 不変条件」と記録する。
- **択 B**: category と identifier の組を将来も不変とする横断方針まで要求するなら、親が新 D として、baseline の独立性、追加許容、削除・category 移動の扱い、境界テストを明記する。これは author の独断ではなく親から裁定へ返すべきである。

### 4. consumer の網羅性

- **file:line**: `orchestrator/campaign/p3_s4_loop.py:57,243-275`、`orchestrator/critic/digest.py:40-43,724-737`
- **real/refuted 見込み**: **refuted**。production consumer は現物 grep 上この2箇所で、追加の `DENY_TABLE` consumer は見つからない。

| consumer | 仮定している不変条件 | 判定 |
|---|---|---|
| `p3_s4_loop.py:247-268` | scanner の finding が rule/category/count を持つ | category 数・identifier 集合は仮定しない |
| `digest.py:727-736` | `rule_id` と `category` の対応、count 範囲 | 5 category 固定や個別 identifier 集合は仮定しない |

`coder_effect_gate.py:117-138` の rule ID/category/identifier 一意性は module load 時に既に検査され、`test_coder_effect_gate.py:81-98` でも category 集合と一意性を固定している。したがって consumer 見落としはない。

ただし category 移動は identifier の禁止自体ではなく、`digest.py:729` の報告分類を変える。これは「禁止集合の縮小」とは別の分類契約であり、黙って scope に含めるなら追加判断が必要である。

- **scope**: identifier の縮小検出は scope 内。category 分類の不変性は追加設計として scope 外候補。

### 5. T-1356 との重複・矛盾

- **file:line**: `docs/archive/worklog-phase3-0818-651.md:588-594`、`docs/archive/worklog-phase3-0819-671.md:551-554`、`s2-plan-output.md:111-116`
- **real/refuted 見込み**: committed history 上のファイル重複は **refuted**。T-1356 は `.claude/agents/auditor.md` の入力/checklist、T-1357 は `orchestrator/tests/test_coder_effect_gate.py` のみである。`git log --all --grep='T-1356'` に該当 commit もない。
- **反証対象**: brief/plan の所有ファイル分離への反証なし。ただし uncommitted な別 worktree の実編集まではこの方法では証明不能。
- **scope**: file overlap は scope 内確認。role 契約の完了主張は scope 外。
- **設計整合**: 両者は矛盾しない。T-1357 の frozen test は auditor への結線を代替せず、T-1356 の「結線前に auditor が拒否すると書かない」制約を維持する。

### 6. superset 判定

- **file:line**: `s1-brief.md:31-36`、`s2-plan-output.md:63-72`、`orchestrator/campaign/coder_effect_gate.py:49-55,134-138`
- **real/refuted 見込み**: `current ⊇ frozen` の選択は **real（推奨可能）**。「縮んでいない」は削除を検知し、追加を許容する比較で自然に表現できる。完全一致は「追加も禁止」という別契約になる。
- **反証対象**: plan の exact-equality 不採用理由への反証なし。
- **注意点**: plan の比較は `(category, identifier)` 集合であり、単なる identifier の和集合より強い。identifier が別 category へ移動しても拒否自体が続く場合、それを縮小と呼ぶかは明示が必要。
- **scope**: identifier の縮小は scope 内。category 移動禁止まで含めるなら追加判断。
- **追加の補正**: `s1-brief.md:34-35` の「拡張許容」は実装全体では「既存5 category 内の identifier 追加」に限られる。新 category は既存テスト `test_coder_effect_gate.py:78-81` が拒否し、plan 自身も `s2-plan-output.md:72` で認識している。

## 裁定パッケージ候補

1. **元の role-contract/M6 をどう扱うか**
   - A（推奨）: 今 wave は `DENY_TABLE` 限定で着地し、role source pin の意味検査を別 T として残す。
   - B: `.claude/agents/coder-v4-autonomous-sort.md` まで scope を拡張する。現起動引数を越えるため、別 wave/裁定が必要。

2. **category 移動を禁止するか**
   - A（現 plan 維持）: `(category, identifier)` を frozen entry と明記し、分類不変性も守る。
   - B: identifier の和集合だけを frozen にし、category 分類の変更は別契約に分離する。

## 総括

P1/P2 の scope 選定と stale 訂正は維持すべきである。  
ただし本 wave は role-contract pin/M6 全体を解決せず、DENY_TABLE 局所成果としてのみ報告する。  
consumer の追加見落としはなく、D96 は今回の test-only 変更には必須ではない。  
superset は維持し、category-aware 比較の意味だけを明記すべきである。