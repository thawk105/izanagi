# [T-2797] B-5 共通 Tier0 の実装と、LLM arm 親運用・全 arm 同一 walltime の設計 (2026-09-21〜22)

D2200 項 1 の段階認可のうち、発効束の未充足部品「共通 Tier0 (事前登録 §3.1 のコンパイル + 固定スモーク)」を実装し、同じ wave で AI 手番とされた
LLM arm の親運用と全 arm 同一の job walltime (§3.3) を設計した。設計判断は本 wave の decisions 3 件 (題「B-5 共通 Tier0 は子の候補経路で…」「B-5 LLM arm の親運用 — …」
「B-5 本走の job walltime — …」、land の fold で D 番号が付く)。
依頼の逐語は `verbatim/T-2797-request.md`。

## 0. この wave が主張すること・しないこと

- **主張する:** B-5 mode の候補 slot (search / score) で、Tier0 (pipeline と同じ経路の perf build 1 本 + 固定スモーク) が `pipeline-submitted.json` より前に走り、
  不通過は submission を書かず A だけを消費する (B を消費しない・retry しない・search は次の A へ)。通過・不通過は slot ごとの `tier0.json` と台帳 event
  (`tier0 = {status, reason, sidecar_sha256}`、スモークの数値は載せない) に残り、header の `tier0_status` は `implemented` と契約全体を示す。
  焦点走 f4 (統合 + [T-2632] 取り込み + fix 後、37 file) は全緑、変異 matrix と受入は §6 / §7。
- **主張しない:** B-5 本走・校正の投入 (未認可、本 wave は投げていない)。§12 の hash 採取、倍率 k と発効 commit の確定 (land 後の別段)。
  **Tier0 の通過は certified を意味しない** (verify / anomaly reject / bench は従来どおり、規律 2)。コンパイラの非ゼロ終了が候補起因であることの証明
  (投入後の build 失敗を候補起因とする D2198 の既存規約の限界、§4)。**実 build での生死確認 (Tier0 の perf build が pipeline 側で cache hit し verify / bench が続くこと) は未実施** (§8)。
  親運用・walltime は設計であって実装ではない。

## 1. 置いたもの

| 所在 | 内容 |
|---|---|
| `orchestrator/campaign/p3_s4_loop.py` | `B5_TIER0_CONTRACT` (契約の単一定義)、`_b5_tier0_build_inputs` (pipeline と同じ source evidence / admission)、`_run_b5_tier0_smoke` (既存 gateway `run_once` + 既存パーサ + `bench_lock`)、`_run_one_iteration_resolved` の条件の意味検査の後・submission の前の Tier0 (B-5 mode の候補経路だけ)、拒否 outcome `rejected-tier0` の B-5 早期 return と CLI rc 3、base provenance の outcome 集合への `rejected-tier0` 追加 |
| `orchestrator/campaign/b5_generator_contrast.py` | `classify_slot` が submission の有無と独立に `tier0.json` を読む (identity・契約の一致、`rejected-tier0` = A のみ、投入済みで通過証拠が無ければ分類不能欠測)、`_header` の `tier0_status="implemented"` と `tier0_contract` |
| `orchestrator/campaign/b5_generator_contrast_report.py` | 共通構成比較に `tier0_status` / `tier0_contract` (契約の混在を拒否) |
| `orchestrator/tests/test_b5_tier0.py` (新規) | 実 gateway / 既存パーサ / 実 lock を fixture executable で通すスモーク test、通常走の挿入点 test (legacy / v2 の 16 ケース)、親の実 build 確認用の live test 4 本 (専用 receipt が無いと skip) |
| `orchestrator/tests/test_b5_generator_contrast.py` / `_report.py` / `test_ccbench_spawn_sites.py` / `test_p3_s4_loop.py` | 分類・予算・非流出・契約差・旧台帳互換、spawn 目録の bounded client 1 行、既存 B-5 seam fixture の Tier0 追従と provenance の早期 return ケース追加 |

commit (wave branch `worktree-dev-wave-t2797-tier0`): 統合 `b5935b88e` → fix1 `5386b9015` → fix1c `8469b6d4b` → fix1d `051dae5cb` → main 取り込み merge `2e53f3649` → fix2 `83732738b`。

## 2. 契約 (段 4 裁定 §3、`verbatim/s4-adjudication.md`)

- 固定スモーク argv: `--thread_num=4 --ycsb_tuple_num=200 --extime=1 --ycsb_rratio=50 --ycsb_zipf_skew=0.9 --ycsb_rmw=true --ycsb_max_ope=5` + env contract の `clocks_per_us`、numactl も env contract。
  timeout 32 s、`strict_returncode=True`、`use_perf=False`。通過条件 = rc 0・`integer_abort_commit_counts` の commit > 0・`throughput_tps` が有限正。
- 失敗の計上: build の `(RuntimeError, subprocess.SubprocessError)` とスモークの失敗は候補起因 (A のみ・retry なし)。準備段 (source evidence・admission) の例外は捕まえず既存の分類不能欠測へ。
  score slot での不通過は探索予算を動かさず既存の非 certified 分岐で系列停止。stock slot と非 B-5 経路は Tier0 を走らせない。
- sidecar `tier0.json` (schema `p3-s4-loop-b5-tier0/v1`): identity (b5_slot / campaign_id / genome / identity_preimage_sha256)、`contract`、`status`、`reason`、`build` (trace / binary / bin_sha256 / cached)、
  `smoke` (flags / timeout_s / returncode / wall_s / commits / aborts / throughput_positive)、`error`。

## 3. 固定スモークの所要実測 (DW-O13、`probe/`)

- 2026-09-21 14:48〜14:52 JST、gen_S `15197.nqsv` / bnode039 (loadavg 0.70、`pgrep ycsb_` 空)、job Elapse 35 s。probe は repo 外で走らせ、ここへ `.txt` で写した。
- 試走 β の build cache の trace-disabled binary 6 本 (BACKOFF_FIXED = −1 / 1 / 2 / 3 / 8 / 698) × 5 回、固定 argv、`run_once(use_perf=False, strict_returncode=True, numactl=[])`。
- **30 / 30 走で rc 0・commit > 0・throughput 有限正、wall min 1.0035 / 中央値 1.0046 / max 1.0463 s** (各 binary の初回だけ +0.02〜0.04 s)。timeout = ceil(1.0463 × 30) = 32 s。
- 観測 regime の差: build から数時間後の binary、値 1000 は未測 (cache に無い)、write-heavy 試走の cache。

## 4. 段 2〜4 の所見と裁定 (`verbatim/s2-plan.md`、`s3-consult-{A,B}.md`、`s4-adjudication.md`)

- 相談 A / B の must-fix 計 6 を裁定し、実装単位を 1 つに統合 (driver の header が子の契約定数を読むため)、Tier0 のコンパイルを perf 1 本に限定、開始印 sidecar を削除、
  score slot も Tier0 を通す (明示の契約)、build の例外境界を pipeline と同じにした。
- **scope 外 (real、記録のみ):** (a) コンパイラの非ゼロ終了は候補起因の証明にならない (相談 A2) — 投入後の build 失敗を候補起因とする D2198 の規約の一般的な限界で、
  本 wave は同じ失敗集合を投入前へ移しただけ。試走 53 session で build 失敗 0。(b) 実効の handshake 期限は min(2700 s, 残 walltime − 1800 s) (相談 A4) — 期限表示や launcher は変えず、設計記録 (§8) に書いた。

## 5. 段 5〜6 の経緯 (`verbatim/s5-author-A1.md`〜`s6-focus.md`、`s6-adjudication.md`)

- **Codex 利用上限で 2026-09-21 14:33〜20:20 JST に中断した** (別 wave の codex events 末尾「You've hit your usage limit ... try again at Sep 26th, 2026 7:35 PM」)。D582 どおり自動再試行せず停止し、
  ユーザーの連絡で再開した。本 wave の段 2・3 の codex 子 3 本は上限到達前に完了していた。
- author (現 main の unit worktree で先に作成) → 統合 → 焦点走 f1 (3 赤) → レビュー A / B (ともに NO-GO、must-fix 同一 3: 挿入点 test が専用 receipt 無しで skip、
  既存 seam の fixture 追従、自走入口) → fix1 (F3 / F4 / F5、F1 は親 prompt の差し替え禁止が広すぎて正しく停止) → fix1b (F1、通常走の挿入点 test) → 焦点走 f2 (legacy 側 8 ケースが Tier0 前の
  activation 検証で赤) → fix1c → 焦点走 f3 (seam 2 件だけ赤) → 変異 probe で F6 (等価変異でも挿入点 test 16 node が contract-loader-drift で落ちる) → fix1d → probe2 で等価 M0 が SURVIVED。
- **[T-2632] (共有 file の所有 wave) の land 後に local main を取り込んだ。** 自動 merge はテキスト競合 0 だったが、取り込んだ base provenance の outcome 集合が `rejected-tier0` を含まず、
  Tier0 拒否で子が異常終了する意味上の衝突 (F7) を親が照合で見つけた。merge commit は preflight が `p3_s4_loop.py` (両親変更) に Codex author を要求し、merge 状態の木では
  Codex 子を起動できない (midflight gate NG) ので、合成内容の著者 commit を本文で名指しした merge commit にし、F7 と seam 追従は直後の fix2 (Codex author) で直した。
- 焦点再レビュー (NO-GO、must-fix 1 = N1) は F1〜F6 closed、F7 は M18 の実測で閉じた。F7 の影響説明は誤りだった (driver は rc でなく sidecar で分類するので `rejected-tier0` のまま。
  実害は子の異常終了と provenance / loop state の未公開) — 裁定追補 4 で訂正。N1 は §8 の scope 外。
- 焦点走 f4 (37 file、最終統合): **4,813 passed / 20 skipped / 0 failed、161.55 s** (`focus/focus-f4.log`)。

## 6. 変異 matrix (`mutation/`)

- 経路: `tools/mutation_worktree.py --runner-mode dispatch --detached`、source = 独立 clone (D1009、main = 対象 commit)、runner = `run_tests.py --force-dispatch` で
  `test_b5_tier0.py` / `test_b5_generator_contrast.py` / `test_b5_generator_contrast_report.py` (重い `test_p3_s4_loop.py` は runner 外)。期待 node は dispatch probe の観測
  (新規 test file が parametrize / fixture / skip に依存し login self-run が DW-M08 の適用外のため)。
- **final (`mutation-final-results.json`、対象 commit `83732738b`、spec sha256 `1e73bb90…`、2026-09-21 23:33〜09-22 00:10 JST): 20 件中 matching 20 — KILLED 19 (期待 node 集合と完全一致)、
  等価変異 M0 SURVIVED。**

| M | 変異 | 落ちた node 数 | 主な kill 先 |
|---|---|---:|---|
| M0 | 等価 (comment 1 行) | 0 | — (SURVIVED、正例) |
| M1 | Tier0 の block を到達不能に | 17 | 挿入点 16 + 非 B-5 / stock 不到達の AST 検査 |
| M2 | submission を Tier0 より前に | 16 | 挿入点 16 (順序・拒否・例外伝播) |
| M3 | Tier0 の v2 build を trace=True | 5 | v2 側の挿入点 (perf binary が gateway に届く) |
| M4 | smoke の rratio を 95 (保護対象外の workload 値) | 1 | `test_smoke_exact_argv_and_parser` |
| M5 | `strict_returncode=False` | 3 | rc 非 0 の検査 |
| M6 | commit > 0 検査を外す | 1 | `[zero-commit]` |
| M7 | timeout を既定 120 s に | 1 | `test_smoke_timeout` |
| M8 | bench lock を外す | 5 | lock test + fixture executable の lock 要求 |
| M9 | 拒否でも submission を書く | 6 | 拒否 test (legacy / v2 × 3) |
| M10 / M10b | B-5 早期 return 集合 / CLI rc 3 から `rejected-tier0` を外す | 6 / 6 | 拒否 test |
| M11 | build の捕捉を `Exception` に広げる | 3 | build の I/O 例外伝播 (legacy / v2) + 例外境界の AST |
| M12 | `rejected-tier0` を submitted 扱い | 6 | driver の A のみ・retry なし・B 保持 |
| M13 | `rejected-tier0` を retry 対象に | 5 | driver の retry なし |
| M14 | 投入済みで通過証拠なしを受理 | 2 | driver の証拠欠落で停止 |
| M15 | スモーク数値を event に | 6 | 数値非流出・event 形 |
| M16 | report の構成比較から Tier0 key を外す | 4 | report の契約混在拒否 |
| M17 | header を not-implemented に | 2 | header 契約 |
| M18 | provenance の outcome 集合から `rejected-tier0` を外す | 6 | 拒否 test (子の rc 3) |

- **probe の経緯 (初回結果は消さない、DW-M02):** probe1 (`mutation-probe-results.json`、main=`8469b6d4b`) で等価 M0 も挿入点 16 node を落とした (contract-loader-drift、
  `mutation-probe-m0-stdout.txt`) → fix1d → probe2 (main=`051dae5cb`) で M0 SURVIVED。probe2 の M4 は rr20 (holdout 保護 ratio) で、gateway の保護層が smoke 全体を拒否し
  11 件余計に落ちて単一理由でなかった → rr95 へ再照準 (probe3)。M18 は [T-2632] 取り込み後に事前登録し probe4 (main=`83732738b`) で観測。

## 7. 受入全走・検査

- 焦点走 f1〜f4 は `focus/` (最終 f4 = 全緑)。全史 provenance 監査: 統合後 12,443 件・merge 後 12,475 件でいずれも新規違反なし。bytecode guard rc 0。
- **受入全走: 未実施 (本 insight の記録 commit 時点)。** 1 wave の job 合計が 2 node 時間以上になる投入はユーザーの事前確認が要る (2026-09-21 のユーザー指示、VLDB 方針控え項 4)。
  本 wave の積算は上限 ≈ 1.47 node 時間 (変異 job の queue 待ちを含む wall、焦点走 4 回の外側 wall、smoke 実測) で、受入 1 回 (3 shard × 13〜25 分 ≈ 0.65〜1.25) を足すと
  線を越えるため、確認を得てから投入する。

## 7. 受入全走・検査

(記録前に確定)

## 8. 設計 (実装しない) と scope 外・次の一手

- **LLM arm の親運用 (decisions「B-5 LLM arm の親運用」):** `LLM_WAIT_S = 2700` は変えない。LLM 系列 1 本に親 session 1 本 (系列開始前に確保、終了で context を廃棄、§4.1)、同時親数 p = 4 は運用上の選択。
  同時 LLM 系列 ≤ p。実効 handshake 期限 = min(2700, 残 walltime − 1800) s (poll 15 s)。親が止まった系列は登録どおり欠測 (救済しない)。
- **全 arm 同一 walltime (decisions「B-5 本走の job walltime」):** 探索 3 arm 共通 W = ceil(21,259 s × k)、block-stock は W_stock = ceil(5,447 s × k)。k は再提示でユーザーが決める (gen_S 上限から k ≤ 4.06)。

| 数値 | 出所 |
|---|---|
| 1 巡 10〜13 分 | 試走の実測 (1 系列 10 巡)。上限保証ではない |
| 2,700 s | 現行契約 (D2198) |
| 780 / 2700 ≈ 29% | 算術 |
| 36 系列 × 10 巡 = 360 巡 ≈ 60〜78 親時間 | 拒否なしの外挿 (A = 30 まで使えば最大 1,080 機会) |
| 21,259 s / 5,447 s | 試走の series / block-stock job Elapse の実測最大 (write-heavy・n = 1・Tier0 追加前・共有 lock 下) |

- **scope 外 (real、本 wave では直さない):** N1 — 投入済み (pipeline-submitted あり) の `duplicate-skip` を driver が `submitted=False` に戻し B が増えない (`b5_generator_contrast.py` の
  duplicate 分岐、既存 test も B=0 を期待)。D2198 の試走実装の既存挙動で、B-5 は slot ごとに campaign identity が別なので通常運用では到達しない。到達しても系列は分類不能欠測で止まる。
  発効束の段で D2200 項 1 (2) 4 の「重複 skip 拒否と B 消費を維持」の読みと合わせて確認する。
- **生死確認は未実施:** `test_b5_tier0.py::test_live_*` は job body の prebuild receipt と scratch submit-tree を要し、B-5 mode の短縮実行は試走 cohort 名の B-5 投入になる (未認可)。
  **次の一手 = 本走前の校正 job でこの live test を走らせ、Tier0 の perf build が pipeline 側で cache hit (bin_sha256 一致) し verify / bench が続くことを確かめる。**
- 発効束の残り: §12 の全項目の採取、calibrator での rep 1 高値 (warm-up) の確認、倍率 k と総 wall の倍率の再提示 (worklog の [T-2797] 項)。

## 9. 一次資料

- 依頼逐語・brief・段 4 / 段 6 裁定・codex 入出力: `verbatim/`
- 焦点走 log: `focus/`、smoke 実測: `probe/`、変異: `mutation/`
- 行末空白の可逆最小正規化 (`git diff --check` 対応、可視文字は不変): `NORMALIZATION.md` (7 file の原文 sha256・bytes・除去位置)、script は `normalize_trailing_ws.py.txt`
- 前段: `output/insights/2026-09-20/t2797-b5-contrast/README.md` §6 / §8、D2198 / D2199 / D2200、[T-2830] の insight `output/insights/2026-09-21/t2830-b5-node-local-lock/`、
  [T-2632] の insight `output/insights/2026-09-21/t2632-b4-evidence-carrier/`
