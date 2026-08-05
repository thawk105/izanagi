# 監査結果

**判定は NO-GO。** 現行プランの関係テストは、production で到達しない trace を fixture で生成して赤を作る。さらに秘密依存の実行結果を公開入力 `P` に入れて固定しており、実装後の緑を非干渉の根拠にはできない。

## BLOCKER

### B1 — baseline-red が到達不能な fixture による人工物である（M4 反証）

- **(a) 壊れるもの:** 「現行 baseline の実漏洩で赤くなり、射影で緑になる」という検査の生死。実際には injected `drive` と偽 renderer が不可能な結果を返すから赤くなる。
- **(b) 根拠:** プランは `do_build=False` で S 依存の `diffq_variant_id` と digest marker を強制し、`make_critic_digest` 自体を fake に置換する（[plan.md:132](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:132>)、[plan.md:136](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:136>)、[plan.md:141](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:141>)）。しかし実 driver は quarantine と auditor が通れば no-build を `dry-pass, variant=None` にする（[p3_s4_loop_trigger_gating.py:553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:553)）。no-build では digest も生成しない（[同:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:748)）。既存 fixture の auditor は常に `pass` である（[p3_autonomous_workload_trial.py:453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:453)）。プラン自身が同型の「no-build なのに certified/digest」を不正 fixture として削除対象にしている（[plan.md:266](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:266>)）。
- **(c) 最小是正:** variant の関係テストは、固定した auditor reject を実 driver に通して到達可能な diff-quarantine trace を作る。digest は別に admitted WAL fixture と実 `make_critic_digest` を使い、fake renderer と任意 marker を禁止する。baseline-red はこの二つの実経路で記録する。

なお、WAL のない fallback は variant しか登録しないのに、偽 digest は別の `src_token` sentinel まで射影しようとしている（[plan.md:60](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:60>)、[plan.md:140](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:140>)）。未知 ID を拒否する規則どおりなら実装後も緑にならず、fake が特別扱いすれば検査が恒真化する。

### B2 — `P` に S 依存の観測結果を入れており、非干渉条件が循環している

- **(a) 壊れるもの:** identity 以外の経路で最大 5 bit を漏らしても検査が緑になる。これは前 wave が却下した「現行の許可 field を公開と呼ぶ」循環を再導入している。
- **(b) 根拠:** `P` に outcome、verdict、metrics、stop reason、rejection class/reason/count を含める（[plan.md:112](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:112>)）。前裁定はこの定義を明示的に自己参照として却下した（[s4-adjudication.md:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-05_t244-p2-noninterference/s4-adjudication.md:51)）。production では metrics は harness outcome から作られ（[p3_autonomous_workload_trial.py:705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:705)）、digest は空/非空、anomaly、key/version、liveness extra、reason、件数を描画する（[digest.py:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:580)、[同:588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:588)、[同:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:624)、[同:669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:669)）。
- **容量:** S は 5 bit なので、全残余の合計上限は世代ごとに 5 bit。空/非空だけで最大 1 bit、3値 verdict で最大 `log2(3) ≈ 1.585 bit`、5 metrics の None パターンだけで最大 5 bit、32通りの count または metric tuple があれば 5 bit 全部を運べる。これは容量評価であり、現行 mapping の実測値ではない。
- **(c) 最小是正:** `P` は S より前に決まる入力と random coins のみに限定する。公開したい outcome/reason/metrics は明示的な declassification 関数 `D(S,trace)` として別定義し、`D` 以外の sink bytes を比較する。「同じ outcome を fixture が返す」は代用にならない。

### B3 — U-1 の origin-scope ID を実装していない。裁定違反である（M6）

- **(a) 壊れるもの:** 「U-1 実装済み」という D96・phase・worklog の記録。campaign-local ordinal は origin-scope identity ではない。
- **(b) 根拠:** 裁定正本は origin scope の不透明 ID を要求する（[worklog.md:765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/worklog.md:765)）。authority は実際に `origins: []`（[reflux_origin_authority_v2.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_origin_authority_v2.json:1)）。プランは campaign 初出順ラベルへ置換し（[plan.md:49](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:49>)）、自ら「origin scope ID ではない」と認めている（[plan.md:77](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:77>)）のに、phase へ U-1〜U-3 実装済みと記録する予定である（[plan.md:29](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:29>)）。
- **残余容量:** cap=1 で適格候補が必ず一つなら `candidate-0001` 自体は 0 bit。ただし候補の有無は無条件には最大 1 bit。cap-lift 後、ラベル列は候補の同一性 partition を保存する。G 世代で最大 `log2(B_G)` bit、すなわち G=2,3,4,5 でそれぞれ `1, 2.32, 3.91, 5.70 bit` である。候補数と再出現順もこの partition から復元できる。
- **(c) 最小是正:** authority entry を発行して origin に束縛するか、ユーザー裁定を取り直して U-1 を campaign-local pseudonymization に縮小する。現裁定のまま代用品を U-1 として land してはならない。

### B4 — `(campaign_id, label)` の逆引きは一意でない

- **(a) 壊れるもの:** critic 表示から trusted WAL／report の実 ID を監査する経路。no-build fallback では逆引きの正本自体がない。
- **(b) 根拠:** プランは `(campaign_id,label)` で再解決可能と主張する（[plan.md:64](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:64>)）。一方、関係テストは固定 P のまま fresh `run_root` を32個作る（[plan.md:129](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:129>)）。campaign ID の preimage は config と trial を含むが run root を含まない（[ident.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/ident.py:125)、[p3_autonomous_workload_trial.py:530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:530)）。したがって同じ `(campaign_id,candidate-0001)` が32個の異なる raw ID を指す。trial ID を変えれば今度は P が固定されていない。さらに no-build fallback には、逆引き手順が要求する `STAGE_BUILD_START` がない。
- **(c) 最小是正:** trusted 側のキーに immutable な run identity/report hash を加え、`(run_id,campaign_id,label) → raw IDs` の mapping commitment を永続化する。WAL がない fallback を許すなら report bytes と mapping を明示的に束縛する。

### B5 — declassification 会計が「省略可能かつ自己申告」である

- **(a) 壊れるもの:** auditor への diff/digest 開示を「明示的に会計した」という保証。新 producer が account を落としても legacy として受理され、改変 account も開示 bytes から独立再検証できない。
- **(b) 根拠:** プランは field 欠落を旧 v2 として許すが schema version を上げない（[plan.md:202](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:202>)）。現 completeness は `input_payload_sha256` の形式しか検査せず（[autonomous_trial_completeness.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/autonomous_trial_completeness.py:183)）、report の preview からは `working_diff` が除かれる（[p3_autonomous_workload_trial.py:1586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1586)）。よって後段 verifier は `/working_diff` の value hash を再計算できない。正式 cross-binding は現在も未実装（[phase3-8c-preregistration.md:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/phase3-8c-preregistration.md:212)）で、C10 evaluator も UNSATISFIED を返す設計である（[s8c_preregistration_evidence.py:493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/s8c_preregistration_evidence.py:493)）。
- **(c) 最小是正:** report/event を v3 に上げ、v3 auditor attempt では account を必須化する。v2 のみ欠落を許す。canonical provider payload bytes またはその不変参照を保存し、completeness が pointer 値、value hash、payload hash、policy hashを独立再計算する。

## MAJOR

### M1 — M1 の build 側と「毎世代 5 bit」は未実測である

- **(a) 壊れるもの:** build/source/admission 全経路まで現行漏洩が実証済みという一般化。
- **(b) 根拠:** read-only probe の実測は diffq が 32/32 一意、wire literal 0/32。build-like も32/32だったが、probe は実 `src_token` ではなく predicate SHA-256 を代入している（[probe_codebook.py:31](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s1/probe_codebook.py:31>)）。実 no-build pass は `variant=None` なので漏洩量は 0 bit。したがって brief の「毎世代 5 bit」は成立せず、正しくは `I(S;ID | path) ≤ 5 bit`、diffq 単射かつ一様時のみ 5 bit である。
- **(c) 最小是正:** 実 source materialization、source token、admission receipt、build-start WAL を使う32点の非コンパイル fixtureを追加するか、build 経路を未実測として主張から除外する。

### M2 — digest 再描画が tag／reflux ablation の同値性を固定していない

- **(a) 壊れるもの:** 元 artifact と critic 向け再描画の差が identity 射影だけ、という前提。既定引数を使うと tag が変わり、将来 reflux-off で赤節を再混入できる。
- **(b) 根拠:** 元 driver は `tag=CRITIC_TAG` と実 config の reflux 値を渡す（[p3_s4_loop_trigger_gating.py:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:748)）。一方 `make_critic_digest` の既定値は `tag="p3-s4", reflux=True`（[p3_s4_loop.py:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:276)）で、プランの再実行記述は両引数を固定していない（[plan.md:19](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s2/plan.md:19>)）。fake renderer の関係テストではこの差を検出できない。
- **(c) 最小是正:** 二度目の独立呼出しを避け、driver が同じ admitted view から raw artifact と projected sink を生成する。最低でも tag/reflux を明示的に引き回し、実 renderer で on/off 双方について「identity 箇所以外は byte-for-byte 同一」を検査する。

### M3 — M5 の「pin がないから provenance 影響なし」は成り立たない

- **(a) 壊れるもの:** 成果物影響の説明。byte golden がなくても attempt journal、report hash、registry snapshot は変わる。
- **(b) 根拠:** `FROZEN_MANIFEST` が s1/s8b の23件だけなのは確認できる（[test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_frozen_artifacts.py:38)）。しかし `_invoke` は critic payload bytes を `input_payload_sha256` に入れ（[p3_autonomous_workload_trial.py:922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:922)）、report は journal 全体を hash する（[同:1378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1378)）。trial registry も journal hash を扱う。現状の8c成果物は正式 proof chain ではない（[phase3-8c-preregistration.md:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/phase3-8c-preregistration.md:122)）ため、「proof chain の現在値は変わらない」という brief の文言は根拠がない。
- **(c) 最小是正:** 「凍結 pin なし」と「provenance 不変」を分離する。変更される payload hash、journal hash、report hash、registry snapshot、raw/projected digest の対応を影響表に列挙し、正式 chain は未成立と明記する。

### M4 — 名乗りが実装内容を超えている

- **(a) 壊れるもの:** 研究成果物上の安全主張。
- **(b) 根拠:** 前裁定は正しい関係検査がない限り「P2 の部分実装」「非干渉検査」を名乗らないとした（[s4-adjudication.md:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-05_t244-p2-noninterference/s4-adjudication.md:57)）。今回の検査は B1/B2 によりその条件を満たさず、U-1 も未履行である。
- **(c) 最小是正:** 未修正で land する場合に名乗れるのは「8c critic 境界の campaign-local ordinal pseudonymization regression」「auditor disclosure metadata producer」「IR source/golden change detector」まで。`origin-scope ID`、`noninterference`、`indistinguishability`、`P2 部分充足`、build/WAL/digest end-to-end、cap-lift、proof-chain 保全は名乗らない。

## MINOR

### m1 — M3「既存被覆は key-set だけ」は事実ではない

- **(a) 壊れるもの:** 新規検査の純増検出力に関する説明。
- **(b) 根拠:** 既存テストは key-set だけでなく、wire/mask の不在、schema 値、metrics の exact 値・None、単位変換を検査している（[test_p3_autonomous_workload_trial.py:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:584)、[同:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:614)、[同:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:831)）。不足しているのは S を変える関係検査であって、値検査全般ではない。
- **(c) 最小是正:** M3 を「既存テストには S-dependency の関係 oracle がない」へ縮小する。

## NIT

### n1 — U-3 golden hash の preimage 記述が byte-level で曖昧

- **(a) 壊れるもの:** 別実装者が同じ preimage を再構成できるという契約。
- **(b) 根拠:** plan の `69d827...` は golden の raw 25–56 行を、先頭空白・末尾 comma・LF 込みで連結した hash だった。AST の「tuple node source」を `ast.get_source_segment()` で連結すると静的実測は `ffc20e...` になり一致しない。source 全体の `3d9cdc...` は現ファイルと一致した。
- **(c) 最小是正:** 「AST node」ではなく、開始・終了 byte offset、indent、comma、改行を含むかを規範化し、preimage length も固定する。

## 総括

- **NO-GO。**
- 最大理由は、到達不能な no-build trace と fake renderer で baseline-red を人工生成していること。
- outcome・metrics・rejection 情報を `P` に入れる定義は循環であり、最大 5 bit の残余を検査しない。
- campaign-local ordinal は裁定済みの origin-scope ID ではない。
- `(campaign_id,label)` の逆引きは複数 run root と no-WAL fallback で成立しない。
- declassification account は v2 で省略可能かつ開示 bytes に cross-bind されていない。
- 未修正で「非干渉」「U-1 実装済み」「P2 部分充足」を研究成果物へ記載してはならない。
- pytest は実行しておらず、緑は主張しない。