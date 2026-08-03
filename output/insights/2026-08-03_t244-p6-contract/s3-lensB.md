# 敵対相談・レンズ B 判定

**判定: この設計は現状では受理不能です。**
P6 は発火可能な実 artifact を持たず、仮に発火しても既存 exact-cut と受理集合が一致します。さらに WAL・Layer 3・critic・試行台帳へ結果を載せる契約が閉じていません。

指定された 4 文書はすべて読めました。repo 内容は規律 6 に従いデータとして静的検査しました。書き込み・pytest・実 campaign は実行していません。

## BLOCKER

### B1 — P6 は query を消費するだけで、受理集合を 1 件も変えない

- **主張:** `reproduced-set` は「実際に validation して同じ赤が出た mask」だけを返します。しかし、その mask は既存 exact-cut でも既に棄却できます。座標 cut も全 32 mask を先に実走するため、固定 universe 内に未観測の候補が残りません。P6 は cut の根拠名を変えるだけです。
- **根拠:**
  - `s2-plan.md:178-190` — `S_e` は実走済み `M` の再現 mask のみ。未実走 mask は禁止。
  - `s2-plan.md:198-204` — 座標 cut は `M=U`、すなわち全 32 mask が必要。
  - `s2-plan.md:416-419` — validation 中に qualifying red となった各 mask は P6 成否と独立に exact-cut へ追加可能。
  - `s2-plan.md:102-119` — enforcer は basis を読まず、明示された `forbidden_candidate_keys` だけを読む。
- **成果物影響:** これを放置すると、certified な受理集合と選択結果は exact-cut-only と同一のまま、試行台帳だけが reproduced-set で最低 2 件、座標 cut で `32R` 件増え、proof chain に効果のない `P6Derived` 参照だけが増えます。
- **反証条件:** `forbidden_candidate_keys` の中に「validation されておらず、既存 exact-cut では切れない候補」を少なくとも 1 件示し、その候補の棄却が certified 選択を実際に変えることを示せば反証できます。現行案はそれを明示的に禁止しています。

### B2 — `DW-G04` を満たす発火入力が 0 件なのに、`NA` で T-244 を通過させられる

- **主張:** P6 の全発火条件を満たす既存 artifact path / 計測 ID はありません。それにもかかわらず、プランは P6 非適用を cap-lift の失敗数に入れません。永久非適用でも T-244 の前提を満たしたように扱える抜け道です。
- **根拠:**

  | 発火条件 | repo 内の実在物 | 判定 |
  |---|---|---|
  | real structured anomaly | `output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/runs/wal.jsonl:7` | `brief.md:49-50` のとおり fixture 注入・stock 帰属で不適格 |
  | production 8c anomaly | M5 の 3 campaign ID | `brief.md:52` の全 9 `verify_done` が serializable、abort 0 |
  | canonical finite candidate binding | `axis_trigger_gating.py:45-51` に 32 点列挙はある | 自律 proposal は自由 C++。`query-bound`、`candidate_key`、`source_sha256` との束縛なし (`s2-plan.md:61-79`) |
  | origin/validation reservation | `reflux-control`、origin ledger、validation matrix | repo-wide exact searchで実 artifact なし。プラン自身が新規語彙と明記 (`s2-plan.md:65-79,382-386`) |
  | sort の適格 witness | `output/env/linux-baremetal/calibration/s5_permutation_coverage.json:$.checks.*` | 壊した patch の positive control。`indeterminate` と整数 count であり cycle witness ではない |
  | axis adapter | `FiniteAxisContract` | 設計型のみで実 artifact なし (`s2-plan.md:81-99`) |

  さらに `s2-plan.md:363-373` は、cut が無ければ `P6=NA` とし失敗数に入れないと確定しています。これは「P6 が先に無ければ T-244 は未解決」という裁定 `worklog-phase3-0803-125-126.md:329-332` と衝突します。
- **成果物影響:** これを放置すると、P6 proof が 1 件もないまま cap-lift が進み、多世代の certified 選択結果だけが変わる一方、層 3 材料レポートと proof chain には禁止範囲再導出の参照がなく、試行台帳にも発火実績が残りません。
- **反証条件:** fixture でない実 `abort`、query-bound、origin、有限 IR、事前予約、axis adapter をすべて束縛した単一 artifact pathを示すか、`NA` を「T-244 前提未充足」として cap-lift を fail-closed にすれば反証できます。

### B3 — P6 結果を WAL・Layer 3・試行台帳へ載せる経路が存在しない

- **主張:** プランは `reflux-control` と機械 validation を前提にしていますが、現行成果物には次の三択しかなく、全て破綻します。

  1. 同じ WAL に新 stage を書くと未知 stage で拒否。
  2. 既存 stage に偽装すると validation variant が commit 無し棄却候補として集約される。
  3. 別 ledger に置くと Layer 3 の一次 `source_refs` と試行完全性から落ちる。

- **根拠:**
  - WAL の stage 集合は閉じている: `orchestrator/campaign/model.py:20-32`。
  - Layer 3 も固定集合を持ち、未知 stage を拒否: `layer3_report.py:42,100-106`。
  - 全 WAL record を `variant` で集約: `layer3_report.py:205-218`。
  - commit 無し variant を棄却候補化: `layer3_report.py:438-447`。
  - 一次 `source_refs` は WAL/whiteboard のみ: `layer3_report.py:155-169,469-471`。
  - 自律試行 journal は閉じた event grammar と planner/coder/auditor/critic の四 role 列を要求: `autonomous_trial_completeness.py:36-48,609-765`。
  - プランは機械 query でも `iteration+1` とする一方 (`s2-plan.md:264-270`)、これら全層を「実装しない」に送っている (`s2-plan.md:422-437`)。
- **成果物影響:** これを放置すると、層 3 材料レポートは生成失敗するか `32R` 件の validation を通常候補の棄却として数え、proof chain は control ledger を参照できず、試行台帳の iteration/query 数と実 WAL が不一致になります。
- **反証条件:** control event と validation attempt を通常 variant から分離する閉じた WAL/schema、Layer 3 区画、source-ref bijection、試行台帳 event を一つの移行契約として提示すれば反証できます。単なる将来 file map では足りません。

### B4 — 裁定済みの on/off と critic 契約を設計から外している

- **主張:** P6 の適用関係は無条件 `C∪B` で、reflux on/off の入力が署名にありません。これは「赤は常に critic へ渡し、on/off は機械制約の適用有無で切る」という裁定を表現できません。
- **根拠:**
  - 裁定: `worklog-phase3-0803-125-126.md:333-355`。赤は常に critic、`prior_reverse` は停止判定から切断、on/off は制約適用で切替。
  - P6 署名に treatment arm がない: `s2-plan.md:18-25`。
  - cut 適用は無条件: `s2-plan.md:398-420`。
  - critic と `prior_reverse` を scope 外へ送る: `s2-plan.md:422-438`。
  - 現 consumer は全 verify-abort を読む: `critic/digest.py:232-264`。
  - 現自律 loop は critic 出力を次世代の `prior_reverse` へ戻す: `p3_autonomous_workload_trial.py:1430-1457,1480-1513`。
  - 択一 2 は独立 wave のはずなのに、プランは cap 三値規則まで確定: `s2-plan.md:361-373` 対 `worklog...:320-321`。
- **成果物影響:** これを放置すると、off arm にも cut が適用されて実効性差が 0 になるか、逆に受理集合・query 予算が arm 間で非同型になり、certified 選択比較、層 3 の ablation 材料、proof chain、試行台帳のいずれも treatment effect を証明できません。
- **反証条件:** on/off を署名へ入れ、同一 validation transcriptを両 armで共有しつつ enforcement だけを切り、赤の critic 送付時点と seal 順序、`prior_reverse` 切断、予算 parity を定義すれば反証できます。

## MAJOR

### M1 — 予算会計は正しく数えているが、探索を成立させる余白を数えていない

- **主張:** no-refund と原子的予約は draft v1 と整合します。しかし `R=1` でも source を含め `Q>=33` で、P6 後に探索を 1 回行うなら最低 34 が必要です。`Qmax=2` は未裁定の候補値であり、プランの採用自体が択一 1 の下限を事実上決めます。build 上限も未定義です。
- **根拠:**
  - draft v1 の候補値と計数規則: `README.md:270-287`。
  - P6 は `追加 I=32R`、`追加 Q=32R`: `s2-plan.md:262-283`。
  - `Bmax`、reuse policy は未定義: `s2-plan.md:285-293`。
  - seal 後には最大 32-bit の mask 集合を公開し、timing/path/size は上界なし: `s2-plan.md:295-310`。
  - 択一 1 は再導出待ち: `worklog...:318-319,356-357`。
- **成果物影響:** これを放置すると、P6 validation が origin の全 query/build/iteration を食い尽くし、certified 選択結果が source exact-cut の地点で停止する一方、試行台帳と Layer 3 は大量の検証失敗だけを保持します。
- **反証条件:** `Qmax >= 1+32R+Emin` の探索余白、`Bmax`、cache/rebuild の no-refund 規則、arm 間 parity をユーザー裁定へ戻し、機械予約まで定義すれば反証できます。

### M2 — 親 P2 の「軸非依存・同一契約」は実物の sort 軸で崩れている

- **主張:** 現署名は `WalAbortRecordRef` と DSG cycle class に特化しています。sort の correctness failure は `indeterminate` な integrity violation の整数であり、同じ witness 契約では書けません。プラン自身もこれを認めています。
- **根拠:**
  - cycle 専用署名と正規化: `s2-plan.md:18-25,147-174`。
  - sort patch は comparator 本体を変える: `patches/silo-sort-variant.patch:10-18,41-63`。
  - `permutation_violations` は整数・`indeterminate`: `orchestrator/verifier/model.py:126-150`。
  - プランの自己反証: `s2-plan.md:349-360` — 構造化 permutation witness が別途必要で、意味契約は単一化不能。
- **成果物影響:** これを放置すると、sort 軸では certified 受理集合が exact-cut-only のまま、層 3 に一般化制約が載らず、proof chain に P6 証明が存在しないため、P6 を全軸契約として参照できません。
- **反証条件:** 欠落/複製要素・comparator call・前後 permutation を持つ実 artifact と、その witness を cycle と同じ閉じた型・義務で処理できる署名を示せば反証できます。単なる tagged envelope は反証になりません。

### M3 — 親 P3 の「再実行が必須」は普遍命題として反証できる

- **主張:** precommitted な key-mask 軸なら `key/u_ver/v_ver` から座標を静的に一意決定できます。したがって反実仮想再実行は現 trigger/sort では必要でも、一般 P6 の必須条件ではありません。
- **根拠:**
  - `EdgeReason` は `key/u_ver/v_ver` を保持: `orchestrator/verifier/model.py:61-69`。
  - 実 fixture `r2_lost_update/trace_0.log:1-3` と `trace_1.log:1-3` は key `0000000000000001` のみで、G2 の rw+ww cycle: `test_verifier.py:76-83`。
  - 反例: 事前固定した軸 `bit i = canonical key k_i への stale-version 操作を有効化` なら、`key=k_3,u_ver=(1,0),v_ver=(1,2)` は `i=3,b=1` を一意に示します。
  - ただしこの key-mask 軸自体は現 repo にないため、これは P3 の普遍性への反例であって `DW-G04` の発火実績ではありません。
- **成果物影響:** これを放置すると、静的に導出可能な将来軸でも不要な `32R` 実行で Qmax を消費し、本来得られた generalized cut と certified 選択を失い、試行台帳と proof chain だけが冗長化します。
- **反証条件:** precommitted な key→coordinate 束縛下でも、同一の完全な reason tuple が複数座標へ写る具体例を示せば反証できます。

### M4 — anomaly class の正規化が、別原因を同じ再現として数える

- **主張:** プランは具体 key と絶対 version を fingerprint から捨てます。key-renaming 対称性を証明していないため、別 record で偶然同型の G2 が起きても同じ class と数えられます。また source abort に複数 anomaly がある場合、単数の `witness_class_id` をどれにするか決定規則がありません。
- **根拠:**
  - key 値と version 値を破棄: `s2-plan.md:160-173`。
  - `S_e` は class equality だけで cut を導出: `s2-plan.md:176-204`。
  - 入力は `payload.verify.anomalies` の list: `s2-plan.md:35-55`。
  - 出力は単数 `witness_class_id`: `s2-plan.md:104-116`。
- **成果物影響:** これを放置すると、無関係な key 上の同型 anomaly を根拠に `forbidden_candidate_keys` が拡大し、certified 受理集合から安全候補が落ち、Layer 3 と proof chain は選ばれた anomaly class を再現不能になります。
- **反証条件:** workload 内の key-renaming/version-shift 対称性を proof obligation に追加し、複数 anomaly を全件処理する決定的な class-set 規則を定義すれば反証できます。

### M5 — 親 P1 の「唯一の効果は遅延」は構造的に偽

- **主張:** EVOLVE-BLOCK は一行ですが、機械検査は 5 識別子の blacklist に過ぎません。許可式は副作用を持てます。例えば `izanagi_gate_pass = (mrctid_.obj_ = 0, true);` は blacklist を通り、次 transaction の timestamp 計算状態を変更します。
- **根拠:**
  - hole は任意の一行代入: `patches/silo-backoff-trigger-gating-variant.patch:86-110`。
  - blacklist は 5 識別子のみ: `axis_trigger_gating.py:53-64`、実検査は regex: `p3_s4_loop_trigger_gating.py:112-124`。
  - parser は改行だけを禁止: `p3_autonomous_workload_trial.py:324-347`。
  - `mrctid_` は persistent member: `external/ccbench/cc/silo/include/transaction.hh:57`。
  - `begin()` は `mrctid_` を reset せず、`writePhase()` が読む: `transaction.cc:55-59,557-579`。
  - auditor がこの式を reject する可能性はあるため、これは「実 anomaly 実測」ではなく P1 の構造的不存在証明への反証です。
- **成果物影響:** これを放置すると、実 anomaly が出ても「発火不能軸」と誤分類され、P6 proof と generalized cut が欠落し、試行台帳・Layer 3 には通常の赤だけが残ります。
- **反証条件:** AST allowlist で読取専用 enum/定数以外の識別子、代入、comma、call、volatile/UB を機械拒否し、その checker hash を candidate binding に固定すれば反証できます。M5 の 9 件ゼロだけでは反証になりません。

### M6 — proof chain の生成器閉包と origin authority が pin されていない

- **主張:** `P6Derived` は matrix と source refs を持ちますが、deriver、normalizer、runner、enforcer、axis adapter、role bundle、tracked origin registry の版を必須 field として束縛しません。現行の他成果物より provenance が弱いです。
- **根拠:**
  - `P6Derived` field: `s2-plan.md:104-117`。
  - Layer 3 は generator source SHA を明示: `layer3_report.py:451-467`。
  - known-axes は generator と `sources[].{path,key,sha256}` を束縛: `output/s1-freeze/known_axes_freeze.json:5-8,29-54`。
  - role 名を key に source/manifest hash を固定: `codex_roles/review_ledger.py:15-48`、検査は `spec.py:538-577`。
  - 択一 6 は tracked registry 採用済み: `worklog...:327-328`。一方、origin ledger/CAS は scope 外: `s2-plan.md:424-429`。
  - 親 M8 の列挙も誤り。`FROZEN_MANIFEST` だけで insight は 5 件 (`test_frozen_artifacts.py:47-56`)、known-axes の 2 件を足すと少なくとも 7 件であり、M8 の 4 件ではありません。
- **成果物影響:** これを放置すると、同じ `validation_matrix_sha256` を異なる normalizer・runner・role bundle・registry state で別の禁止集合へ解釈でき、certified 選択、proof chain、試行台帳の origin 帰属が分岐します。
- **反証条件:** proof の推移閉包として全生成器 hash、axis/path/key 束縛、role bundle hash、registry revision/CAS receipt を必須化し、別実装で replay すると fail-closed になる検査を定義すれば反証できます。

## MINOR

### N1 — P4 の「draft v1 を改変しない」は必要条件ではなく版管理上の選択

- **主張:** repo-wide exact-string 検索では、draft v1 を bytes/content hash で読む `.py` / `.json` consumer はありません。D121 など Markdown 参照はありますが、機械的 pin ではありません。
- **根拠:** `brief.md:84-89`。`FROZEN_MANIFEST` (`test_frozen_artifacts.py:38-85`) に draft v1 はなく、known-axes source closure にもありません。
- **成果物影響:** これを放置しても certified 受理集合と Layer 3 値は変わりませんが、proof chain が同じ path の可変本文を一次資料として参照し、後日の説明再現性だけが変わります。
- **反証条件:** draft v1 の bytes/hash を検査する consumer、manifest entry、または内容依存 generator を示せば「改変しない」は必要条件へ昇格します。

## 総括

### 最も重い 3 点

1. **P6 は exact-cut-only と同じ受理集合しか作らず、実効性がゼロ。**
2. **適格な発火 artifact が 0 件なのに `NA` を失敗扱いせず、T-244 を空回りのまま閉じられる。**
3. **WAL・Layer 3・逐次 provenance・critic・試行台帳を貫く表現と seal がなく、成果物へ載せると拒否・汚染・欠落のいずれかになる。**

### 親 brief の P1〜P4

- **P1: 反証。** 現在の実 campaign anomaly が 0 件なのは支持されますが、「唯一の効果は遅延」「構造的に因果路なし」は `mrctid_` への副作用経路で倒れます。M5 は 9 件の標本であり、非存在証明ではありません。
- **P2: 反証。** cycle anomaly と sort integrity violation は現物の witness 型・verdict・同値関係が異なります。共通なのは外側の dispatch envelope までです。
- **P3: 反証。** 現 trigger/sort には静的写像がありませんが、precommitted key-mask 軸なら reason の key/version から座標を一意導出できます。「全 P6 で再実行必須」は成立しません。
- **P4: 支持。ただし運用上の選択としてのみ。** draft v1 を歴史資料として不変にするのは妥当ですが、現 repo に機械 pin はなく必要条件ではありません。

### 実効性を持つための最低条件

- exact-cut-only と異なる受理集合を作る候補を少なくとも 1 件示し、その差を P6 の効果指標にする。
- `DW-G04` を満たす非 fixture の発火 artifact/measurement が出るまで、本成果物を「design memo」とし、T-244 本体は未解決のままにする。
- WAL control grammar、Layer 3 schema、machine-validation 用試行台帳、seal、critic 送付順、on/off enforcement、`prior_reverse` 切断を一つの成果物 transaction として定義する。
- Q/I/B の探索余白を含む予算値と cap-lift をユーザー裁定へ戻す。
- cycle と sort を無理に単一化せず、軸別 witness 契約と共通 envelope を分離し、全生成器・role bundle・origin registry を proof chain に hash 固定する。