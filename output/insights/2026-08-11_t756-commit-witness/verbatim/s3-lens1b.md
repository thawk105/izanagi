判定は **land blocker** です。静的検査のみを行い、pytest・実測・編集はしていません。

## 所見

### L1-1 — 新検査が発火する経路の有限列挙

- 主張: 新しい witness 検査が発火するのは、未評価 variant が新たに `pipeline.evaluate()` の `_run_one_pass` へ入る経路だけです。
- 根拠: [pipeline.py:841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:841)、[loop.py:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/loop.py:256)、[screening_driver.py:189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/screening_driver.py:189)、[s1_direct_comparison.py:636](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s1_direct_comparison.py:636)、[s8b_oracle_driver.py:1169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s8b_oracle_driver.py:1169)

  | 経路 | witness 導入後 | 下流 |
  |---|---|---|
  | `campaign.loop` | pipeline 経由で発火 | COMMIT・fitness |
  | `screening_driver` | pipeline 経由で発火 | screening 後の COMMIT |
  | `s1_direct_comparison` | `evaluate_fn=pipeline.evaluate` なので発火 | certified cell |
  | `s8b_oracle_driver` | `evaluate_fn or pipeline.evaluate` なので発火 | oracle outcome |
  | `s8b_floor_campaign` | `pipeline.evaluate` を使わないが correctness/certified を主張しない | 対象外 |
  | `guided.py` | verifier 自体を呼ばない | replay VERIFY/BENCH/COMMIT |
  | `silo_ladder_rung1` | CLI・直接 API とも witness なし | correctness evidence |
  | 公開 CLI・補助 coverage driver | witness なし | certified な材料 gate |

- 具体的な失敗経路: 検算したが、fresh な `s1_direct_comparison` と `s8b_oracle_driver` が pipeline を迂回する経路は見つかりませんでした。
- 深刻度: nit
- 処方: 設計文書では「pipeline を通る fresh evaluation に限った保証」と明記し、下記の bypass を同じ保証へ含めないでください。

### L1-2 — `silo_ladder_rung1` は保存済み witness を捨てて certified evidence を作る

- 主張: `silo_ladder_rung1` は同一 correctness run の `commit_counts_` を保存しているのに、witness なし verifier の `certified=True` を正式な correctness 受理条件にしています。
- 根拠: [silo_ladder_rung1.py:3936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:3936) で `run.stdout` を保存し、同ファイル [3944–3949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:3944) で witness なし CLI を実行しています。受理条件は [1115–1135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:1115)、raw 再束縛も [2842–2857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:2842) で witness なしです。実在成果物には [run.stdout:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/correctness/run.stdout:15) の `480595` と [verifier.json:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/correctness/verifier.json:13) の `txns=480595` があり、stdout は raw manifest でも hash 束縛されています。
- 具体的な失敗経路: 末尾 txn を丸ごと失い、残存 txid が密連番・DSG が acyclic の trace → CLI は stdout の大きい commit 数を読まず `certified=true` → `correctness_certified` が通り、材料レポートへ載ります。
- 深刻度: blocker
- 成果物影響: `correctness_leg.verifier.results[0].certified` と `correctness_certified` 受理集合が、完全性未確認の trace を含んだままです。
- 処方: 推奨裁定は、凍結 `verifier.json` を変えず、raw `run.stdout` を一意に parse して `stats.txns` と照合し、batch 0 も外側の再束縛 gate で要求することです。既存成果物だけで実施でき、再実測は不要です。

### L1-3 — 既存 WAL と guided replay は新 gate を一度も通らない

- 主張: verifier policy の epoch/migration がないため、既存の witness なし COMMIT は terminal skip され、guided replay からも通常の VERIFY/BENCH/COMMIT 形で再流通します。
- 根拠: [loop.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/loop.py:163)–185 は既存 terminal variant を再評価しません。[digest.py:208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/critic/digest.py:208)–233 は witness でなく `STAGE_COMMIT` だけで材料を採用します。[replay.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/replay.py:119)–150 は旧 WAL の certified/fitness を読み、[guided.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/guided.py:131)–141 はそれを VERIFY/BENCH/COMMIT として書き直します。`docs/phase3.md:258`–259 は live variant への再利用を禁止しています。
- 具体的な失敗経路: 旧 verifier が部分 trace を false-green COMMIT 済み → コード更新後も resume で再検証されない → `load_workload` または guided が旧 fitness と certified を選択材料へ残します。
- 深刻度: blocker
- 成果物影響: 既存 campaign の受理集合、winner、fitness、guided の `final_pick` は新 gate 導入後も変わりません。
- 処方: 裁定パッケージ候補は、(a) verifier-policy epoch を campaign identity に入れて再評価、または (b) witness のない COMMIT を `legacy-no-commit-witness` として現行 certified 選択から除外、の二択です。guided は replay 専用 provenance を通常 COMMIT と機械的に区別してください。

### L1-4 — 公開 CLI と補助材料 gate も witness なし certified を流す

- 主張: plan の「CLI は変更不要」は、pipeline 外の複数の correctness 材料 gate に FN-1 を残します。
- 根拠: [cli.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/cli.py:46)–68 は常に witness なしで `certified` を出力し、certified なら [81–86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/cli.py:81) で rc=0 です。これを直接使う材料 gate は少なくとも次です。

  - `s3_lock_coverage.py:110–125` → `stock_silent_certified` (`:236–238`)
  - `s5_permutation_coverage.py:106–121` → `stock_silent_certified` (`:229–231`)
  - `s8a_trigger_coverage.py:202–218` → `skeleton_certified` (`:288–305`)
  - `t152_write_intent_coverage.py:446` → certified control (`:563–585`)
  - `silo_ladder_rung1.py:3944–3949`

- 具体的な失敗経路: 各 control run の末尾 txn が消え、既存 integrity と残存 DSG が緑 → CLI が certified を返す → control の「正しい骨格が certified」という材料値が真になります。
- 深刻度: must-fix
- 成果物影響: coverage/oracle 材料の `stock_silent_certified`、`skeleton_certified` 等が、不完全 trace によって真になり得ます。
- 処方: CLI を certifying mode と legacy diagnostic mode に分けるか、各 driver に同一 run の stdout witness を渡す結線を追加するかを裁定してください。少なくとも「FN-1 を verifier 全体で閉じた」とは記述できません。

### L1-5 — per-call の受理集合は緩まないが、診断順序は変わる

- 主張: plan の論理式どおり実装すれば `New(T,E) ⇒ Old(T)` は成立し、既存の `trace-empty` と `trace-no-abort-counts` も先取りされません。
- 根拠: 現行 `certified` は [model.py:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/model.py:200)–203 で既存 `integrity.clean()` を必須にしています。pipeline の順序は [pipeline.py:860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:860)–881 で、nonzero exit → empty → abort-count → verifier です。`missing_txids` は [core.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/core.py:25)–30 にあります。
- 具体的な失敗経路: 受理集合については検算したが破れませんでした。ただし「missing txid と witness 欠落」または「parse error と batch 非ゼロ」が共存すると、新 guard が verifier より前に返るため、拒否自体は維持されても旧診断は発火しません。
- 深刻度: nit
- 処方: matching witness を付けた既存 integrity-red 入力も拒否される対照テストを足し、`clean()` の新条件が既存条件への純粋な conjunction であることを固定してください。

### L1-6 — `parse_bench_stdout` は correctness witness 用には曖昧です

- 主張: `parse_bench_stdout()` は同一 label の重複を last-write-wins で潰すため、witness の一意性を保証しません。
- 根拠: [benchparse.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/calibrator/benchparse.py:20)–36 は辞書代入のみで重複を記録しません。対して ladder の parser は [silo_ladder_rung1.py:798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:798)–803 で main/batch 各 1 行を要求しています。
- 具体的な失敗経路: stdout に `commit_counts_=2` と後続の重複 `commit_counts_=1`、batch 0 があり、trace が 1 txn → 辞書値 1 と observed 1 が一致 → 曖昧な stdout が certified になります。
- 深刻度: must-fix
- 成果物影響: pipeline の受理集合に「複数の相矛盾する witness 行を持つ run」が残り、WAL には選ばれた一方だけが記録されます。
- 処方: correctness 用 parser は main/batch 各 exactly-one を要求してください。欠落・重複・非整数・負数を別々に殺す control が必要です。

### L1-7 — witness は独立ではなく、親 brief の「構造的に厳密」も反例があります

- 主張: `commit_counts_` は trace 外の有用な corroboration ですが、同じ実行体・commit 経路に依存するため failure-independent witness ではありません。
- 根拠: trace stream は [trace.hh:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/external/ccbench/include/trace.hh:53)–61 で open 結果を検査せず、C 行書込みも [78–82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/external/ccbench/include/trace.hh:78) で状態を検査しません。一方、Silo は [transaction.cc:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/external/ccbench/cc/silo/transaction.cc:584)–596 で C を出し、YCSB は成功後に [ycsb.hh:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/external/ccbench/include/ycsb.hh:161)–167 で counter を増やします。stdout は [result.cc:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/external/ccbench/common/result.cc:47)–50 です。
- 具体的な失敗経路:

  - trace file の open/write が failbit になっても例外・rc に反映されない → counter は増えるが C 行は落ちる。この反例により brief の「構造的に厳密」は成立しませんが、新 gate はこの故障を正しく拒否します。
  - 実際の commit に対し C 出力と counter 更新が同時に欠落する common-mode failure → expected と observed が同じ小さい値 → 残存 DSG が acyclic なら certified のままです。

- 深刻度: must-fix
- 成果物影響: `integrity.commit_witness.delta=0` が trace 完全性の完全証明として読まれると、certified claim が実際より強くなります。
- 処方: 「独立 witness」ではなく「trace 外 counter による個数 corroboration」と記述し、common-mode と count-preserving corruption を非検出限界として明記してください。検査した成果物中、より独立した exact commit 数 field はありません。`throughput[tps]` も同じ total counter から導出され、`stats.txns` は trace 由来です。

### L1-8 — 新しい拒否理由と commit mismatch が下流の診断層で欠落します

- 主張: plan は pipeline の拒否までは閉じますが、critic と S8b report の reason 契約、および cycle 共存時の integrity 表示を更新していません。
- 根拠: [digest.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/critic/digest.py:238)–269 は `verify` payload のない abort を `load_rejections` から除外します。liveness reason の閉集合は [digest.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/critic/digest.py:116)–122 で新理由を含みません。S8b の閉集合も [s8b_abort_reason_contract.py:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s8b_abort_reason_contract.py:18)–24 にありません。また verdict は cycle を先に選ぶ [model.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/model.py:194)–197 一方、renderer は [digest.py:604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/critic/digest.py:604)–628 で non-serializable 時に integrity を表示しません。
- 具体的な失敗経路:

  - commit witness 欠落 → early abort に `verify` payload なし → critic では structured rejection にならず、S8b driver では unknown abort reason → protocol violation に化けます。
  - expected 3 / observed 2 だが残存 DSG に cycle → WAL には commit witness がある一方、材料 report は cycle だけを表示 → trace 不完全性が CC anomaly に隠れます。

- 深刻度: must-fix
- 成果物影響: critic の rejection 種別、S8b oracle row の outcome、材料レポートの原因帰属が変わります。
- 処方: 両新理由を digest の liveness reason/hint と S8b の `VERIFY_INCONCLUSIVE_ABORT_REASONS` に追加してください。renderer は verdict にかかわらず `integrity.clean=False` を併記し、既存 `trace-empty` 等の早期 payload にも取得済み witness を残すべきです。

### L1-9 — 出力形状の pin は親 brief が挙げた 1 件より多い

- 主張: conditional serialization 方針は正しいものの、`result_to_dict`／`Integrity` 形状の等値・byte pin の consumer inventory は未完です。
- 根拠: 静的列挙結果は次のとおりです。

  1. closed key schema: [silo_ladder_rung1.py:1425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:1425)–1446
  2. raw verifier dict と final JSON の完全一致: 同 [2835–2837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:2835)
  3. raw trace からの `result_to_dict` 再計算と verifier envelope の完全一致: 同 [2842–2857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:2842)
  4. evidence test の直接辞書一致: [test_silo_ladder_rung1_evidence.py:1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1060)–1064
  5. raw file 全体の SHA-256 byte 束縛: [silo_ladder_rung1.py:2558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/silo_ladder_rung1.py:2558)–2604 と attempt receipt の `:2648–2666`; 実在 `verifier.json` hash は [raw-manifest.json:1656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/raw-manifest.json:1656)
  6. `Integrity` key の独立 mirror と完全一致: [test_t152_write_intent_coverage.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_t152_write_intent_coverage.py:27)–49、`:760–795`

  現在の evidence test は JSON literal byte 比較ではなく deserialize 後の辞書比較です。byte-level pin は raw manifest の SHA で、plan の新しい専用 byte regression は追加価値があります。

- 具体的な失敗経路: `commit_witness` を no-witness 出力へ無条件追加 → closed schema、再計算 equality、evidence test が赤になり、再生成した raw file は frozen SHA とも一致しません。
- 深刻度: must-fix
- 成果物影響: 凍結 `correctness/verifier.json` の hash、raw/final 等値、ladder evidence の参照可能性が変わります。
- 処方: この全一覧を consumer inventory に入れてください。ladder の完全性 gate は既存 verifier JSON の中へ key を追加せず、L1-2 の外側比較に置くのが最小です。

### L1-10 — FN-2 の完全解決が submodule 権限外という認定は正しい

- 主張: txn ごとの期待 R/W 件数または終端 marker が trace に存在しない以上、FN-2 の完全で一般的な解決には producer/schema 変更が必要です。
- 根拠: schema は [trace.hh:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/external/ccbench/include/trace.hh:17)–23 に件数・終端を持ちません。YCSB は key を復元付きで選ぶ [ycsb.hh:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/external/ccbench/include/ycsb.hh:55)–75 一方、Silo は同一 key の read/write を [transaction.cc:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/external/ccbench/cc/silo/transaction.cc:211)–219、`:529–547` で集合へ畳みます。したがって `ycsb_max_ope × commits` から trace R/W 行数を厳密には復元できません。
- 具体的な失敗経路: C と少なくとも 1 本の R/W は残るが、その txn の他の R/W が落ちる → commit 数は一致し、行数の正しい期待値も Python 側にはない → cycle 辺が消えた acyclic trace が certified になります。
- 深刻度: nit
- 処方: full FN-2 は新 pin 承認込みの裁定パッケージへ返す判断でよいです。Python-only では「現行 YCSB の C-only txn 拒否」や最終行 newline 検査という部分防壁は可能ですが、true v2 や FN-2 完了と記録してはいけません。

### L1-11 — 変異 1 と 11 は計画どおりの実装では生き残ります

- 主張: 変異候補 1〜11 のうち 1・11 は期待テストを落とさず、3・4・10 は帰属が一意ではなく、6 は fixture 値に条件があります。
- 根拠: plan は witness があれば fields を常に設定し、比較条件は notes 用としています (`s2b-plan.md:22–54`)。変異表は同 `:340–356` です。

  | # | 検算結果 |
  |---:|---|
  | 1 | **survive**。`len(txns) != expected` を恒偽にしても、fields は observed=1 / expected=2 のままで `clean()` が赤にするため、予定テストは落ちません。 |
  | 2 | kill。新しい `clean()` 節そのものを消すので missing-file control が偽緑になります。 |
  | 3 | kill するが非一意。既存 orphan/missing/version 等すべての integrity テストが先に殺し得ます。 |
  | 4 | kill するが、専用 byte test だけでなく既存 ladder schema・recompute equality も落ちます。 |
  | 5 | kill。structured dict の delta 完全一致が直接検出します。 |
  | 6 | **条件付き**。producer test で trace C 行数と stdout commit 数を意図的に異ならせないと、`n` 代入が同値になり survive します。 |
  | 7 | kill。guard を抜けると optional API が旧緑になります。 |
  | 8 | kill。batch は verifier が見ないため guard 無効化で緑になります。 |
  | 9 | kill。keyword を消すと tail-loss が no-witness 旧緑になります。 |
  | 10 | main/batch の値が相異なれば kill。ただし全 suite では後段 batch guard も落ちるので「producer test だけ」の帰属ではありません。 |
  | 11 | **survive**。一致時に mismatch-note 条件を反転しても fields は equal、notes は gate に不関与なので negative control は certified のままです。 |

- 具体的な失敗経路: 変異 1 または 11 を投入 →予定 nodeid は緑 → mutation matrix が「新 gate の比較を kill 済み」と誤記録します。
- 深刻度: must-fix
- 成果物影響: mutation matrix と正しさ proof chain の kill 判定が過大になります。
- 処方: #1 は `observed_commits = expected_commits` への変異、#11 は `clean()` の `==`/`!=` 反転へ置換してください。#6 は `trace_c_lines != stdout_commit_count` を fixture で明示し、重複 stdout と「matching witness + 既存 integrity-red」も変異対象へ足してください。

### L1-12 — 5-tuple と二つの独立 Optional は取り違え・部分状態を作りやすい

- 主張: main/batch を含む 5-tuple と別々の Optional fields は、同程度に小さい named representation より明確に脆いです。
- 根拠: plan の位置契約は `s2b-plan.md:97–117`、現行コード直後には既に frozen dataclass の [_BenchResult:288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:288) があります。また plan は片側だけの witness を unclean とする一方 (`:42–54`)、`delta` serialization の部分状態を定義していません (`:60–75`)。
- 具体的な失敗経路:

  - main N / batch 0 の位置を consumer が逆展開 → 全正常 run が `trace-batch-commits-unattributed` になります。
  - `expected_commits=2, observed_commits=None` → `clean=False` だが、`delta=observed-expected` は例外になるか witness key が隠れ、構造化 abort が失われます。

- 深刻度: must-fix
- 成果物影響: pipeline の受理集合と abort reason、WAL の structured witness が位置・部分状態により変わります。
- 処方: 隣接 precedent に合わせた frozen `_TraceRunResult` dataclass を keyword 構築・属性参照で使うのを推奨します。部分 witness は serializer を total にして `delta=None` を定義するか、atomic な witness object で both-or-none を保証してください。

### L1-13 — `batch_commit_counts_ != 0` は現行の緑構成を赤にしない

- 主張: pinned Silo/YCSB の現行ソースでは `local_batch_commit_counts_` を非 0 にする writer がなく、batch 非ゼロ拒否で受入全走が赤になる証拠はありません。
- 根拠: counter は [result.hh:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/external/ccbench/include/result.hh:19) で 0 初期化され、[result.cc:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/external/ccbench/common/result.cc:437)–438 と `:685–689` は集約するだけです。YCSB 成功経路が増やすのは main counter のみです ([ycsb.hh:161–167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/external/ccbench/include/ycsb.hh:161))。現行 legacy/S2 flags に batch 指定もありません ([pipeline.py:96–127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:96))。凍結実例も [run.stdout:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/correctness/run.stdout:16) で 0 です。
- 具体的な失敗経路: 検算したが現行 pinned source では作れませんでした。将来 batch writer を持つ protocol を接続した場合だけ、意図どおり fail-closed になります。
- 深刻度: nit
- 処方: 非ゼロ拒否は維持してよいです。stock legacy/S2 の batch=0 control を固定し、将来 batch protocol を受ける際は trace 帰属の別裁定にしてください。

## 総括

現状のままの land は止めるべきです。blocker は次の二つです。

1. `silo_ladder_rung1` が、実在して hash 束縛済みの `run.stdout` witness を使わず正式な correctness evidence を certified にする。
2. 既存 WAL の witness なし COMMIT が terminal skip・guided replay を通じて現行選択へ残るのに、epoch/migration 方針がない。

一方、fresh な pipeline evaluation については、受理集合が緩まないこと、`s1_direct_comparison` と `s8b_oracle_driver` が同 gate を通ること、現行 batch 値が 0 であることは静的に確認できました。

land 前の最低条件は、ladder の外側 witness gate、旧 WAL の扱いに関する裁定、stdout 一意性検査、下流 reason 契約、変異 1/11 の差替えです。FN-2 の完全解決は submodule/pin 裁定へ返す認定で妥当です。