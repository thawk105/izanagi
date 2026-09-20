# [T-2153] 意味 witness の残件 (c) — `BACKOFF_REQUESTED_US` を 4 箇所同時観測 (transaction.cc 2 + backoff.hh 2) で登録簿へ (枝選択 21 → 22)

- 日付: 2026-09-20
- branch: `worktree-dev-wave-t2153-witness-requested-us` (base = local main `482f19b88`、fresh worktree。wave 中に main `800178b39` へ ff)
- 実装 commit: `cfab7a2f26fe13d01638c0e63c70c8cca306a922` (Codex `role=author` の実装 1 巡を所有 path 限定で統合、統合は親。段 6 レビュー 2 本とも must-fix 0 で fix 巡なし)
- 対象: `orchestrator/campaign/condition_meaning_gate.py` (複数 file 宣言 `_CONDITIONAL_BRANCH_COMPANION_SITES`、深い鏡像 shadow の複数 file 書出し、箇所識別 marker、`site_observations` / `companion_sources` の evidence と再検証、登録簿 +1)、`orchestrator/tests/test_condition_meaning_gate.py` (+323 行)
- 前 wave: `output/insights/2026-09-20/t2153-witness-bc/README.md` (18 → 21、D2182)、`output/insights/2026-09-19/t2153-witness-6/README.md` (15 → 17、D2161)、entry 1195 / 1704 / 1745 の残件表
- 専用 handoff / job dir: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2153-witness-requested-us/` (prompt・log・patch・probe・login / compute cell 原本・変異台帳。repo には逐語と要約だけ)

## 1. 依頼と守った裁定

依頼は「[T-2153] (P2、残件 (c) の 1 件) 意味 witness の `BACKOFF_REQUESTED_US` を 4 箇所同時観測 (transaction.cc 2 + backoff.hh 2) で登録する — 1 macro に複数 file の箇所群を宣言し同じ shadow で計装する拡張。着手直前の local main から fresh worktree。一次資料 `output/insights/2026-09-20/t2153-witness-bc/README.md` (D2182、entry 1745) と同 wave の手順 (Codex author = D95、実 patch 木 + official 同形供給で login と計算ノードの実 TU で実走、変異 = 正例と負例、期待 node 完全一致)。所有 TU 2 箇所だけの部分登録は採らない。SS2PL 系 4 件 (T-2737 §7 待ち)・探索 loop 配線・offline 供給・admission 永続化・S2 再走は含めない。既存 stock / template の pre-image は byte 一致、規律 2 を緩めない。仮想リスク向けの gate・検査・台帳・一般化は scope 外」(逐語は `verbatim/T-2153-origin.md`)。

守った裁定: D1490 (主張は所有 TU の枝選択まで)、D1491 (旧宣言経路は BACKOFF_FIXED 固定)、D1492 (配線は admission が成果物へ載る driver だけ → 本 wave は driver を配線しない)、D1613 (header は深い鏡像で所有 TU の文脈で観測)、D2161 (実 TU 実測で登録、代表 1 本にしない)、D2182 (全箇所観測、主張は DefineSpec patch の逐語箇所)、規律 2 (受理集合は狭まる向きだけ)。設計判断は本 wave の decisions fragment (slug `witness-multifile-sites`、land の fold で D 番号が付く)。`patches/` は触っていない (stock / template の pre-image は byte 一致)。

## 2. 何を変えたか (設計)

| 要素 | 機構 |
|---|---|
| 宣言 | 主 entry は既存 2-tuple のまま `("cc/silo/transaction.cc", "#if BACKOFF_REQUESTED_US")` + `_CONDITIONAL_BRANCH_SITE_COUNTS` に 2。副 file は新 mapping `_CONDITIONAL_BRANCH_COMPANION_SITES = {"BACKOFF_REQUESTED_US": (("include/backoff.hh", "#if BACKOFF_REQUESTED_US", 2),)}`。`_declared_site_count(macro)` = 主宣言 file の N (意味不変、S1 fixture helper の consumer を壊さない)、`_declared_total_site_count(macro)` = 和 (REQUESTED_US = 4) |
| 計装 | 主 + 副を各々 no-follow capture し、file ごとに N_i 箇所を計装。file ごとの箇所数不一致は既存 reason `compile-time-branch-site-count-mismatch` (detail に file 名、expected / observed は数値文字列)。**複数 file macro に限り**各箇所に固有 marker `IZANAGI_COMPILE_TIME_BRANCH_SITE_{SELECTED,COMPLETED}(f<i>s<j>)` を総数 marker の隣に挿入し、preprocess argv に token 貼り付けの `-D…(k)=…_OBSERVED_##k` 2 本を足す (単 file macro の argv は不変) |
| shadow | `_write_shadow_owner_source` は `{source_rel: text}` の mapping で全計装 file を書く。浅い鏡像は「主 == owner TU かつ副なし」に限り、副があれば深い鏡像 (D1613)。全計装 file を symlink 作成対象から除外 (symlink 越しの write で元 source を書かない) |
| 判定 (順序固定) | (1) 総数: 期待 (N·v, N) の N を総数に (非識別 → `…-not-discriminating`、不一致 → `…-selection-mismatch`)。(2) 複数 file macro だけ、箇所ごとに要求 (1,1) / 対照 (0,1) と和 = 総数を新 reason `compile-time-branch-site-observation-mismatch` で要求。総数が相殺する入力 (owner 2 箇所を外側 `#if 0` で殺し、pragma once 無しの header を 2 回展開 → (4,4)/(0,4)) を (2) が拒否する |
| evidence | 複数 file macro の green にだけ `companion_sources` (登録順 tuple、row = source_rel / start_directive / site_count / source_sha256 / source_file (計装に使った `CapturedFileEvidence`)) と `site_observations` (全宣言箇所 × 両腕、row = source_rel / site_index / requested_{selected,completed} / default_{selected,completed}) の 2 key。既存 dataclass に field を足さない、`proof_kind` 不変、単 file macro の evidence dict は不変 |
| 再検証 | 副宣言の有無は `record.macro` から登録簿で決める (record の key から決めない)。副宣言ありなら 2 key 必須、なしなら unexpected。row の型・key 集合・順序・登録値 (exact int、bool 拒否)・`source_file` の type / relative_path / sha256 / identity 等値、site 集合 (登録簿から導出)・各 row (v,1)/(0,1)・和 = 総数・両腕 argv の site marker define 存在 |
| 主張範囲 (docstring) | "Twenty-two"。副 file の証拠は「宣言した owner TU と当該 configure の include 文脈」に限り、同 header を include する他 TU (ycsb_silo.cc 等) の枝選択は主張しない |
| 不変 | 既存 21 entry の値・順序・2-tuple、reason / detail 逐語、計装本文、argv、evidence key 集合、`DefineSpec` / `DEFINE_SPECS`、旧宣言経路 (BACKOFF_FIXED 固定 5 箇所)、CLI 引数、`_run_process` の spawn site 1、B-4 目録 49、S1 helper (主 N のまま、複数 file 対応済みとは主張しない) |

配線しなかった driver: `backoff_requested_us` (`_require_requested_us_condition_gate_before_measurement` の返り値を 1107〜1111 で捨てる)、`backoff_sweep` (非 FIXED は declaration=None、preflight 返り値を捨てる)、`screening_driver` (返り値を捨てる)。段 3 B の driver 表で、登録だけで REQUESTED_US の受理が変わる公開 driver は無く、自動追随する公開入口は CLI だけ。

## 3. 前提実測 (段 1、production CLI、main 482f19b88、login pegasus02、official 同形供給、pin e9e477ca1)

- 静的 (`verbatim/nest-static-analysis.out.txt`、現行 pin + fixed → requested-us の重ね順 = driver と同じ): `#if BACKOFF_REQUESTED_US` の逐語は transaction.cc L11 (top) / L157 (`#if BACK_OFF` 内) + include/backoff.hh L109 / L141 (top) = 4 箇所、他 file に無い。header は `cc/silo/include/transaction.hh:9` → `../../../include/backoff.hh`、`#pragma once`。前 wave (pin 511c953) と同じ行番号。
- 現行 gate: REQUESTED_US 1 vs 0 = supply green / meaning **unestablished** (`meaning-witness-undeclared`) / admitted、未確立 [BACKOFF_REQUESTED_US]。対照 SORT / NOINLINE (header 宣言の既存例) = green (1,1)/(0,1)、RUNG1 = green (2,2)/(0,2)。
- `CCBENCH_BACK_OFF` の CMake 既定は 1 (既定供給で abort() 内の箇所も活性)。
- pin 閉包: gate module / test の bytes を pin する台帳・凍結物は 0 件 (契約 pin = 集合 22 / 23・順序・schema・docstring "Twenty-two"・spawn 目録 1・B-4 49 はあり、全部追随)。編集面重複 (byte 一致版、claude 19 + codex 20 worktree): なし。
- 生死実験 (`verbatim/probe-site-token.out.txt`、g++ 11.4.0): `-D'…SITE_SELECTED(k)=…_OBSERVED_##k'` で箇所ごとの token が 1 行ずつ出る、`#pragma once` で 2 回 include しても 1 回、コメント / raw string 内は展開されず数えられない (D1490 の構造的 fail-closed を保つ)。

## 4. 実 TU の実測 (最終 production 登録簿 cfab7a2f2、official 同形供給、pin e9e477ca1)

| 構成 (木 / macro / 要求 vs 対照) | login (pegasus02) | 計算ノード (bnode016) |
|---|---|---|
| ccbench-e9e477c-requested-us (fixed → requested-us) / BACKOFF_REQUESTED_US / 1 vs 0 | supply green、meaning **green (4,4)/(0,4)**、admitted、未確立 []、site_observations 4 row (transaction.cc 0/1、backoff.hh 0/1) すべて (1,1)/(0,1) | 同 |
| 同 + `-DCCBENCH_BACK_OFF=0` | supply green、meaning **red `compile-time-branch-selection-mismatch`** expected (4,4)/(0,4)・observed (3,3)/(0,3)、admitted=False | 同 |
| sort / SORT_VARIANT / 1 vs 0 (既存、浅い鏡像 N=1) | green (1,1)/(0,1) | 同 |
| fixed / BACKOFF_NOINLINE / 1 vs 0 (既存、深い鏡像 N=1、header 宣言) | green (1,1)/(0,1) | 同 |
| rung1 / IZANAGI_SILO_LADDER_RUNG1 / 1 vs 0 (既存、浅い鏡像 N=2) | green (2,2)/(0,2) | 同 |

login と計算ノードで 5 cell とも前処理 digest・byte 数・owner TU sha・closure digest・counts・compiler (g++ 11.4.0)・`site_observations` が完全一致 (差は driver-id に出力 dir 名を含めた request_digest とその派生、一時 path)。green record の `companion_sources[0].source_sha256` は実木の `include/backoff.hh` の sha256 と一致、`source_sha256` は `cc/silo/transaction.cc` と一致。両腕の preprocess argv に総数 marker 2 define + site marker 2 define。

**I1 (既存 macro の不変):** SORT / NOINLINE / RUNG1 の record (supply・meaning・admission) を変更前 (main 482f19b88) と変更後 (cfab7a2f2) で同 driver-id・同 configure で leaf 比較 (`verbatim/compare-i1-login.log`): key 集合 (再帰) と安定値 25+27+3 field (前処理 digest・bytes・source sha256・closure digest・counts・define_value・reason・proof_kind・request_digest) が同一。差は `record_digest` (row 0,1) と `admission_digest` (row 2) だけで、一時 path (`/tmp/izanagi_condition_supply_*`、`/tmp/izanagi_compile_time_branch_*`) を含む argv とそれから派生する ID の差 (段 6 レビュー A が配列 index を保った全 leaf 比較で独立確認: identity の値に差は無い)。**他 18 macro の record bytes 同一は主張しない** (浅い鏡像 N=1 / N=2、深い鏡像 N=1 の代表 3 cell + key / field pin + 同一 code path の回帰 test)。

## 5. 主張の境界 (正直に書く)

- witness が確立するのは D1490 / D2182 のまま「宣言した owner TU (`cc/silo/transaction.cc`) を当該 configure で前処理したとき、DefineSpec patch の逐語 4 箇所 (transaction.cc 2 + include/backoff.hh 2) すべてで、define の値が枝の選択を決めている」まで。副 file の証拠はその include 文脈に限り、同 header を include する他 TU (ycsb_silo.cc 等) や header 単体の意味は主張しない。動的到達性・枝本文・runtime の `requested_us = realized_us` の成立は主張しない。
- 4 箇所の活性は configure に依存する。abort() 内の箇所は `#if BACK_OFF` の内側で、`BACK_OFF=0` では completed 3/4 で red (fail-closed、実測)。`BACK_OFF` を companion define にはしない (検査する configure を変えてしまう)。
- 箇所識別 (per-site marker) は複数 file macro に限る。単 file macro (既存 21) は総数で足りる (.cc の TU は再展開されず、header 単 file は N=1 で重複が総数に出る) ので計装・argv・record を変えない。
- 受理集合: REQUESTED_US 1/0 は unestablished admit → green admit / red reject。非対値 (1/None、1/1、0/0、0/1) は factory None のまま (test で固定)。他 macro に red / unestablished → green へ転じる入力は作っていない (段 6 A が変更前後の AST 比較で確認)。
- 公開 driver の JSON / receipt は本 wave では取得していない。「未確立一覧が縮む」のは CLI cell (login + 計算ノード) で実証した範囲であり、B-10 の数値成果物や `backoff_requested_us` の材料を再認証しない (driver は admission を捨てる、D1492)。
- 単体 test の正例は合成 fixture (owner TU → 中継 `cc/silo/include/transaction.hh` → `../../../include/backoff.hh`、`#pragma once`、owner の 1 箇所は `#if BACK_OFF` 内、両腕に無条件本文、CMake mapping は fixture 内で局所追加) + 実 compiler。実 TU の緑は §4 の CLI cell が担う。
- schema 再検証は整合した両側偽造 (row と `CapturedFileEvidence` の sha256 を同じ別値にし record digest も再生成) を検出しない — 現行主 source と同じ境界であり、issuer 契約 (D1491 の capability) と区別する。

## 6. 段ごとの所見 (要点)

- 段 2 plan (12 call、379 s): P1/P2/P4/P5 採用、**P6 に補正** — 総数一致だけでは「owner 2 箇所を `#if 0` で殺し + pragma once 無しの header を 2 回 include」で (4,4)/(0,4) が相殺成立する反例 → 複数 file macro に限る箇所識別を提案。m3 は個別検査導入後は「未 include を通す欠陥」の単独検出にならない、m4 → m4′ (個別観測の無効化)、m5 は欠落 key を受理する条件へ具体化、2 回 include の期待は 6/4 (8/4 は 3 回)。
- 段 3 consult A (正しさ境界、9 call): must = 個別観測を evidence に保存し再検証まで閉じる (A1)、m3 の帰属 (A2)、相殺の反例は成立 (A3)、副 file 証拠は owner TU の include 文脈に限る (A4)、I1 の主張範囲は実測 cell に限る (A7)。refuted = 副 mapping による factory / 旧経路の拡大 (A5)、2 file 計装による argv 比較 / supply closure の破れ (A6、ただし全計装 file を symlink 対象から除く条件)。
- 段 3 consult B (過剰・削除・pin、18 call): must = fixture の CMake mapping 欠落 (`condition_gate_test_support.py` の固定 `_OPTIONS` に REQUESTED_US が無い → `macro-not-supplied`、B1)、I1 の実証範囲 (B3)、箇所識別は仮想リスク向け一般化ではない (B5、維持)、研究前進は CLI の観測証拠に限定 (B7)。nit = NOINLINE 特例 assert は緩めない・patch 束縛は header×2 + owner×2 の完全列挙 (B2)、reason は既存を再利用し file 名は detail (B3-P3)、全 21 件の serialization 固定期待 test と header 戻し注入 test は削れる (B4)、brief の記録訂正 (B6: bytes pin 0 件と契約 pin を分ける、B-4 は 49、t316 probe は FIXED gate を実呼出し)。driver 表: 登録だけで受理が変わる公開 driver は無し。
- 段 4 裁定 (`verbatim/ruling.md`): 上記を全件採用 (m6 を最小 matrix から削る案だけ不採用)。plan v2 (a)〜(i)、変異 m0〜m8 事前登録、実 TU 完了条件。
- 段 5 author (Codex、27 call、814 s): 所有 2 file に実装、sandbox で pytest 未実走。test module を import した直接呼出し 75 ケース PASS、反実仮想 3 件 (個別等値検査除去 / 副 digest 束縛除去 / 副 schema の key 依存化) が DID NOT RAISE。親の焦点走 1 (計算ノード bnode019、所有 test + consumer 15 file: S1・mocc 3 件・A-2 certification・calibration workload・S5・rung1 driver・t152・spawn 目録・B-4 目録・s8a sweep・requested_us・backoff_sweep) = **1148 passed / 2 skipped、赤 0**。所有 test 単独の `-rA` 走 (bnode、`verbatim/focus-own2-child-stdout.txt`) = **218 PASSED / 0 skipped**、うち新設 43 node すべて PASSED。
- 段 6 review A (正しさ境界、11 call) / B (過剰・削除・pin、9 call): **両方 GO、must-fix 0**。A: should = I1 要約の「identity から派生」は当たらない (argv の一時 path と派生 digest / ID だけ、独立 leaf 比較で確認) → 本稿 §4 に反映、m8 は payload 挿入だけを無条件化しないと個別観測で先に落ちて帰属がずれる → spec に反映。B: nit = 総和の再検査 2 ブロックは先行検査で到達不能 (裁定由来の冗長性、維持)、should = node 別の実走証拠 → `-rA` 走を追加取得。fix 巡なし、焦点再レビュー不要。
- 変異 matrix: §8。

## 7. scope 外 (裁定パッケージ候補、実装しない)

1. `s1_verify_extime_calibration` の factory 配線 + genome configure / offline 供給の整合 (D1492 対象、前 wave から継続)。
2. 所有 TU 内の未宣言な条件指令 (重ね当て patch の複合枝) の走査 (`#ifndef` 番兵の免除規則が要る、前 wave から継続)。
3. 公開 driver (coverage / frequency / rung1 / requested_us) の実走による `condition_gates` の取得。`backoff_requested_us` に admission を載せる変更は D1492 の配線判断 (返り値を捨てる現行を変える) なので別変更単位。
4. (前 wave から継続) 探索 loop への meaning 配線 + offline 供給 + admission 永続化、SS2PL 4 件 (T-2737 §7 待ち)、S2 の Pegasus 固定値。
5. 単 file の複数箇所 macro (RUNG1 N=2、GATING N=12) への箇所識別の拡張 — 現行は総数で足りる (§5) ので足さない。header 単 file で N>1 の macro を登録するときは要再検討。
6. `_write_shadow_owner_source` の deep mirror で directory が symlink のとき (`.git` 以外) は capture の no-follow が先に拒否するので専用検査は足していない。
7. 古い文言: `make_define_request` の error 文 `22-macro domain` (現物 40、前 wave から継続)。

## 8. 変異による裏取り

事前登録は `verbatim/ruling.md` §3 (m0〜m8)。段 6 レビュー A の should (m8 は payload 挿入だけを無条件化しないと個別観測で先に落ちて帰属がずれる) を spec に反映 (`**companion_payload` → 2 key を空 tuple で常時出す形)。runner = `tools/mutation_worktree.py` (独立 shared clone `mutation-source` を source、固定 commit `cfab7a2f2`、dispatch mode、`tools/run_tests.py --force-dispatch test_condition_meaning_gate.py test_s1_direct_comparison.py -q -rf`)。台帳の原本 (artifact.stdout 込み、930 KB / 950 KB) は job dir、insight には `artifact.stdout` を落とし原本 sha256 で束縛した要約版を置く。

| 走 | spec | 結果 | 台帳 |
|---|---|---|---|
| probe (20:19〜20:38 JST) | `verbatim/mutation-spec-probe.json` (sha256 `6f8f990e30e460be…`、全変異を SURVIVED・期待 node 空で登録し観測 node を集める、DW-M07 の probe) | baseline PASSED、m0 SURVIVED、m1〜m8 は MISMATCH (= 観測 node が記録された) | `verbatim/mutation-ledger-probe.summary.json` (原本 sha256 `dadd22ed0a502541…`) |
| final (20:41〜21:00 JST) | `verbatim/mutation-spec-final.json` (sha256 `e1a6a7418c3f8838…`、probe の観測 node を完全集合として登録) | **baseline PASSED (28.0 s)、m1〜m8 KILLED (期待 node 完全一致 8/8)、m0 等価 SURVIVED、MISMATCH 0、wrapper rc=0** (各変異 32〜35 s) | `verbatim/mutation-ledger-final.summary.json` (原本 sha256 `d640096dfc15f299…`) |

| id | 変異 (G の置換) | 結果 | 落ちた node (帰属) |
|---|---|---|---|
| m0 | 副 mapping `_CONDITIONAL_BRANCH_COMPANION_SITES` の行末に comment | SURVIVED (等価、期待どおり) | — |
| m1 | 副 mapping の header N 2 → 1 | KILLED 42/42 | 独立期待表との照合 (`test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches`)、全 registry 正例 `[BACKOFF_REQUESTED_US]`、REQUESTED_US の正例・負例・schema 群 40 (fixture は header 2 箇所のため `site-count-mismatch` で green 前提が崩れる)。単一 seam (宣言 N) の波及 |
| m2 | 深い鏡像の書出しで owner 以外の file を計装本文でなく元本文にする (file は消さない) | KILLED 44/44 | REQUESTED_US 38 (completed 2/4 → 正例・shadow 検査・schema 前提) + **NOINLINE 6** (`test_backoff_noinline_*` 4、`accepts_each_registry_macro[BACKOFF_NOINLINE]`、`test_noinline_inert_meaning_record_comes_from_registry_factory`) — 深い鏡像経路は header 宣言の既存例と共有されるので同じ seam が両方に効く (単一 seam) |
| m3 | 期待式の N を `_declared_total_site_count` → `_declared_site_count` (総数 4 → 主 2) | KILLED 37/37 | **正しい 4 箇所入力の過剰拒否** (expected (2,2)/(0,2) vs observed (4,4)/(0,4)): 正例・pragma-once・CLI・全 registry 正例 `[R]`・schema 群 (green 前提) + 負例の reason 変化 (`include_counts[missing]` は総数 2 で一致するが個別観測が拒否するので reason が `site-observation-mismatch` へ、相殺 node は総数不一致で reason が `selection-mismatch` へ)。「未 include を通す欠陥」の検出には数えない (段 3 A2) |
| m4′ | 個別観測の等値検査 `if counts != expected:` → `if False and …` | KILLED 1/1 | `test_requested_us_multifile_rejects_compensated_missing_sites` (評価側の直接検査、単一理由 = 相殺入力 (owner 2 箇所 `#if 0` + pragma once 無し header 2 回 include) が総数 (4,4)/(0,4) で通る) |
| m5 | 副検証の適用条件を登録簿でなく `"companion_sources" in evidence` に | KILLED 1/1 | `test_requested_us_multifile_green_schema[missing]` (両副 key を落とした green record が受理される、単一理由) |
| m6 | 登録簿の REQUESTED_US 主 entry 削除 | KILLED 44/44 | factory None / unestablished による REQUESTED_US 41 (fixture は独立期待から作るので KeyError ではない) + 登録簿 / patch 束縛 + 全 registry 正例 `[R]` + 集合 pin (`test_v1_domain_and_claim_boundaries_are_exact`)。多 node だが seam は 1 つ (entry 削除) |
| m7 | 副検証の `source_file.sha256 != row["source_sha256"]` 項だけ除去 | KILLED 1/1 | `test_requested_us_multifile_green_schema[digest]` (形式正しい別 digest を片側だけ改変した record が通る、単一理由) |
| m8 (過剰拒否の正例) | 副 key 2 つを単 file macro の evidence にも空 tuple で常時出す | KILLED 95/95 | **requested_us の node は 0 件**、既存単 file macro の正例が `_issue_arm_record` の発行時 schema (unexpected key) で赤: 全 registry 正例 21・NOINLINE / SORT / REPORT の正例・S1 の prepare 系 (canonical predicate 32 + frozen gate 6 + quarantine 系) 等。bytes 比較に到達する前に schema で落ちる (段 6 A の指摘どおり、検出箇所をそのまま書く) = 既存 record の key 集合を守る防壁の正例 |

DW-M02: 所見ゼロを変異なしで緑と数えていない。DW-M03: m2 / m3 / m6 / m8 の多 node は上表で seam と帰属を分けた。DW-M05: 変異中は親の worktree 編集と子の起動を止めた (mutation-source は独立 clone)。probe → final の 2 走は DW-M07 の手順で erratum ではない。

## 9. 逐語一覧

| file | 内容 |
|---|---|
| `verbatim/T-2153-origin.md` | ユーザー依頼 (dev-wave 引数) の逐語 |
| `verbatim/brief.md` / `verbatim/ruling.md` | 段 1 brief (P1〜P8)、段 4 裁定 (plan v2、変異事前登録 m0〜m8、記録訂正) |
| `verbatim/s2-plan.md`、`verbatim/s3-consult-{a,b}.md` | 段 2 plan、段 3 相談 2 本 |
| `verbatim/s5-author-impl.md`、`verbatim/s6-review-{a,b}.md` | 段 5 author 報告、段 6 レビュー 2 本 |
| `verbatim/login-pre/`、`verbatim/login-pre2/`、`verbatim/login-after/`、`verbatim/i1-after/`、`verbatim/stage6-compute/` | 段 1 前提実測 (3 + 1 cell)、変更後 login (5 cell)、I1 用の同 driver-id 取り直し (3 cell)、計算ノード (5 cell、bnode016) の CLI stdout.jsonl |
| `verbatim/nest-static-analysis.{sh.txt,out.txt}`、`verbatim/probe-site-token.{sh.txt,out.txt}` | 各 directive 箇所の外側条件の静的列挙、箇所識別 marker の生死実験 |
| `verbatim/compare-i1-login.log`、`verbatim/compare-login-compute.log` | I1 の leaf 比較、login / 計算ノードの leaf 比較 |
| `verbatim/focus-own1.log`、`verbatim/focus-own2-child-stdout.txt` | 焦点走 (15 file) と所有 test の node 別結果 |
| `verbatim/mutation-spec-{probe,final}.json`、`verbatim/mutation-ledger-{probe,final}.summary.json` | 変異 spec 2 本と台帳 2 走の要約版 (`artifact.stdout` を落とし、原本 sha256 / bytes を `original_sha256` / `original_bytes` に束縛。原本は job dir) |
| `verbatim/verbatim-normalization.json` | 逐語 3 file (`focus-own1.log`、`s3-consult-b.md`、`s6-review-b.md`) の末尾空白を `git diff --check` のため可逆最小正規化した記録 (原文 sha256・bytes・行ごとの removed・復元法、可視文字不変。他 file は原文 sha256 のみ) |
