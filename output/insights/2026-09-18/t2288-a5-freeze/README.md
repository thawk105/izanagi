# [T-2288] B-4 床値 spec 3 本の A-5 を確定して凍結した — 凍結 commit `0b4fbd7a6` の 3 spec が実 checkout で `--validate-only` を通った (実装差分ゼロ)

`authority: none`
`default_effect: no-state-change`

2026-09-18。wave `dev-wave-t2288-a5-freeze`、branch `worktree-dev-wave-t2288-a5-freeze`。起点 local main
`d2ebef7a407dc6be61622ed596cf08b8b518f606` (段 4 直前まで進行なし)。**実装面 (D95 決定 2) の差分は 0。** 本 wave の成果物は
凍結 commit (3 spec + decisions fragment)、本スナップショット、worklog fragment である。可変状態の正本は worklog 末尾と現行 phase doc であり、
本書ではない。

## 依頼と答え

依頼は「[T-2288] (D2120 項 4、D1641 決定 1〜3 / D1638 の委任) B-4 床値 spec の A-5 を AI が確定して凍結 commit へ進める —
1 spec あたり 2 窓の `not_before` / `not_after`、各窓の `campaign_id`、`seed_hex`、`artifact_relpath` ×2、`summary_relpath`、3 spec と
集約出力の対応。着手直前の local main から fresh worktree を作る。順序と落ち方は binder precheck の insight「凍結 wave への注意点」に従い、
捨て branch の 3 commit は置き方の実例として読む (land しない)。spec の path・命名は本 wave の決定として insight に明記。今回は凍結まで
(床値実測・集約・採用裁定は後続)。規律 2 を緩めない。本題の凍結だけ」だった。

**答え: A-5 を確定し、3 spec を 1 commit で凍結した。凍結 commit は `0b4fbd7a67652d37bb41cd18386e1234268eafdc`、その親 =
`provenance.source_commit` = `d2ebef7a407dc6be61622ed596cf08b8b518f606`。** 同じ commit に decisions fragment
(`docs/spool/decisions/2026-09-18-dev-wave-t2288-a5-freeze-1.md`、fold 後に D 番号が付く) を置き、3 spec の relpath と sha256 (= 集約の
期待 spec 列)・窓・識別子・seed 式・実行設定・集約対応をそこで確定した。凍結 commit の後、同じ checkout で
`floor_pair_driver --validate-only --expected-sha256` を 3 本実走し、**3 本とも rc=0・stderr 空**で `floor-pair-plan/v2` (各 248 session・
496 測定・2 窓 × 124) を返した。実行手順は precheck の注意点どおりで、落ちた箇所は無い。

値の一覧と理由は decisions fragment が正本で、本書は実走の記録と後続への申し送りを持つ。

## 確定した A-5 (要約。正本は decisions fragment)

| 項目 | 値 |
|---|---|
| directory | `output/env/pegasus/floor-pair/t2288-f1/` (`t2288-f1` は凍結集合の識別子) |
| spec (3 本) | `spec__env-pegasus__protocol-silo__threads-48__workload-<wl>-s0.9-rmw0__campaign-t2288-f1-<wl>-c1c2.json`、`<wl>` ∈ {rr95, rr50, rr5} |
| 窓 (UTC 半開、3 spec 共通) | w1 `[2026-09-19T00:00:00Z, 2026-09-27T00:00:00Z)`、w2 `[2026-09-29T00:00:00Z, 2026-10-07T00:00:00Z)`、各 62 標本 |
| campaign_id / window_id / pair_id | `t2288-f1-<wl>-c1` `-c2` / `<wl>-w1` `-w2` / `pair-<wl>` |
| 窓の出力 | `window__…__workload-<wl>-s0.9-rmw0__campaign-t2288-f1-<wl>-c1.jsonl`、同 `-c2.jsonl` (同 directory) |
| summary | `summary__…__workload-<wl>-s0.9-rmw0__campaign-t2288-f1-<wl>-c1c2.json` (同 directory) |
| seed_hex | `SHA-256(UTF-8 "izanagi floor-pair-spec/v3 seed\|<spec_relpath>\|<source_commit>")`、値は `verbatim/specs.sha256.txt` |
| 実行設定 | 既決値の継承: `PEGASUS_COMPUTE` / `pegasus` / 2100 (D1641 決定 3・D2089)。本 wave の運用選択: `numactl_argv []` / `extra_env {}` / `use_perf false` / `timeout_s 120` / `probe_timeout_s 30` |
| 既決値 | artifacts (D2069)、cells・perf_config (D2088 / D2089)、calibration (D2090)、statistics・failure_policy・format ID (driver 定数) |
| 集約 | `expected_specs` = 3 (relpath, sha256)、`summary_paths` = 3 summary、`output_dir` = 同 directory。予測 file 名は decisions fragment |

3 spec の sha256 (凍結 bytes、`sha256sum` で照合): rr95 `990e3a6feb176ccf863315fde6e2afce43b7fc16053f50a1080641dde2570619`、
rr50 `b582d20c37268f491e4c47bb7436731197c18e737cdcca43694c64fa3e0d5e37`、rr5 `d13c384473a5d24170e929f7e17aad9cc24479a5487ed0da21d06bc45430d8c4`。
段 3 レンズ B が独立に再計算した値と全桁一致した (`verbatim/s3-lens-b.md`)。

## 実走の記録 (すべて login node、計算ノード job なし)

順序は precheck の注意点どおり: startup gate (fresh、乖離 0) → `place` → spec 生成 → 凍結 commit → `--validate-only`。

| 走 | rc | 観測 |
|---|---|---|
| `b4_binary_record place` (record `rr20--stock_common.json` → 本 worktree) | 0 | `output/env/pegasus/binaries/7cdf0dc345f7…274a4`、701,760 bytes、mode 744、sha256 一致、tree clean (ignored)。policy は現行と一致 (`store_binaries` が要求、D2069 項 6) |
| `--validate-only` rr95 (`--expected-sha256 990e3a6f…0619`) | 0 | stdout 126,415 bytes、stderr 0 byte。`plan_sha256` `9c7838cc1d501595e690c4f868dbd36a32acdb1e54372b5a15585ac9305c3860` |
| `--validate-only` rr50 (`b582d20c…5e37`) | 0 | stdout 126,415 bytes、stderr 0 byte。`plan_sha256` `b4da73d253e55851c2752cbe821b8deebc2c49269c0bb0022a1ce2c1b09a05b8` |
| `--validate-only` rr5 (`d13c3844…d8c4`) | 0 | stdout 123,935 bytes、stderr 0 byte。`plan_sha256` `cc45797ad26eb1a50d658126ac594277523e04b9fd102727807f38cd42e738b7` |
| 負対照 (期待 sha256 の末尾 1 桁 `9`→`8`) | 1 | `frozen spec sha256 不一致: expected=…0618, observed=…0619` (`verbatim/negative-a-wrong-sha.err`) |

3 plan とも schema `floor-pair-plan/v2`、session 248 (窓ごと 124 = 62 標本 × 2 side)、測定 496 (candidate 248・reference 248)、
top-level key は `plan_sha256` / `randomization_algorithm` / `schema` / `seed_hex` / `sessions` / `spec_sha256` (`verbatim/plan-summary.txt`)。
事前登録 §11.2「1 pair・1 セルあたり 248 side session・496 測定」の名目と一致する。plan 全文は job dir に置き、本書へ複製しない
(同じ checkout・同じ spec bytes・同じ実装から `--validate-only` で再生成できる)。

`--validate-only` は `load_frozen_spec` と `make_measurement_plan` だけを呼び、`_assert_live_environment` (`run_window` 専用) を
通らない。計算ノード・新規 Pegasus 実行体 (F660) は要らなかった。負対照は precheck (5 本) が同じ binder で落ちることを実測済みなので
本 wave は 1 本だけ再走した。

## 段 2・3 が親 brief を訂正した点 (すべて採用)

- **窓判定は session 開始時刻** (`floor_pair_driver.py` の session 実行部)。brief の「任意の session 間 > 24 h」「人手確認は式で閉じる」は
  過大で撤回した。driver は session 全体の締切を持たないので、per-rep timeout の合計 (約 21.5 分) を session の wall 上限とも言えない。
  w2 の開始を 1 日遅らせて開始許容帯の差を 48 h にしたが、これは余裕であって終了→開始の分離の機械保証ではない (D1974 項 3・6)。
- **HMAC randomization は 3 箇所を決める** (窓内の標本順・side session 順・session 内の candidate / reference 順)。brief の「side 順序だけ」
  「同一 bytes なので有利な選択は存在しない」は誤りで撤回した。公開式は再現性を与えるだけで、選別不能性を証明しない。
- **実行設定は較正由来の確定値ではなく本 wave の運用選択**として記録する。`numactl_argv []` は「生成 command の numactl prefix が空」の
  意味で較正時 (NUMA 1 node → numactl なし) と同等、`extra_env {}` は親環境の継承。120 秒 / 4.5 秒 ≈ 27 倍は算術であって成功率の
  根拠ではない。
- **1 窓 ≈ 1.6 h は上限ではない。** bench 部分 (124 session × 10 rep × 3.5〜4.5 秒) は 1.21〜1.55 h、probe の timeout を全件計上すると
  4.3〜4.65 h、全 timeout の総和は 44.4 h。3 spec の別 node 並走は資源と admission に依存する推測。
- **spec 名にも campaign 成分を含める** (可読性のための選択。D1641 決定 3 の命名規則は成果物向けで、spec への必須化とは読まない)。
- **D2088 の「spec の非保証欄」は schema v3 に無い** (未知 key は拒否)。AI の選択 (reps・実行設定) は decisions fragment と本書に残す
  (記録先の訂正であり値の変更ではない)。
- **三軸語走査器 (`s8b_holdout_freeze search`) は holdout 値の file 内 conjunction を見るもの**で、仮置き語の一般走査ではない。
  仮置き語 (旧 precheck の識別子・2030 年の日時・ゼロ seed) は別に grep で走査した (spec 3 本は 0 件)。
- **issuer は spec 間の campaign_id 重複を検査しない** (集合和で消える)。6 件相異は本 wave の選択で、機械検査ではない。

段 3 の裁定全文は `verbatim/s4-ruling.md` (plan の訂正 10 点、レンズ A 9 点、レンズ B 9 点)。ユーザーへ返す裁定事項は無し
(A-5 は D2120 項 4 の委任で確定できる — 両レンズ一致)。

## 後続の測定 wave への申し送り (本 wave は実装しない)

1. **Pegasus job body が要る。** main の `tools/pegasus/admission_registry.json` に floor-pair 系の job body は無く、`run_window` は
   `site_policy.current_site(require_evidence=True)` の証拠を要求する。F660 により、job body を着地させる wave と実測する wave は分ける。
   `--validate-only` は実測の代替ではない。
2. **各 spec の w1・w2・finalize は同じ実行 HEAD で走らせる。** finalize は両窓の header の `loaded_head` と `runtime_head` に、finalize 時に
   読み込んだ `spec.loaded_head` との exact 一致を要求する。spec bytes が同じだけでは足りない。測定の途中に成果物を commit して HEAD を
   進める運用はこの条件と衝突する。凍結 commit 自体で走らせる必要はないが、実行 commit H を決めたら 3 段とも H に固定する。
3. **`place` は checkout ごと。** ignored binary は merge で移らない。配置には receipt の policy が現行と一致することが要る (D2069 項 6・7)。
4. **窓の末端ぎりぎりに投入しない。** session 開始が窓外になると `outside_window` (FATAL) で残りは未実行になる。queue 待ちと走行を見込み、
   w1 は 2026-09-19T00:00:00Z 以降、w2 は 2026-09-29T00:00:00Z 以降に session が始まるよう投入する。窓を使えずに終わった場合は
   未実施の凍結として記録を残し、窓の延長・差替えをせず新しい凍結を別 commit で行う。
5. **create-only を守る。** 欠落・窓逸脱後の再実行で既存の出力を置き換えない。
6. **証拠確認者 (thawk105 名義、AI 委任) が実 timestamp で確認する事項:** 実 campaign の 24 時間以上の分離 (終了→開始を含む保守的な
   確認)、n = 62、欠測率 (campaign 合算 5%)、環境の一致。
7. **集約は decisions fragment の 3 組 (relpath, sha256) を `expected_specs` に、3 summary を `summary_paths` に、同 directory を `output_dir`
   に渡す。** summary から期待列を導出せず、正常入力だけに間引かない。

## 主張しないこと

- **凍結時の成功が後続の実測の成功を保証しない。** `--validate-only` が通ったのは loader と plan 生成までで、`run_window`・`finalize`・
  issuer・材料レポートへの接続は実行していない。
- **事前性の機械証明は無い。** spec の sha256・HEAD blob 一致・祖先性は「後から spec と期待 hash を差し替える」経路を閉じない。期待 spec 列を
  凍結 commit に同居させても機械的に後変更不能にはならず、後続がこの pin を使うと決めることで運用として保つ。
- n = 62・実 campaign の分離・対象集合の意味的一致は機械検査されない (D1974 項 6)。統計的独立性、残存標本での 95% 被覆、contention 域の
  網羅性も主張しない。
- session の wall 上限、将来の割当て・環境の同一性、別 node 並走、admission、binary の将来の可用性、trace 不在の完全な検出、実行中の
  module bytes が記録 commit に対応すること、成果物の削除・改変の防止、床値の生成・採用・§5 の記入・本書の発効はいずれも主張しない。
- binder が正しいことを証明しない。通ったことと、負対照 1 本 (precheck の 5 本に加え) が拒否されたことを観測しただけで、driver の
  「証明していないこと」(module docstring) はそのまま残る。

## 生証拠

| path | 中身 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief (親)。(P1)〜(P8) と段 1 前の棚卸し。訂正前の記述を含む |
| `verbatim/s2-plan.md` | 段 2 plan (codex、read-only)。JSON 全文・loader 照合表・A-5 の根拠と代案・集約対応・手順 |
| `verbatim/s3-lens-a.md` | 段 3 レンズ A (正しさ境界・既裁定整合・事前性)。must-fix 4 |
| `verbatim/s3-lens-b.md` | 段 3 レンズ B (実装照合・実効性)。must-fix 3、spec sha256 の独立再計算 |
| `verbatim/s4-ruling.md` | 段 4 裁定 (親)。全所見の real / 情報 / nit と採否、plan v2 |
| `verbatim/s6-review-a.md` | 段 6 レビュー A (逐語整合・過大主張・記録形式)。must-fix 1 / nit 3 |
| `verbatim/s6-review-b.md` | 段 6 レビュー B (実物照合・凍結 bytes・git 状態)。must-fix 0、独立実測で全件一致 |
| `verbatim/specs.sha256.txt` | 生成器の出力 (3 spec の sha256・relpath・seed_hex) |
| `verbatim/plan-summary.txt` | 3 plan の集計 (schema・plan_sha256・session / 測定数・窓別・campaign 別・先頭 session) |
| `verbatim/negative-a-wrong-sha.err` | 負対照の stderr (traceback 全文) |

spec 生成器・parse 事前 probe・plan 集計 script (`.py`) と plan 全文 (stdout 3 本) は job dir にだけ置いた (script は実装面 suffix、plan は
再生成可能)。

## 段 6 の敵対レビュー 2 本 (記録 3 点に対して、read-only)

| レンズ | 所見 | 親の是正 |
|---|---|---|
| A (逐語整合・過大主張・記録形式、`verbatim/s6-review-a.md`) | must-fix 1 (検査の実施状態と結果の参照先が不整合 — 本表と worklog fragment が「実走して記録する」予定形のままだった)、nit 3 (directory の「兄弟」の階層表現、既決値と運用選択の一括、insight の非保証列挙に module bytes の項が無い)、情報 (数値・hash・識別子は全桁一致、授権・責任境界・申し送りは既裁定と整合、生証拠 `s4-ruling.md` の holdout 値の列挙は走査器の hit 元になりうる) | must-fix と nit 3 件をすべて是正 (本表を実測値で埋めた、D fragment 項 1 の階層表現と項 5 の区分を直した、非保証に module bytes を足した)。holdout 値の列挙は走査器の正規表現 (`ycsb_rratio=` / `"ycsb_rratio": "` 形) に当たらず、同 file を含む作業ツリーで search が hit 0 だったことを下表に記録 |
| B (実物照合・凍結 bytes・git 状態、`verbatim/s6-review-b.md`) | must-fix なし。spec 3 hash・凍結 blob・親 OID・変更集合 4 file、較正 3 件と receipt の sha256・セル値・workload 逐語、seed 3 件と生成器の出力 bytes、集約予測名、出力 path の相異・親 directory・symlink 不在、実装面差分 0、plan-summary と本書の整合、負対照 hash、binary の bytes・mode を独立に実測して全件一致 | 是正なし。未確認と申告された項目 (validate-only の独立再実行、`place` 当時の rc・policy) は親の実走記録 (本書「実走の記録」) が持つ |

## 受入・検査

| 検査 | 結果 |
|---|---|
| `python3 tools/check_docs.py` | 凍結 commit 前 (D fragment を含む木) rc=0。本記録 commit 前 (insight・worklog fragment・D fragment の是正を含む木) にも再走し rc=0 |
| `python3 tools/check_ai_provenance.py --message-file` | 凍結 commit の message: 1 件、違反なし。本記録 commit の message も同じ検査を通してから commit |
| 仮置き語の grep (`precheck-placeholder` / `2030-01` / ゼロ seed) | spec 3 本 0 件。verbatim のレンズ A に旧識別子を説明する 1 行 (識別子としての継承ではない) |
| `python3 -m orchestrator.campaign.s8b_holdout_freeze search` (三軸語走査) | rc=0。27,705 file (tracked + untracked、binary 1,827 skip)、holdout rr80 / rr20 とも conjunction hit 0 (軸別 count: rratio 20 / 7、skew 387、rmw 308)、正対照 190 hit (走査器は生きている)。spec 3 本・本 insight・fragment 2 本・verbatim を含む作業ツリーで実走 (所要約 20 分、login node、load 30〜55) |
| `python3 tools/spool_fold.py --dry-run --show-diff` | rc=0。仮採番 D2135、worklog entry 1636、[T-2288] の `更新` は base digest `f5251c0e…` で適用 (実採番は land の fold が行う) |
| 変異 matrix | 実装面差分 0 につき免除 (DW-S04) |
| 受入全走 | 本記録 commit を含む最終 tip に対して land 前に 1 回だけ投入し、child-green でなければ land しない (受領証は job dir)。結果は land の受領証と worklog に残る |
