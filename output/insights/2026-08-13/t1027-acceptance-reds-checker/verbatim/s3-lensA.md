## 所見

- [B] 親 brief の不変条件が逆向きである。[brief.md:59-61](/work/1/SFC/tanab/dev-wave-jobs/t1027-acceptance-reds-checker/brief.md:59) は「不完全 collection から `attributable` を出すな」と書くが、禁止すべきなのは `non-attributable` である。再現/影響: この文面を実装・変異判定の正本にすると、判定不能な赤を `status=non-attributable-only`、rc=0 として checker receipt に記録でき、将来の land 受理集合へ壊れた wave が入る。

- [B] 「最長 exact match」は完全な main collection 上でも `@group` と literal `@`、summary detail と literal ` - ` を識別できない。[plan.md:23](/work/1/SFC/tanab/dev-wave-jobs/t1027-acceptance-reds-checker/plan.md:23)、[check_acceptance_reds.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:108)。再現/影響: wave が `p.py::test_target@literal` を追加して失敗し、main の完全 collection が既知赤 `p.py::test_target` だけなら、reference `p.py::test_target@literal - detail` は base test + group と解釈され、base の rerun rc=1 から top-level rc=0、`non-attributable` になる。`test_foo` / `test_foo_bar`、`[...]`、class の `::` は suffix が `_`、`[`、`::` なので拒否され、この反例は `@` と ` - ` に限定される。

- [B] 単独 rerun の rc=1 は「その nodeid が main でも赤」の証明ではない。[check_acceptance_reds.py:734-742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:734) は出力を検査せず rc だけで非帰属化し、プランも capture 後に再送するだけである。再現/影響: selector 本体は pass するが `pytest_sessionfinish` や session-level error が exit status 1 にした走行でも、receipt の当該 node は `rerun_rc=1`、`classification=non-attributable` となり、land 受理集合が誤って広がる。

- [M] footer 消失は設計上は rc=2 だが、テスト・変異では固定されていない。[plan.md:65-67](/work/1/SFC/tanab/dev-wave-jobs/t1027-acceptance-reds-checker/plan.md:65) の欠落・複数・未知書式禁止に対する production parser テストがなく、`test_injected_collection_failure_cannot_reach_rerun_or_status` は seam から直接 `InvalidInput` を投げるため恒真的である。再現/影響: 「footer 不在時は抽出 nodeid 数を selected とみなす」破壊を入れても列挙テストは緑のままになり、footer のない部分出力に目的 nodeidがあれば rerun rc=1から rc=0、非帰属 receipt が生成される。

- [M] M2 は二つの独立条件を一緒に無効化するため、byte 完全性の片側破壊を殺せない。[plan.md:185-188](/work/1/SFC/tanab/dev-wave-jobs/t1027-acceptance-reds-checker/plan.md:185)、[plan.md:210](/work/1/SFC/tanab/dev-wave-jobs/t1027-acceptance-reds-checker/plan.md:210)。再現/影響: `size` 比較だけを削除しても `test_dispatch_receipt_with_omitted_scheduler_stdout_fails_closed` は `omitted_bytes>0` で赤を維持する。また raw `f0 90 80` は `errors="replace"` で U+FFFD 一文字になり、元も再 encode 後も 3 bytesなので長さ一致自体も lossless の証明にならない。壊れた nodeid集合が非帰属 receipt と land 受理を生みうるため、`omitted=0,size mismatch` の独立負例と U+FFFD 拒否が必要である。

- [M] current-run receipt の設計上の束縛は妥当だが、テストと最終 receipt に証拠が残らない。nonce は [dispatch_compute.py:1354-1358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/pegasus/dispatch_compute.py:1354) の乱数と排他的 `mkdir` で、probe も [check_acceptance_reds.py:693-697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:693) ごとに新規なので、通常は同じ「hash directory」を再利用しない。一方、`test_dispatch_collection_receipt_requires_bound_request_args` は別 path しか試さず、同一 argv の receipt が二つあり一方だけ告知された競合や directory scan 変異を殺せないうえ、[plan.md:52](/work/1/SFC/tanab/dev-wave-jobs/t1027-acceptance-reds-checker/plan.md:52) で原 receipt を削除し、最終 checker receiptにもその hash・request ID・stdout hashを残さない。再現/影響: foreign receipt を選ぶ実装でもテストが緑になり、台帳上はどの collection で `non-attributable` を導いたか監査不能になる。

- [M] exit code は増えていないが、consumer 契約が scope 外のままである。[plan.md:107](/work/1/SFC/tanab/dev-wave-jobs/t1027-acceptance-reds-checker/plan.md:107) の意味は rc=0 が green または全件非帰属、rc=1 が帰属赤、rc=2 が判定不能であり、受理可能なのは厳密に rc=0 だけである。再現/影響: 将来 caller が `rc != 1` を受理すると footer 欠落等の rc=2 まで land し、さらに acceptance log hash 束縛が scope 外のままなら別走行の green rc=0 でも certified 受理集合が広がる。consumer 側で exact rc、`status=non-attributable-only`、log hash を同時検査する必要がある。

- [N] `test_truncated_relay_without_receipt_fails_closed_before_rerun` は truncation detector の試験になっていない。[plan.md:140-141](/work/1/SFC/tanab/dev-wave-jobs/t1027-acceptance-reds-checker/plan.md:140) の入力は receipt 欠落だけで既に rc=2 なので、relay header の `omitted_bytes` 解析を壊しても緑である。再現/影響: P3 の診断が旧 `no exact selector` 等へ退行しても受理集合は変わらないが、レポートの `reason` が誤原因へ変わる。

- [N] brief の relay 上限の一般化は広すぎるが、collection 修正の前提自体は壊さない。[brief.md:32-53](/work/1/SFC/tanab/dev-wave-jobs/t1027-acceptance-reds-checker/brief.md:32) に対し、[dispatch_compute.py:763-767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/pegasus/dispatch_compute.py:763) は rc=0 を 4 KiB、rc!=0 を 64 KiB にする。再現/影響: 12,098-byte の collect 成功走は切れるが同サイズの rerun rc=1 は切れないため、親の二例から全走へは一般化できない。ただし collection は rc=0 必須で、receipt 告知も relay より前なので、ここ単独では certified 受理集合を広げない。

## 総括

- NO-GO。blocker は逆向きの不変条件、delimiter の非一意写像、rerun rc=1 の過剰解釈である。
- receipt tail と footer 件数の導入だけでは「判定不能から non-attributable」を閉じ切れない。
- footer 欠落、byte 完全性、同一走行束縛には独立した production-path 変異が必要である。
- pytest は実行しておらず、指定資料と対象コードの静的検査、および UTF-8 decode 性質の確認だけを行った。