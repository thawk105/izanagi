以下は静的読解と UTF-8 byte 再計算のみ。テストは実行していない。

### 所見 1: 経路 A の 13 節は T-412 の既裁定 scope そのものである

- 深刻度: blocker
- 対象: 段 2 §2 全項目、§5 `[T-412]`、P1
- 実測: `s2-plan.md:44-46,52-68` は `DW-O04/O06/O08/O09/O10/O11/O12/O14/O16/O17/O18/O19/O20` の 13 節、合計 5,008 bytes、削除候補ゼロと記載している。T-412 一次資料も `docs/archive/worklog-phase3-0804-163-164.md:284-306` で旧 14 節を全て不採、`docs/archive/worklog-phase3-0806-242-244.md:969-973` で剪定 0 bytes と確定している。T-454 の固定 scope は待ち手規約 3 条、`DW-O01`、`DW-M05`、`DW-M08`、`DW-S06-B` の F112/F124 である (`docs/archive/worklog-phase3-0805-223.md:249-254`, `docs/archive/worklog-phase3-0806-242-244.md:1010-1013`)。
- なぜ壊れるか: 「材料供給」と呼んでも、既にゼロ裁定された削除集合を T-664 の新規候補として再審査する ownership は発生しない。T-454 の固定 scope も同様に新規 bytes ではない。
- 提案: 候補を殺す。13 節は T-412 の確定結果を参照するだけにし、T-454 の scope は作り直さず、そのまま既裁定として除外する。

### 所見 2: T-313/T-328 の実装順を飛ばして L2 の byte 価値を裁定している

- 深刻度: major
- 対象: 段 2 §5 `[T-313]` / `[T-328]`、総括 1〜3
- 実測: T-313 一次裁定は「常に読む層は固定上限、全体の固定文字数上限は撤廃、剪定は byte 数でなく発火実績＋機械代替」として実装待ち (`docs/archive/worklog-phase3-0803-140.md:67-71`)。最新 T-328 は「T-313 を先に実装し、旧外出し提案は D94(a) と同一なので撤回」としている (`docs/archive/worklog-phase3-0804-152-153.md:14-26,69-72`)。一方、現行 `tools/check_docs.py:3704-3709` は依然として 25,200 bytes の集約 hard ceiling を検査する。
- なぜ壊れるか: 実装前は現行集約 gate が残り、実装後は L2 の解放 bytes が予算価値を失う。段 2 はこの二つの時点を分離せず、現在の裁定候補として A を並べている。なお `DW-G05` は常時読む L1 なので、T-313 だけでは自動的に空かない (`docs/archive/worklog-phase3-0804-156.md:42-44`)。したがって「wave 全体が不要」ではなく、「L2 の byte 削減判断を先送りすべき」が正しい。
- 提案: 別経路へ回す。T-313 実装後に再分類・再計測し、T-412 の L2 は byte 候補として再起票しない。残すのは L0/L1 の候補だけにする。

### 所見 3: dispatcher の `DW-CTX` 移管は D94(c) の再発である

- 深刻度: blocker
- 対象: 段 2 §4、`.claude/commands/dev-wave.md:42` → `DW-CTX`
- 実測: 段 2 は `s2-plan.md:107` で command の 2 行を `DW-CTX` へ移す案を出し、`s2-plan.md:116` では「D94(c) は復活させない」と記載している。D94 は `docs/decisions.md:4228-4233` で「DW-CTX ポインタ統合」を明示的に却下し、理由を「外部 supervisor と manager で読者主体が異なる」としている。現行 `core.md:114-117` も外部 supervisor 向けの主体を明記している。
- なぜ壊れるか: 同じ文面を既存節へ移すだけでも、入口 command の読者と manager 条件節の読者を同一視するため、意味等価性を証明できない。「復活させない」という注記と提案本体が自己矛盾している。
- 提案: 候補を殺す。少なくとも `DW-CTX` 統合は裁定パッケージから除外する。`DW-STOP` 統合は別途、読了時点と成果物影響を独立検証する。

### 所見 4: hit 数は発火実績の証明にならず、O10/O12 が実際に反証している

- 深刻度: major
- 対象: 親 `s1-evidence.md`、段 2 §2 の発火実績判定
- 実測: `firing_evidence.py:38-47` は正規表現の `findall` 数を合計するだけで、文脈判定・重複排除・実行 event との結合をしていない。親自身も `s1-evidence.md:51-53` で証明ではないと認めている。`DW-O12` は `output/insights/2026-08-06_t419-u2-recalibration/s4-adjudication.md:146-150` に実行後の 4 failed / 307 passed の記録があり、`DW-O10` は同 `:217-221` に新規 sidecar の producer inventory 漏れがある。逆に `docs/decisions.md:3713` の `write-path` は一般的な工程語である。
- なぜ壊れるか: O12 の hit=2、O10 の hit=17 は「薄い／発火なし」の証拠ではない。両方とも実発火があり、件数には単なる指針への言及も混ざる。段 2 は直接資料も併記しているため O10/O12 自体を採用してはいないが、hit 数を D94 の反証条件へ輸出すると残りの判定も同じ誤りになる。
- 提案: 条件を足す。各 L2 について、検索 hit ではなく実行 event・対象 artifact・義務の変化を直接記録する semantic evidence 表を要求する。

### 所見 5: T-454 の `DW-M08` を「既存 test 済み」とする記述は一次資料と逆である

- 深刻度: major
- 対象: 段 2 §3 の既裁定行 `DW-M08`
- 実測: `s2-plan.md:79` は「`DW-M08` exact set は既存実装・test に到達済み」としている。しかし T-454 一次資料は、既存 test が互いに素な集合しか扱わず、`failed_keys == expected_keys` の弱化変異で反証されたと明記している (`docs/archive/worklog-phase3-0806-256-261.md:859-866`)。固定されたのは 7 vector だけで、他の弱化変異がないことは示していない。
- なぜ壊れるか: 既存実装と既存 test の存在を、性質の固定と読み替えている。これにより T-454 の未完了分を T-664 から除外する根拠も、純増検出力 0 とする根拠も崩れる。
- 提案: 別経路へ回す。T-454 の確定 scope は変更せず、状態だけを「7 vector 部分実施・予算 0 bytes」と訂正する。T-664 の新規候補には数えない。

### 所見 6: B1 の 449 bytes は算術上は入るが、安全義務移管の証明が足りない

- 深刻度: major
- 対象: 段 2 §3 B1 `DW-O23`
- 実測: 現行 `operations.md:121-132` の節は独立計測で 1,123 bytes、提案 snippet `s2-plan.md:84-91` は 674 bytesで、差分 449 bytes は正しい。既計測の `DW-G05` 追記 274 bytes と `DW-O01` 追記 76 bytesを加えても、dispatcher +68 bytes込みで `25,184−449+274+76+68=25,153`、残り 47 bytes となる (`docs/archive/worklog-phase3-0804-156.md:38-45,50-55`)。
- なぜ壊れるか: 問題は算術ではなく、提案文が `T/D/F` 採番、canonical 3 台帳、worklog rotation 一回、tracked/index/submodule/incoming 衝突、docs/handoff と Git admin の双方向非接触を落としていること。実装の `LandResult` field (`tools/dev_wave_land.py:77-104`) と既存の fold failure test (`orchestrator/tests/test_dev_wave_land.py:1925-1952`) は、これら全 caller 義務の独立 oracle ではない。`DW-G05` が要求する certified 選択・レポート・台帳への影響も記述されていない。
- 提案: 条件を足す。全 prose 行と実 field の対応表、tool/test 同時弱化に耐える独立 oracle、台帳・worklog への成果物影響を揃えるまで、449 bytes を解放量として裁定しない。

### 所見 7: B2 は `inventory entry` という実成果物 field を持たない

- 深刻度: major
- 対象: 段 2 §3 B2 `DW-O10`
- 実測: 提案は `final-receipt.json` の `staging_manifest[].path` 等を比較する (`s2-plan.md:77`)。しかし `tools/pegasus/collect_receipt.py:76-91` は実ディレクトリ内の全 regular file を自動列挙し、`:153-179` の receipt にあるのは実体 manifest だけで、期待 inventory／登録集合 field はない。T-419 の sidecar も自動的に manifest へ入る (`output/insights/2026-08-06_t419-u2-recalibration/s4-adjudication.md:217-221`)。
- なぜ壊れるか: candidate に sidecar を追加すれば manifest の差分は見えるが、「producer inventory への登録漏れ」と判定する authority がない。別の hard-code inventory を test に埋めれば二重の棚卸しになり、現行 O10 prose の義務を削れない。段 2 自身も予算解放 0 としている。
- 提案: 候補を殺す。必要なら T-419 側で producer inventory の schema／consumer を裁定し、T-664 の byte 候補からは外す。

### 所見 8: B3 は赤にできても O04 の prose を削れない

- 深刻度: major
- 対象: 段 2 §3 B3 `DW-O04`
- 実測: `s2-plan.md:78` の `git commit -m ...` は単独行として赤にする入力になり得るが、O04 の本義務は `Write` で message file を作り `git commit -F` を使うこと (`docs/dev-wave/operations.md:27-30`)。hook は不透明構文を拒否する正規表現 (`hooks/guard_bash.py:105-109`) を持つだけで、Codex には PreToolUse hook が自動適用されない (`AGENTS.md:18-20,38-40`)。
- なぜ壊れるか: command event の `tool_name` と文字列を検査しても、Write が実行されたこと、message file の内容、`-F` の使用を結び付けられない。赤を一つ追加しても、作業者への事前指示を消す機械的根拠はなく、成果物の certified 選択・レポート・台帳への影響も書けない。
- 提案: 候補を殺す。hook 配線と Write→message file→commit の因果を別途機械化する場合だけ、安全性の独立課題として扱う。

## 総括

blocker は 2 件（所見 1・3）。このまま裁定パッケージ化するのは **NO-GO**。  
T-313 を先に実装して再計測し、T-412 の 13 節と T-454 の固定 scope は再起票しない。  
残る価値は、D94(c) を除外し、独立 oracle と成果物影響を補った L1 `DW-O23` と検証済みの L0 候補だけである。