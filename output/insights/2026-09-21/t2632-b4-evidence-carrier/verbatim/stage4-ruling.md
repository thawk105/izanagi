# [T-2632] 段 4 裁定 (2026-09-21 20:4x JST、親)

入力: 段 2 プラン `codex/s2-plan-r2.md` (以下 plan)、段 3 相談 A `codex/s3-consult-A.md` (正しさ境界)、B `codex/s3-consult-B.md` (過剰・scope)。
いずれも check_codex_output rc=0。段 4 直前の inbox 再走査: 新裁定なし (第 29 回は T-2632 を次回回し)。並走 T-2632 wave なし。

## 1. 所見の裁定

| # | 所見 | 判定 | 採否・scope | 放置時の成果物影響 (DW-G05) |
|---|---|---|---|---|
| A1 | 辺 A の束縛 (hash は読んだ document、attempt は variant + ID で切る) | refuted | — | — |
| A2 | 規律 2・D39 決定 3 (計画した変更経路) | refuted | 入力隔離の test 不足は A7-B で扱う | — |
| A3 | P4 の回復説明が誤り (reject は再実行で新 attempt → 上書きで対応消失、B-4 は再実行拒否、trigger と違い評価前に破損を検出しない) | **real、must-fix** | 採用 (説明の限定 + 評価前の検証 + 失敗後 2 回目の test) | B-4 の 1 回限りの認可を消費した後に破損で止まり、評価済み attempt が whiteboard に残らない |
| A4 | caller の受理域 (codec 経由化は v2 追加 + 旧 json.loads が許した不正 v1 の縮小) | refuted (両方向の変化は裁定整合) | insight に両方向を記録 | — |
| A5 | 参照点の定義と凍結事前登録 | refuted | — | — |
| A6 | 親の実測の一般化 (B-4 lock も trial 同値、stock は whiteboard に触れないが WAL と critic digest には触れる) | refuted (構造上) | 「stock は campaign の観測を変えない」とは書かない | — |
| A7-A | 変異 S10 は `proposal_bytes` が main から見えず NameError で落ちる | **real、must-fix** | 採用 (`proposal_capture["proposal_bytes"]` を使う形へ) | 誤帰属の KILL で hash 検証の検出力を主張してしまう |
| A7-B | planner / coder / critic 入力への漏れを出力 bytes で確かめる test が無い | real、should-fix | 採用 (1 test + 変異 S14) | attempt / hash が critic digest に漏れる回帰を見逃す |
| A7-C | S4 は採用 commit と最新 start の attempt が異なる fixture が要る。pair は drive を stub する既存 fixture では無意味。失敗後の再起動まで検証。invalid lock に non-certifying を明示し issuer 未呼出しも検査 | real、should-fix | 採用。ただし pair の実 drive 通し test は採らない (下記) | attempt 混入・失敗後の対応消失が緑のまま通る |
| B1 | 4 項の被覆、P1 (reference 欄なしで次 wave が実装可能) | refuted | — | — |
| B2 | caller の追加 test 2 件が既存 test と重複 | real、nit | 採用 (既存 test の v2 化・assertion 追加で兼用) | test の重複のみ |
| B3 | P7 の読み | refuted | — | — |
| B4 | caller の説明文 (「current storage format」「All twelve sources are absent」) と brief の完了判定が過大 | real、should-fix | 採用 (caller の docstring / comment を「この caller が読む checkpoint と lock だけでは構成できない」へ限定、brief を 2 経路へ訂正) | 出所の保存と適格行の構成を混同して成果を過大評価 |
| B5 | caller の局所修正 (`.get("trial")`) | refuted | plan の `.get` を採用 | — |
| B6 | 削除・非接触 | refuted | — | — |

**pair の実 drive 通し test を採らない理由:** pair の候補側は `drive_iteration` そのもので、outcome ごとの entry は drive を直接呼ぶ test が覆う。
pair 固有の性質は「stock は entry を書かない」だけで、これは stock 経路 (`_run_stock_control_resolved`) の単位 test で直接検査できる。
drive 全体を stub する既存 `pair_cli_case` に provenance の assertion を足しても、機構を通らない緑になるので足さない。

## 2. scope 外 (実装しない。insight に記録、起票しない)

- base provenance の admission 検査 (`artifact_admission` への追加) — 両相談とも scope 外と明示。
- 中断後に B-4 の認可を再利用可能にする変更・回復 gate・台帳。
- side channel への `reference` 欄、caller に side channel を読ませること (D2100 の 12 件の報告は本 wave 後も候補 1 件につき 12 件のまま)。
- sort / trigger driver への展開 (DW-G03)。

## 3. プラン v2 (plan からの差分だけ。他は plan のとおり)

1. **P4 の保証の限定。** 保証は「provenance を公開できない iteration は checkpoint に確定しない」だけとする。
   provenance 公開後・checkpoint 前の中断の帰結を helper の docstring に経路別で書く —
   非 B-4 の certified は再実行で `duplicate` へ変わり得る / 検疫 reject は再実行で新しい attempt を追加し、同 iteration の entry は上書きされ
   最初の attempt への対応は WAL にだけ残る / B-4 bootstrap・continuation は既存の履歴・receipt 検査で再実行が拒否され、公開済み entry が残る。
   iteration key の上書き merge (trigger 同型) は保つ。「回復可能」「対応を失わない」とは書かない。
2. **評価前の検証 (新)。** `drive_iteration` で layout が決まった直後、B-4 認可の検査・消費 (`require_b4_iteration_authorization` /
   `consume_b4_iteration_authorization`) と評価より前に、既存 report を読み検証する (書かない)。破損なら `.corrupt.<epoch>` へ退避して停止し、
   評価も認可消費もしない。入口停止 (`stopped-before`) の経路でも読むだけで、report を新設しない (P5 は不変)。
3. **test の追加・変更。**
   - `test_base_provenance_inputs_do_not_read_report` (新): `whiteboard_for_planner` / `planner_context_payload` / `make_critic_digest` の出力 bytes が、
     report の不在・内容の異なる report の間で完全一致する。
   - `test_base_provenance_duplicate_reuses_selected_attempt`: 採用された commit の attempt と、最新 start の attempt が**異なる** fixture で組む。
   - `test_base_provenance_failure_keeps_checkpoint`: 書込み失敗の後に同じ proposal で 2 回目を呼び、上の 1. の経路別帰結 (非 B-4 の reject なら新 attempt で
     entry が上書きされ、旧 attempt の WAL record は残る) を assert する。
   - `test_base_provenance_corrupt_report_stops`: 破損 report で、評価 (`_run_one_iteration_resolved`) が呼ばれず、B-4 mode では認可が消費されないことも assert する。
   - `test_pair_candidate_has_one_provenance_entry` は作らない (§1 の理由)。stock 経路の非書込みは `test_base_provenance_skips_stock_and_entry_stop` で直接検査する。
   - caller: 既存 `_campaign` fixture を v2 化し、既存 test (success-only・mixed・minimal rejected・fail row・unreadable の parametrize) をそのまま v2 で通す。
     追加は v1 回帰 (`test_v1_campaigns_remain_readable`)、v1 の trial 欠落、invalid lock の parametrize への non-certifying lock・非 canonical v2・
     壊れた authority の追加と issuer 未呼出しの assert だけ。`test_v2_campaigns_reach_empty_issuer` / `test_unknown_v2_trial_is_campaign_input_unreadable` は作らない。
   - v2 lock を作る fixture の binding は module 単位で 1 回だけ作る (HEAD blob 読みを test ごとに繰り返さない、全体 5 分の上限)。
4. **caller の説明文の限定。** module docstring と `collect_scheduled_batch` の docstring、`# All twelve sources are absent in the current storage format.`
   を「この caller が読む checkpoint (whiteboard 5 field) と lock だけでは構成できない静的な不足分類」と限定する。
5. **brief の完了判定の訂正 (親、docs)。** 「赤候補あり → 不足報告・issuer 未呼出し / 候補なし → 空 batch で issuer 到達」の 2 経路と書く。
   brief (`verbatim/stage1-brief.md`) は段 1 の逐語として書き換えず、訂正は本裁定と insight に置く。

## 4. 変異の事前登録 (DW-M01)

期待 kill node は plan §9 と上の test 名。実装後に位置と単一理由性 (同じ入力を拒否する層が前後・内側に無いこと) を確かめ、成立しないものは
登録から外して実効 gate へ再照準する。期待 node の完全集合は DW-M08 に従い login self-run か初回 dispatch probe で集める。

| ID | 対象 | 一行変異 | 期待 kill (test) | 向き |
|---|---|---|---|---|
| S1 | p3_s4_loop.py drive_iteration | `_append_provenance_entry(...)` の削除 | records_each_outcome | 負 |
| S2 | 同 | checkpoint 保存を provenance 公開より前へ | precedes_checkpoint / failure_keeps_checkpoint | 負 |
| S3 | attempt 抽出 helper | WAL filter から attempt ID 条件を削除 | rejects_same_variant_use_distinct_attempts | 負 |
| S4 | 同 | commit 由来 ID を最新 start の ID に置換 | duplicate_reuses_selected_attempt | 負 |
| S5 | 同 | `canonical_sha256(vars(record))` → `canonical_sha256(record.payload)` | keeps_all_attempt_records | 負 |
| S6 | 同 | 対象 record を stage keyed dict に圧縮 | keeps_all_attempt_records | 負 |
| S7 | merge helper | 既存 entries を `{}` に | merge_is_idempotent | 負 |
| S8 | loader | 破損時 raise → `return {}` | corrupt_report_stops | 負 |
| S9 | writer | file の `os.fsync` 削除 | publish_failure_preserves_old_report (fsync 注入) | 負 |
| S10 | main | hash を `hashlib.sha256(proposal_capture["proposal_bytes"]).hexdigest()` に置換 | hash_excludes_receipt_key | 負 |
| S11 | main | capture を agent-inputs 指定時だけに戻す | main_provenance_hash_without_agent_inputs | 負 |
| S12 | drive_iteration | writer 呼出しを `if not b5_mode:` 付きに | records_b5_early_returns | 負 |
| S13 | drive_iteration | 評価前の検証呼出しを削除 | corrupt_report_stops (評価未呼出し・認可未消費の assert) | 負 |
| S14 | make_critic_digest | report の内容を digest 文字列へ連結する 1 行を挿入 | inputs_do_not_read_report | 負 |
| C1 | p3_b4_prerun_caller.py | decoded identity の trial 読取りを raw lock の `.get("trial")` に戻す | 既存 success-only test (v2 fixture) | 負 |
| C2 | 同 | codec 呼出しを raw `json.loads` + inner の手読みに置換 | invalid lock parametrize (authority / 非 canonical v2) | 負 |
| C3 | 同 | `if decoded.is_v1: raise ValueError(...)` を追加 | v1_campaigns_remain_readable | 正 (過剰拒否) |
| C4 | 同 | catch tuple から `ValueError` を削除 | invalid lock parametrize | 負 |
| C5 | 同 | `.get("trial")` → `["trial"]` | missing_v1_trial | 負 |
| E1 | attempt 抽出 helper | `canonical_sha256(x)` → `hashlib.sha256(canonical_bytes(x)).hexdigest()` | なし (SURVIVED を期待) | 等価対照 |

**実行方法:** `p3_s4_loop.py` は contract loader closure と B-4 projection closure に入るので、未 commit の注入で v2 lock を作る test が内容と無関係に
落ちる ([T-2795] insight §5)。注入群は等価対照 E1 の probe で落ちる node を drift node として対象集合から外し、v2 lock を要する検査
(S 系で drift node にしか現れないもの) は変異を焼いた commit を独立 clone に作る commit 群で扱う。drift による赤を KILL と数えない。
`p3_b4_prerun_caller.py` は closure 外なので通常の注入群で扱う。
