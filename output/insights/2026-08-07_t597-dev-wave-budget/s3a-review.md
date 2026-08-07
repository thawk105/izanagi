結論は **NO-GO** です。DW-M08 の全面 pointer 化には未代替経路が残り、提案 5 test のうち 1 件は対象分岐を削除しても成立します。以下は静的検査のみで、pytest と `check_docs.py` は実行していません。

## 所見

### A-1

- **主張** — 期待・観測 node の正規化は、現行 tool が扱えない `@real-repo` 経路を残しており「完全代替済み」ではありません。
- **根拠** — `_normalize_node()` は repo prefix と `./` だけを除去し、test 部の `@real-repo` 接尾辞を保持します (`tools/mutation_harness.py:798-809`)。F95 は collection の素 node と実走側の接尾辞付き node が両立せず、その変異面が登録から落ちると記録しています (`docs/failures.md:2294-2314`)。修正 [T-417] は現在も未完了です (`docs/archive/worklog-phase3-0804-158-159.md:567-571`)。提案 test は `./` と絶対 path しか扱いません (`s2-plan.md:74`)。
- **深刻度** — blocker
- **成果物影響** — real-repo node を赤くする変異の「期待・観測を同形式で照合する」義務が誰にも担われず、その検査面が変異台帳から黙って落ちます。

### A-2

- **主張** — canonical job stdout の強制には、`runner_mode=local` と `tools/run_tests.py` を組み合わせる許可経路があります。
- **根拠** — `_runner_identity()` は `run_tests.py` を runner mode に関係なく許可します (`tools/mutation_harness.py:450-473`)。`run_tests.py` は headroom に応じ local/dispatch を切り替えます (`tools/run_tests.py:1684-1754,1780-1786`)。一方 harness は指定 mode が `local` なら実際の dispatch receipt を読まず console を `job_stdout` にします (`tools/mutation_harness.py:1168-1171`)。console は省略され、FAILED 行が消え得ることが既知です (`docs/failures.md:1665-1673`)。計画の既存 test は `runner_mode="dispatch"` だけです (`orchestrator/tests/test_mutation_harness.py:968-988`)。
- **深刻度** — blocker
- **成果物影響** — この呼出形では「job stdout 全文を証拠にする」義務の担い手がなく、欠落した余分な失敗 node により偽の完全一致を変異台帳へ記録できます。

### A-3

- **主張** — `"-rf" in command` は有効な report option の強制ではなく、提案 test も競合 option を覆いません。
- **根拠** — main は token の存在だけを検査します (`tools/mutation_harness.py:1881-1889`)。既存記録には `-rf -rs` がこの検査形を満たしつつ、後勝ちの `-rs` により FAILED node を失う事例があります (`output/insights/2026-07-29_t146-probe-cleanup-wave/s6-review-adjudication.md:16-17`)。提案 test は単に `-rf` token を除くだけです (`s2-plan.md:73`)。
- **深刻度** — blocker
- **成果物影響** — pytest が FAILED summary を実効的に出す義務を検証する担い手がなく、正しく発火した変異が node 抽出不能で停止します。

### A-4

- **主張** — `DW-M05` が許す独自 harness には tool の機械強制が届かないため、M08 の具体的 prose を全面削除できません。
- **根拠** — `DW-M05` の独自 harness 条件が列挙する「同等の検査」は固定 HEAD・復元・lock・flush・resume・signal 復元です (`docs/dev-wave/mutation.md:31-37`)。M08 固有の `-rf`、stdout、抽出、0-node fail-close、正規化は現行 `DW-M08` が担います (`同:49-54`)。計画後の本文は tool pointer だけです (`s2-plan.md:20-24`)。Skill/dispatcher はこの leaf を読むだけで義務を複製していません (`.agents/skills/dev-wave/SKILL.md:21-23`, `.claude/commands/dev-wave.md:70`)。
- **深刻度** — blocker
- **成果物影響** — 独自 harness 作者に対する M08 の具体的検査義務が prose にも機械層にも残らず、failed-node 証拠のない独自台帳を段4で承認できます。

### A-5

- **主張** — separator 無し用の提案 test は、対象とする `if not separator` 分岐の削除に対して検出力ゼロです。
- **根拠** — `remainder.partition(" - ")` は separator 不在時にも既に `node == remainder` を返し、続く `node = remainder` は同値再代入です (`tools/mutation_harness.py:822-825`)。したがって計画が名指す `:824-825` を削除しても提案 assert は成立します (`s2-plan.md:72`)。これは brief の「分岐の存在を自己申告根拠にしない」に反します (`brief.md:49-50`)。
- **深刻度** — blocker
- **成果物影響** — 新旧 test の検出差を示す `DW-M08` の diagnostic-sensitivity 義務を担う有効な変異がなく、prose 削除の pin 根拠が成立しません。

### A-6

- **主張** — 待ち手案は、採用済み規約の「通知のたびに作り直さない」を削っています。
- **根拠** — 一次控えは「既存待ち手を作り直さず、通知時は状態を読む」と明記します (`rulings-inbox/2026-08-05-background-waiter-duplication.md:23-24`)。これは実際に 73 本を常駐させた原因です (`同:8-17`)。計画の「1 条件 1 本」は同時本数しか拘束せず、逐次置換を禁じません (`s2-plan.md:119-127`)。
- **深刻度** — must-fix
- **成果物影響** — 親の「通知時に待ち手を再生成しない」義務が誰にも担われず、出口なし待ち手の再発を許します。

### A-7

- **主張** — 「機構名検索」の検索先を `見送り台帳` に狭めると、元事故を検出できません。
- **根拠** — `見送り台帳` は `docs/phase3.md` の固有 H2 です (`docs/phase3.md:529`)。しかし F154 の恒久対応は、別 ID に記録された裁定を見つけるため機構名で `docs/worklog.md` を検索することです (`docs/failures.md:3525-3530`)。計画案は「見送り台帳」と書き換えています (`s2-plan.md:137-139`)。
- **深刻度** — must-fix
- **成果物影響** — 段1親の「worklog を機構名で検索して別 ID の見送り裁定を検出する」義務がなくなり、見送り済み機構を再実装できます。

### A-8

- **主張** — [T-529] 由来案は provisional な候補を先取りし、かつ「各解除条件と今回裁定の対応付け」を落としています。
- **根拠** — 元 handoff は「条文単位の棚卸し」と「今回裁定が各条件へ効くかの対応付け」の二義務を候補として記載します (`/work/1/SFC/tanab/dev-wave-jobs/handoff/wave-t529-impl-reraise.md:40-45`)。計画案は前者だけです (`s2-plan.md:143-153`)。
- **深刻度** — must-fix
- **成果物影響** — 段1親の「各解除条件へ今回裁定を対応付ける」義務が誰にも担われず、未解除 blocker を解除済みと誤判定できます。

### A-9

- **主張** — brief の「完全一致に専用 pin がない」と、その分岐削除後も既存 test が成立するという前提は誤りです。
- **根拠** — strict superset と strict subset の両方向が既に `MISMATCH` を固定しています (`orchestrator/tests/test_mutation_harness.py:352-378`)。brief はこれを 0 件として扱っています (`brief.md:35-37,77-79`)。plan 自身も誤りを認めています (`s2-plan.md:80,204-206`)。
- **深刻度** — must-fix
- **成果物影響** — `DW-S01` の「純増検出力だけを書く」義務が破れ、既存検出力を新規 test に誤帰属した変異記録になります。

## 提案 assert 5 件の静的判定

| 提案 | 対象分岐削除後 | 判定 |
|---|---|---|
| separator 無し | assert は成立したまま | 検出力ゼロ |
| `-rf` 欠落 | exact guard 削除で assert 不成立 | 検出力あり。ただし A-3 の競合 option は未被覆 |
| 同値 node 正規化 | `_observed_status` の正規化削除で assert 不成立 | 部分的。`@real-repo` と production 経路は未被覆 |
| mutation rc=1/node 0 | 対象分岐削除で `MISMATCH` になり assert 不成立 | 検出力あり |
| baseline rc=1/node 0 | 対象分岐削除で `FAILED` になり assert 不成立 | 検出力あり |

## 段1前提・順序・層の監査

| 前提 | 判定 |
|---|---|
| 1. byte / cap | 正しい。raw UTF-8 count は 25,187、cap 定数も一致 (`tools/check_docs.py:176-181,254-258`) |
| 2. M08 機械部分を全強制 | **反証** — A-1〜A-3 |
| 3. tool 内の集合完全一致 | admitted node 表記に限れば正しい (`tools/mutation_harness.py:1191-1193`) |
| 4. pin 不在 | **一部反証** — `-rf` と rc=1/空は未 pin、完全一致は既存 pin 済み |
| 5. O19 重複 | 正しい (`docs/dev-wave/core.md:32-35`, `operations.md:105-112`) |
| 6. pgrep 自己一致採録済み | 狭い主張として正しい。現行 `DW-M05` と commit `a62be201` が一致 (`mutation.md:35-37`) |
| 7. 他 wave の需要 | 一部のみ確定。機構名検索は worklog 採録済みだが、T-529/T-595 は handoff 上の provisional 候補 |

工程順そのものは `test commit → descendant docs commit` で分離され (`s2-plan.md:165-175`)、現時点の worktree も clean でした。順序違反は見つかっていません。

層検索では Skill・dispatcher・hooks・role adapter に M08 の具体義務の写しはありません。したがって pointer 化は「削ったふり」ではなく、段6と独自 harness 作者が読む具体契約を実際に除去します。なお `check_docs.py` は意味保存を検査しないと明記されています (`docs/skill-self-improvement.md:77-84`)。

## 総括

- **blocker: 5 件**（A-1〜A-5）
- **判定: NO-GO**
- DW-M08 pointer 化は、T-417、runner-mode/canonical stdout、実効 `-rf`、独自 harness の各穴を閉じて pin するか、現行 prose を保持する必要があります。
- 待ち手・機構名検索・解除条件案も、元候補の全義務へ戻してから byte を再計算すべきです。