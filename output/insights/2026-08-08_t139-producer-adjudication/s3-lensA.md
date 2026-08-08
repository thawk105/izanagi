# 敵対検証結果

判定は **NO-GO**。静的検査のみで、pytest・計測は実行していない。

## 恒真性の短答

| 検査 | 判定 |
|---|---|
| 承認済み core digest | `F:<canonical path>` を caller と独立に読み、replace object を無効化した Git helper を使う限り恒真ではない。[s2-plan.md:341](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:341) [trial_registry.py:482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/campaign/trial_registry.py:482) |
| 追補の従属三つ組 | F に束縛済み core_ref と照合する関係検査自体は恒真ではない。ただし追補の値を承認する検査にはなっていない。所見 1。 |
| a03 | kind・pointer・有限区間だけでは、有限の常時通過範囲を排除できない。実質恒真化可能。所見 2。 |
| `verify_receipt` | 不一致入力は落とすので字義上の恒真ではないが、producer が作る二つの文書の自己整合しか見ない。実走 bytes/schedule には恒真同然。所見 9。 |
| 恒真 deny | 現在は追補 A 不在で意図的に全拒否。さらに a12/a13 の正本矛盾を同時に満たす exact-key 集合はない。所見 3。 |

## 所見

1. **blocker — 追補は exact-key だけで、中身を事前登録できていない**

   brief は追補の中身を別 wave とする一方、プランの物理例は各値を `{}` とし、明示した値検査は a03/a04 と「B が q に関与しないこと」だけである。[brief.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/brief.md:21) [s2-plan.md:321](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:321) [s2-plan.md:341](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:341)

   これでは a01、a02、a05〜a13 の空 object を拒否する契約がなく、時間表・待機・driver 引数・arm identity・schedule・J・q・alpha という core の必須内容を固定できない。[preregistration.md:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:320)

   **成果物影響:** schedule、J、q、primary alpha を未固定または事後選択でき、適格 cluster 集合、RF、区間、p 値、certified 選択が変わる。

2. **blocker — a03 の静的検査は恒真化を防げない**

   プランは `kind="allocation_observation"`、非空 pointer、有限な `lower < upper` を要求するだけで、直後に「定数を返す実装」「有限だが常に通る範囲」は証明不能と認めている。[s2-plan.md:353](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:353) それでもテスト計画は「constant recovery rule を reject」と過大主張している。[s2-plan.md:424](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:424)

   core は定数指標と実現値を必ず含む範囲を明示的に禁止する。[preregistration.md:347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:347) trusted metric registry、実装 source hash、raw observation からの再計算がなければこの禁止は機械化できない。

   **成果物影響:** 環境未復帰の割当てを「復帰済み」として含められ、外乱を含む TPS が RF と certified 判定へ入る。

3. **blocker — a12/a13 の正本矛盾は、正例テストでは解消しない**

   §14 は a01〜a13 を列挙する一方、凍結 §15 の gate と正例は a01〜a12 を要求する。[preregistration.md:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:320) [preregistration.md:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:404) [preregistration.md:422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:422)

   プランは a13 を選ぶ新 D が必要だと正しく認めている。[s2-plan.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:3) 合成 fixture が a13 で通っても、実装自身との整合を示すだけで凍結正本との整合は示さない。

   **成果物影響:** a13 実装では凍結 §15 の正例集合を拒否し、a12 実装では primary alpha が未束縛になるため、受理される追補と proof-chain の参照が変わる。

4. **blocker — P5 が未成立なので、必須引数を置く先はまだ「実 sink」ではない**

   プランは `_submit` を唯一の qsub 実体と宣言するが、同時に PBS 測定本体は起草不能で、空 wrapper を producer 実装済みと数えてはならないと認める。[s2-plan.md:365](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:365) [s2-plan.md:391](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:391) U3 も producer body 確定に依存している。[s2-plan.md:473](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:473)

   D235 の先例が閉じたのは、実際に certified/WAL を書く既存実体だった。単に新関数へ必須引数を付けることではない。[decisions.md:11085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/docs/decisions.md:11085) 台帳外投入が見えないことも core 自身が明記する。[preregistration.md:433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:433)

   **成果物影響:** 実行可能な pilot 経路は閉じず、または canonical producer 自体が存在しないため、投入集合・receipt・proof-chain 参照を binding 必須化できない。

5. **blocker — preflight の source authority が未定義で、過去の同型欠陥を再導入する**

   `PreregBinding` に producer/preflight の source commit はないが、PBS は「commit blob の t139_preflight.py」、テストは「binding source commit」からのロードを要求する。[s2-plan.md:85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:85) [s2-plan.md:379](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:379) [s2-plan.md:467](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:467) どの commit を意味するか定義されていない。

   さらに helper 一枚だけを commit から実行しても、import される resolver が live worktree なら束縛されない。先例は全 imported repo module の bytes を source commit と比較している。[certified_writer_preflight.py:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/campaign/certified_writer_preflight.py:85) これは実際に一度起きた欠陥である。[worklog.md:2310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/docs/worklog.md:2310)

   **成果物影響:** 正本 resolver と異なる bytes で binding を受理でき、投入集合と receipt が参照する事前登録三つ組が変わる。

6. **blocker — receipt から trace-enabled / trace-disabled 分離を再計算できない**

   `arms.*.compile` は performance arm の identity/argv しか持たず、correctness row は `trace_binary` を持つだけで、その source、compile identity、trace flag、performance binary との非同一性を結んでいない。[s2-plan.md:258](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:258) [s2-plan.md:268](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:268) 追加制約にもこの関係はない。[s2-plan.md:274](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:274)

   これは別ビルド・別 run を要求する絶対規律 1 に不足する。[CLAUDE.md:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/CLAUDE.md:58) 既存先例は trace/perf hash の相違と、verifier が trace hash を使ったことまで検査する。[artifacts.py:899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/qualification/artifacts.py:899)

   規律 2/3 についても、`correctness_anomaly` という reason code はあるが、producer body の終端動作も、構造化された anomaly/dependency record も未定義である。[CLAUDE.md:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/CLAUDE.md:67)

   **成果物影響:** trace-enabled 性能値または trace-disabled correctness 結果を正規 evidence と区別できず、TPS/RF と anomaly に基づく certified 選択が変わる。

7. **blocker — 段 A だけでは成果物へ効く権威層が閉じず、D234 とも未裁定のまま**

   プランは validator/consumer を段 C へ送るが、D234 は validator、consumer、投入 script まで producer 実装 wave の責務と明記する。[s2-plan.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:21) [decisions.md:11065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/docs/decisions.md:11065)

   一方、凍結 core は A→pilot→C の順序を要求し、D162 は独立 validator と同一呼出し consumer を権威境界とする。[preregistration.md:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:258) [decisions.md:8018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/docs/decisions.md:8018) 新 D なしに片方を選ぶことはできない。

   **成果物影響:** receipt を消費すれば producer 申告が certified 選択へ昇格し、消費しなければ certified 選択・レポート・proof-chain の値と参照は変わらない。

8. **must-fix — “closed schema” は key 閉包しか設計されていない**

   18 top-level key と nested exact key はあるが、列挙された追加制約には `schema_version` の const、ID/hash/path の型、array cardinality、ID 一意性、planned↔actual↔attempt↔allocation の参照整合性、completed/anomaly/qsub-failure ごとの条件分岐がない。[s2-plan.md:225](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:225) [s2-plan.md:274](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:274)

   core は全 attempt、実順序、allocation、correctness evidence 等を必須にしている。[preregistration.md:285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:285) `receipt_attempt_ids == intent_attempt_ids` は変異表にだけあり、publish API が読む canonical intent namespace も未定義である。[s2-plan.md:397](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:397)

   raw schema に適格性判定を入れる必要はないが、後段が「欠測」と「存在しない実行」を区別して再計算できる条件付き schema が要る。

9. **must-fix — `verify_receipt` と brief §4-6 は実走 checkout の検出を過大主張している**

   brief は「別 checkout 測定が混入する」ことを検出すると書くが、予定 API は receipt の宣言三つ組/HEAD と binding の一致しか見ない。[brief.md:44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/brief.md:44) [s2-plan.md:448](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:448)

   producer は期待された HEAD、binary hash、planned/actual schedule を同時に受領証へ書けるため、実際に使った bytes・順序・待機との一致は証明されない。これは core §15 が明示する非保証であり、T-643 でも完全偽造検出は見送り、人間確認併用と裁定済みである。[preregistration.md:433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:433) [worklog.md:3182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/docs/worklog.md:3182)

   したがって検出できるのは「二つの producer 文書の食い違い」であり、「実測 checkout の食い違い」ではない。

10. **must-fix — `declared_use_class` と correctness evidence は downstream 禁止がなければ権威化する**

   `qualification` は D162 により「審査へ提出」であって合格ではない、と言える。[decisions.md:8010](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/docs/decisions.md:8010) しかし `official` は単独では「正式用途」以上の読みを防げず、consumer が分岐に使わないことは prose だけである。[s2-plan.md:306](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:306)

   `correctness_evidence` も syntactic boolean ではないが、`outputs` の型と意味が未定義なので、producer が作った clean verdict への pointer として機能しうる。同様に `admission_telemetry.returncode`、`attempt.reason_code=completed`、`exclusivity` は raw claim であり、独立再計算なしには適格性入力にしてはならない。[s2-plan.md:263](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/s2-plan.md:263) [decisions.md:8014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/docs/decisions.md:8014)

   新 D、evidence-only の明示、そして consumer が use class や producer 出力を受理条件に使わない否定検査が必要である。

11. **must-fix — 「実装被覆 0」は権威層に限定しないと事実でない**

   既存 T139 probe は HEAD exact、replace-ref/dirty-tree 拒否、commit blob 抽出、runtime PBS hash 照合を既に行う。[t139_positive_control_probe.pbs:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/tools/pegasus/probes/t139_positive_control_probe.pbs:65) [t139_positive_control_probe.pbs:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/tools/pegasus/probes/t139_positive_control_probe.pbs:106)

   repo/CCBench/script/prereg hashes、TRACE=0 compile、実 schedule/TPS も記録済みである。[t139_positive_control_probe.sh:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/tools/pegasus/probes/t139_positive_control_probe.sh:348) [t139_positive_control_probe.sh:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/tools/pegasus/probes/t139_positive_control_probe.sh:394) [t139_positive_control_probe.sh:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/tools/pegasus/probes/t139_positive_control_probe.sh:486)

   これは engineering-screen/nonqualification で、login admission も `unknown`、trace-enabled correctness も欠くため main producer ではない。[admission_registry.json:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/tools/pegasus/admission_registry.json:58) それでも producer 機構の被覆は 0 ではない。「D162 の authoritative promotion 9 層は 0」と限定し、既存機構を partial coverage として棚卸しすべきである。

12. **nit — pin 0 件は反証できなかったが、実測記録を再現可能にすべき**

   実検索では次がいずれも 0 件だった。

   - core digest の literal hit: `output/ orchestrator/ tools/ docs/` で 0
   - canonical path の machine-source hit: `orchestrator/ tools/ hooks/` で 0
   - role-key 候補中に同 digest を持つ artifact: 0

   `FROZEN_MANIFEST` の現行 23 件にも T139 core はない。[test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/tests/test_frozen_artifacts.py:38) したがって brief の結論自体は今回は支持される。[brief.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/brief.md:28)

   ただし DW-O09 は path だけでなく role-key 側の検索と分類を要求するため、実行した query と候補分類を brief に残すべきである。[operations.md:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/docs/dev-wave/operations.md:46)

   F/HEAD/worktree の digest 一致も実測では確認できたが、これは将来不変条件ではなく現在の観測である。プランどおり F の full SHA を独立定数とし、毎回 F blob を読む必要がある。

## P1〜P5 と成果物影響表の査定

| 項目 | 敵対判定 |
|---|---|
| P1 | **blocker**。段順と D234 の実装境界を新 D で解決するまで着手不可。 |
| P2 | **must-fix**。最小照合としては可。ただし実測 checkout/bytes 検証とは呼べない。 |
| P3 | **must-fix**。新 D が必要。特に `official` を適格性として読む consumer を機械的に排除すること。 |
| P4 | 条件付き可。atomic publish 自体は既存の create-only 機構を再利用できるが、schema と canonical namespace が未完成。[atomic_publish.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-producer/orchestrator/qualification/atomic_publish.py:24) |
| P5 | **blocker**。producer body がない以上、前置・sink・registry だけを land してはならない。 |

brief §4 の各行については、1 は validator/consumer 後にのみ RF へ効く、2 と 5 は P5 未成立で閉じない、3 は proof-chain の必要入力にすぎず十分条件ではない、4 は自己申告だけでは producer 族を閉じない、6 は文書間不一致だけを検出し実測 checkout 混入は検出しない。[brief.md:35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-producer/brief.md:35)

## 総括

- **判定: NO-GO**
- **blocker: 7 件**
- must-fix: 4 件、nit: 1 件
- 最低条件は、追補の完全な値 schema、a03 の trusted 再計算、a13 裁定、実 producer body、source-module 閉包、trace/perf 証拠分離、P1 の権威境界裁定。
- pytest・測定は未実行。静的検査結果のみ。