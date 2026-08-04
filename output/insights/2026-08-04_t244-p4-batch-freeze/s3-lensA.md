## 所見一覧

### A-01 — oracle/golden 凍結条件の誤判定

**real / blocker**

独立 golden を実装前に凍結し SHA-256 を記録する計画なのに、brief は `DW-O08/O09/O10` を不成立としています。[brief.md:55](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/brief.md:55) [s2-plan.md:152](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:152) [s2-plan.md:166](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:166)

少なくとも `freeze / oracle gate` に触る `DW-O08` は成立します。dispatcher は、段1後にこれが判明した場合、brief・plan・review を invalidate し、段1から再実行して旧成果物を流用しないよう命じています。[dev-wave.md:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/.claude/commands/dev-wave.md:26) [dev-wave.md:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/.claude/commands/dev-wave.md:90)

再発型は F27 `[恒真ゲート][テスト代表性]`、F39 `[誤前提][防壁の射程誤認]`。

**影響:** 無視すると certified 選択・材料レポートの値は直ちには変わらないが、台帳へ「先行凍結済み独立 oracle」という無効な監査参照が入る。

### A-02 — `DW-G04` を名称変更だけで迂回している

**real / blocker**

`DW-G04` は既存 artifact path または計測 ID を書けない条件付き機能を設計メモに留めます。[core.md:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/dev-wave/core.md:57) 一方、親 (P2) は production path が存在せず test だけが consumer だと認めながら、「機械部品 + golden」と呼んで実装対象へ移しています。[brief.md:32](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/brief.md:32)

実 production では現在も outcome・stop reason が generation record、critic payload、report へ直接流れます。[p3_autonomous_workload_trial.py:1486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/p3_autonomous_workload_trial.py:1486) [p3_autonomous_workload_trial.py:1492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/p3_autonomous_workload_trial.py:1492) 新 leaf の開示 gate はこれらに一度も発火しません。D149 の P1 固有先例は、`DW-G04` の一般例外を定めていません。

再発型は F21/F72 `[恒真ゲート]`、F60 `[テスト代表性]`。

**影響:** certified 選択・report・試行台帳の実受理集合は不変なのに、台帳上だけ「P4 用防壁が増えた」と誤認できる。

### A-03 — distinct mask set は採用済み query 会計を表現できない

**real / blocker**

プランは batch を重複禁止の set とし、5-bit wire を辞書順に並べます。[s2-plan.md:7](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:7) したがって最大32 memberで、replicate、query ordinal、実行順を commitment に持てません。

しかし採用済み予算は `Q >= 1 + 32R + E_min` で、32候補を `R` 回測定した query 全件を数えます。[worklog-phase3-0804-161.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/archive/worklog-phase3-0804-161.md:24) [worklog-phase3-0804-161.md:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/archive/worklog-phase3-0804-161.md:30) プラン自身も「origin の全 query slot を表せない」と認めています。[s2-plan.md:226](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:226)

同じ candidate set・policy は別 replicate/session でも同じ digest になり、結果の差し替え・再利用を識別できません。

**影響:** 台帳の cardinality と Q 消費が実 query 数より小さくなり、P3/P4 を誤って充足扱いすると cap-lift の受理集合が広がる。

### A-04 — 「事前 commit」は外部結果取得に対して恒真

**real / major**

`record_result()` が受けるのは caller 自己申告の digest・member・二値 outcome だけです。[s2-plan.md:83](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:83) caller は leaf 外で結果を取得した後に `freeze()` し、その結果を直後に投入できます。FSM が証明するのは「`record_result` の呼出しが `freeze` より後」だけで、「verifier/build/query の結果が freeze 後に生成された」ことではありません。

golden と提案テストはいずれも API 呼出し順だけを見るため、この実装は全テストを通り得ます。プランが許す名乗りも実際には「freeze 前結果投入拒否」に限定されています。[s2-plan.md:45](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:45)

**影響:** 現行成果物は不変だが、この codec/FSM を事前 commit の証拠に数えると proof chain と cap-lift 台帳の P4 値が偽陽性になる。

### A-05 — partial abort が seal の抜け道になる

**real / blocker**

親 (P4) とプランは、部分結果を得た後でも `abort()` を成功させ、`sealed/aborted` receipt を公開し、新 session を作ることを許しています。[brief.md:37](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/brief.md:37) [s2-plan.md:33](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:33) [s2-plan.md:95](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:95) [s2-plan.md:228](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:228)

abort 判断が部分 outcome に依存すれば、`complete | aborted`、seal 時刻、次 session の有無が結果依存チャネルになります。残 member の tombstone と公開 transcript 長固定もありません。これは設計本文の「早期停止時は残 slot を tombstone として消費し transcript 長を固定」に反します。[README.md:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/output/insights/2026-08-01_t244-reflux-design/README.md:284)

**影響:** 台帳は未実行 slot を消費済みと証明できず、abort receipt を安全な seal と受理すると Q no-refund と結果非公開の受理集合が広がる。

### A-06 — `Kmax` gate は origin-total 会計を閉じず、参照値も任意

**real / blocker**

D121 の `Kmax` は `reflux-origin` 全体の公開 class 総数です。[decisions.md:5788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/decisions.md:5788) 設計本文も I/Q/K を origin ごとの総予算として定義しています。[README.md:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/output/insights/2026-08-01_t244-reflux-design/README.md:270)

プランはこれを各 `BatchSession` の caller 注入値として扱い、条件は `Kmax >= 0` だけです。[s2-plan.md:21](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:21) session を作り直せば毎回予算が新品になります。さらに公開 class は任意の64桁 hexで、referent の実在・意味・完全性を保証外としています。[s2-plan.md:27](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:27) [s2-plan.md:55](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:55) `Kmax=1` でも任意 SHA 文字列自体に256 bitを符号化できます。

**影響:** report・ledger の class 公開量が実際より小さく計上され、cap-lift の情報会計と受理集合が不正に緩む。

### A-07 — golden と実装の所有分離が brief 内で破れている

**real / blocker**

brief は実装子1単位に「leaf + golden + test」の全所有を与えています。[brief.md:23](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/brief.md:23) これは D149 の「G が golden を書く → 親が hash 凍結 → 別の E が実装」という順序・所有分離に反します。[decisions.md:7295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/decisions.md:7295)

プラン側は G/E 分離へ修正していますが、親 brief の worker dispatch は未訂正です。[s2-plan.md:156](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:156) [s2-plan.md:168](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:168) このままでは一人の実装子が期待値を実装へ追随させられます。

再発型は F27 `[恒真ゲート][テスト代表性][手順漏れ]`。

**影響:** literal digest が一致しても独立 oracle ではなくなり、材料レポート・台帳の「独立 golden」参照が虚偽になる。

### A-08 — golden の独立導出に必要な規範 bytes が未定義

**real / major**

plan は key 名を列挙しますが、`policy.minimum_cardinality` が入れ子 key か dotted key か、新 `schema_id` の literal、receipt/disclosure の exact field・wire 表現を固定していません。[s2-plan.md:8](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:8) [s2-plan.md:68](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:68)

一方、G は `reflux_ir.py` を読むことも禁止されます。[s2-plan.md:156](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:156) しかし member schema literal と正確な wire 文法は同ファイルにあります。[reflux_ir.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_ir.py:19) [reflux_ir.py:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_ir.py:99)

「段4で逐語固定する」は必要条件の先送りであり、現 plan のまま golden は導出不能です。[s2-plan.md:154](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:154)

**影響:** 任意解釈を hash で固定しただけの golden になり、テストは自己整合しても report・台帳の oracle 参照が規範を証明しない。

### A-09 — 採用済み U-D と矛盾する非第一級分岐が残る

**real / major**

brief erratum と canonical worklog は U-D=`batch 第一級`を確定しています。[brief.md:67](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/brief.md:67) [worklog.md:1333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/worklog.md:1333)

それにもかかわらず plan は「U-D が非第一級の場合」の digest-only trusted-control 経路を正規分岐として残しています。[s2-plan.md:37](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:37) [s2-plan.md:40](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:40) これは U-E の committed bytes 照合、U-F の authority floor を落とす実装経路になり得ます。[worklog.md:1336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/worklog.md:1336)

再発型は F31 `[手順漏れ]`、F67 `[誤前提][ドリフト]`。

**影響:** origin ledger が canonical bytes・cardinality・policy を持たず digest だけを受理し、P3/P4 の参照閉包が欠落する。

### A-10 — 変異事前登録候補は KILL 会計に使えない

**real / major**

`M05` は「cardinality または minimum_cardinality の削除」、`M09` は「subset または非空へ弱化」で、各行が複数の非等価 operator を含みます。[s2-plan.md:208](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:208) [s2-plan.md:212](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:212) 新規ファイルなので一意な old anchor もなく、手前の同一拒否や第一失敗理由をコードで確認できません。これは `DW-M01` の単一理由性に未達です。[mutation.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/dev-wave/mutation.md:5)

また、結果-before-freeze guard の削除、`record_result` が outcome を返す変異、partial abort topology、origin-total Kmax の reset、class referent 偽装を撃つ operator がありません。reject-all・accept-all・空 handler を落とすという説明は、実テストも変異実走もない現時点では検出力証拠ではありません。

再発型は F28 `[恒真ゲート][テスト代表性]`、F60 `[テスト代表性]`、F86 `[恒真ゲート]`。

**影響:** mutation 台帳が偽 KILL・過大な fault-class 被覆を記録し、材料レポートの検出力参照だけが強く見える。

### A-11 — 「純増検出力 = テスト全部」は過大会計

**real / minor**

brief は同性質の既存テストがないことから「本 wave のテスト全部」を純増検出力としています。[brief.md:51](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/brief.md:51) しかし D149 は入力点・test 数ではなく独立系譜と fault class で数えると決定しています。[decisions.md:7330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/decisions.md:7330)

golden AST、parser rejection、dual import の型は既存 `test_reflux_ir.py` にあります。[test_reflux_ir.py:204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_ir.py:204) [test_reflux_ir.py:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_ir.py:282) P4 三点セットの新しい被覆は存在し得ますが、「全テスト」を独立検出力として加算はできません。

**影響:** certified 選択・受理集合は変わらないが、材料レポートと変異台帳の検出力件数が過大になる。

## 反証不能だった主張

- `reflux_ir.py` に `parse_wire`・`encode_wire`・`emit_predicate` と5-bit閉集合が存在する。
- tracked tree に `reflux_batch.py`、`BatchSession`、`batch_commitment_sha256` 等の P4 三点セット実装は存在しない。同性質の既存テストも検索では発見できなかった。`s8b_prediction_runner` に既知 cell 集合と `seal()` の近縁機構はあるが、結果の逐次 journal 開示を持つため P4 の独立 oracle ではない。
- `MAX_APPROVED_GENERATIONS = 1` と三入口の generation 拒否は現存し、本 plan は cap-lift・production へ未結線である。[p3_autonomous_workload_trial.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/p3_autonomous_workload_trial.py:134) [p3_autonomous_workload_trial.py:249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/p3_autonomous_workload_trial.py:249)
- 設計どおり実装される限り、空 batch・singleton・floor 欠落、公開 API 経由の frozen member 追加、partial complete-seal は例外で拒否する構成になっている。
- reject-all・accept-all・常時同一 disclosure は、記載された正例と post-seal positive control が実コードになれば落ちる。ただし未実装・未実走なので KILL は未確認。
- current worktree は clean、`main...HEAD` は `0/0` だった。
- brief erratum 後の「U-D 第一級」「P4 無条件義務」「P4 未充足」の状態は canonical worklog・D150 と一致する。

## GO・NO-GO

**NO-GO。**

A-01だけで dispatcher 上、現 brief・plan は invalidate され、段1から再実行が必要です。旧 brief・plan・本 review を流用して段4へ進めません。

また、再起動後も A-02、A-03、A-05、A-06、A-07 が未裁定のままなら実装へ進めません。P4 は引き続き `FAIL`、承認上限は1のままです。

## 総括

P4 三点セットの既存実装不在という親の中心実測は反証できませんでした。しかし現 plan は、API 呼出し順を外部の事前 commit と取り違え、distinct mask set を query batch と取り違え、abort と per-session Kmax に抜け道を残しています。さらに golden 凍結条件と所有分離が wave 規律に違反しています。

型タグについて、現行 `docs/failures.md` では自己ハッシュ改変は F27、空証明は F36、commit hash の自己参照は F38です。依頼文の「F36 hash 自己参照」に相当する型も含め、F27・F28・F31・F36・F38・F39・F60・F67・F72を検査しました。

read-only を維持し、ファイル変更・pytest・変異実走は行っていません。