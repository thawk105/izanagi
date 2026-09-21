# [T-2795] 段 4 裁定 — plan v2 と変異事前登録 (2026-09-21 08:5x JST、base main 5efd69367)

入力: brief `s1-brief.md`、plan `codex/s2-plan.md` (08:37→08:46)、相談 A `codex/s3-consult-A.md` (lane sol、08:47→08:52、must-fix 1 / should 3 / nit 1)、
相談 B `codex/s3-consult-B.md` (lane luna、08:47→08:51、must-fix 1 / should 3 / nit 1)。裁定 inbox は wave 開始 (startup-gate.log の mtime) 以降の更新 0 件。
local main は docs のみ 4 commit 前進 (`21641fee7`、DW-M08 self-run 手順の改訂) — 段 6 の変異直前に main 側の DW-M08 を読む。

## 1. 所見の裁定

| ID | 所見 | 裁定 | 処置 |
|---|---|---|---|
| A-R1 | `loop.py` / `p3_s4_loop.py` は 85 path closure に入り、v2 campaign lock 作成時に live bytes = HEAD blob を要求 (`ident.py:584` → `contract_loader_binding.py:518`)。変異 harness は固定 HEAD へ bytes を注入するだけ (`tools/mutation_harness.py` 冒頭 docstring) なので、lock を作る test は変異の内容に関係なく `contract-loader-drift` で落ちる | **real / must-fix** (親が code で確認) | §3 の変異を 2 群に分ける。注入群は lock を作らない test (認可 sink を直接 2 回呼ぶ単体、run_campaign stub の CLI test、job contract) だけを対象集合にし、等価対照 M0 が SURVIVED になることで drift 非感応を実証。結合検査を殺す性質は scratch commit に変異を焼いた commit 群 probe で測る。closure 照合・resumability は stub しない |
| A-R2 | session 個体の発行証明・失効の契約不足 (同型コピー・close 後の別名参照) | real / should | 採用: module-private の発行台帳 (object identity) + 発行 pid、`close()` は不可逆、`with loop.authorization_session() as S:` で例外時も close、`__copy__` / `__deepcopy__` / `__reduce_ex__` は拒否、S 内部の receipt は caller から変更不能な保存形 |
| A-R3 | 冗長な比較を独立 KILLED と数えない / 別 process・fork の代表性 | real / should | 採用 (B2 と統合): §3 は性質単位。identity / 契約 sha / root / use class は claim path・protocol digest と冗長なので個別削除変異は登録しない。pid は `os.getpid` を loop module 内で差し替える模擬負例とし、実 fork 負例は採らない (pair mode は構造上 1 process、同 process 内の任意改変は防壁の対象外 — A-R2 自身の限定)。insight に限界として明記 |
| A-R4 | 候補の検疫 reject は claim 前に WAL を書く (既存経路) | real / should (記録のみ) | 本 wave の保証は「single_process 下の測定用 `run_campaign` は claim 取得または session 所有再確認を経る」に限定。reject WAL を claim 下へ移す件は研究前進・実測欠陥を示せないので裁定パッケージにせず insight に記録 |
| A-R5 | 「時間予算の述語は無い」は不正確 | real / nit | brief の記述を「新たな完走時間予算は足さない。既存の残時間 1 秒以上の presence 検査を各 sink 到達時に再検査」に訂正 (insight に反映) |
| B-B1 | 結合正例が「両評価成功」を固定していない | **real / must-fix** | 採用: 候補 `certified`・stock `certified-stock`・driver rc 0、同一 WAL に両 variant の BUILD_START / BUILD_DONE / VERIFY_DONE / BENCH_DONE / COMMIT、stock の variant と `src_token == STOCK`、build / bench stub が両 arm で候補→stock 順、claim 取得 1 回・stock 後も同 record。commit 群に「stock の bench を落とす」変異を追加 |
| B-B2 | 重複防御を独立変異と数えない | real / should | A-R3 と統合して採用 |
| B-B3 | 「変更行数で最小」は未算定 | real / should | 採用: 主張は「既存の 2 評価経路と責務を保つ最小設計」に限定。他 driver の自動 session 化・汎用 registry・永続台帳・callback framework は作らない |
| B-B4 | fixture + stock の拒否は既存契約 (README §7、job contract 正例) の縮小 | real / should | 採用: 理由を「今回修復する production 入力は proposal。fixture pair の新規対応は広げない」と記録し、README §7 を更新。fixture 単独・stock 単独 (B-5) は維持 |
| B-B5 | 被覆数・条件判定の根拠の限定 (caller は 17 file・22 call、09 の sha 出現は loop / shell のみ確認) | real / nit | 採用: insight で「約 19 driver」→「17 file・22 call (`test_campaign.py` の semantic inventory)」、09 は「loop.py の現 sha は A-1 受領証、shell の現 sha は B-5 reservation 記録に出現、p3_s4_loop.py の現 sha は出現を確認できず」と訂正。結論 (凍結物の bytes は変わらない) は不変 |
| 両相談の refuted 候補 | 実効性・二重適用・共有 cache・policy 同値・B-5 単独口・S 偽造 / 持出し / 別 identity | refuted (相談の判定を採用) | — |
| B 追加 | `docs/paper-story/README.md` の「修復方向は裁定パッケージ」に修復 insight への日付付き導線 | real / nit | 段 7 で 1 行 (過去の稿・数値は不変) |

未裁定だった plan の残件 2 点: (1) receipt 再利用 = plan どおり採用 (required 契約は verified calibration を再ロードし `receipt_matches_contract` で保存 receipt を再検算、新 receipt は発行しない)。
(2) 候補の通常例外 = 採用 (候補 step は `Exception` だけを捕捉して stderr に traceback、stock を試行してから候補例外を再送出。stock 例外は併記。`BaseException` は捕捉しない)。

## 2. plan v2 (plan からの差分と確定事項)

**A1 — `orchestrator/campaign/loop.py` + `orchestrator/tests/test_campaign.py`**
- `authorization_session()` (context manager、module-private 発行台帳に object identity と発行 pid を記録、exit で不可逆 close) と opaque な session 型。コピー / pickle 拒否。
- `run_campaign(..., authorization_session=None)` (keyword-only)。None のときは現行経路と呼出し順が完全不変 (`test_campaign.py` の既存 order assert を更新しない)。
- `_authorize_measurement` に session 経路: 未束縛なら現行どおり取得し、**認可成功直後** (perf preflight・layout・evaluate より前) に束縛。束縛済みなら plan §1「再利用時の検査」表の全項目を現在の入力から再計算して照合し、claim 取得だけを省く。不一致は layout / lock / WAL / evaluate より前に `execution_guard.ExecutionGuardError` (または loop 内の専用 subclass) で拒否。救済取得・新 S への移植はしない。
- claim record の読取りは `campaign_claim` の既存 reader (read-only) を使う。`campaign_claim.py` の bytes は不変。
- 単体 test は **`_authorize_measurement` を直接 2 回呼ぶ形** (campaign lock を作らない) を主にする (A-R1)。run_campaign 2 回 + S で claim 1 回・evaluate 2 回の test も 1 本置く (commit 済み状態でのみ有効、注入群の対象集合からは外す)。

**A2 — `orchestrator/campaign/p3_s4_loop.py` + `tools/pegasus/p3_s4_loop_pegasus.sh` + `orchestrator/tests/test_p3_s4_loop.py` + `orchestrator/tests/test_p3_s4_loop_job_contract.py`** (必要時のみ `test_p3_exploration_namespace.py` / `test_p3_b4_wiring_probe.py` の実数再集計)
- pair mode = `--run-iteration P --stock-control` (+ `--isolate-worktree` 必須)。pair で禁止: `--value` / `--emit-planner-context` / `--no-build` / `--b4-reflux-ablation` / `--b5-slot` / `--machine-generated-proposal`。`--coder-role` / `--allow-coder-derived-build` は候補だけ、候補の opt-in 必須は維持 (plan §2 の 3 箇所)。stock 単独 (B-5) は argv・挙動とも不変。
- 候補 context (authority 付き) と stock context (authority 無し) を別に作り policy 一致を測定前に要求。stock は `_stock_capability_resolver(stock_context)`。
- worktree: 候補 checkout を抜けてから stock 用に新しい checkout を作る。stock_root は clean な `fixed_sub`。
- 1 つの `with loop.authorization_session() as S:` が候補 step と stock step を包む。S は `drive_iteration` → `_run_one_iteration_resolved` → `run_campaign`、`_run_stock_control_resolved` → `run_campaign` へ、非 None のときだけ渡す (既定 kwargs は exact 不変)。
- 例外・rc・stdout は §1 残件 (2) と plan §3 / §5 のとおり。最後に `p3 S4 pair: candidate_rc=X stock_rc=Y`。rc は候補非零優先、候補 0 なら stock rc (0 は `certified-stock` のときだけ)。
- job body: `IZANAGI_S4_STOCK_CONTROL=1` かつ proposal 無しは prebuild / trap 前に rc=2。proposal 起動に `--stock-control` を足した 1 起動だけ、独立 stock 起動と shell 集約を削除し driver rc をそのまま exit。未設定 / 0 の argv は bytes 不変。B-5 分岐不変。
- 結合検査 `test_pair_main_pegasus_real_claim_and_wal` (main 経由): plan §6 の stub 境界 (実: run_campaign / `_authorize_measurement` / session 検査 / `require_certified_writer_authorization` / `acquire_claim` / reservation / identity / layout / campaign lock / WAL / `pipeline.evaluate`。代用可: build・trace 実行・bench・attestation 観測・condition gate・patch 適用・checkout・compiler 依存の SourceEvidence・perf preflight)。SourceEvidence は root 依存 (候補 root → 非 STOCK、stock root → STOCK) にして stock の root 誤配線を検出可能にする。assert は §1 B-B1 の全項目 + 候補 checkpoint / whiteboard が stock で不変 + stdout に両 outcome。
- 負例 (A2): pair × B-5 / B-4 / value / emit / no-build / machine-generated を main 経由で副作用前に rc=2、候補 quarantine reject 後も stock が初回 claim を取り測定へ到達、候補の認可後例外でも stock 測定・claim 取得 1 回・候補例外の再送出、job body の 1 起動と fixture pair の rc=2。

**親 (段 7):** `tools/pegasus/README.md` §7、`docs/phase3.md` 該当行、F1019 (結合検査の追加と模擬範囲: 「認可 / claim 結合の再発検査を追加。実 compiler の STOCK 成立、実 checkout / patch と build の統合、Pegasus production pair は未実施」)、
paper-story README の導線 1 行、修復 insight、decisions / worklog fragment。

## 3. 変異事前登録 (DW-M01、実装前、性質単位)

**注入群 H** — 固定 HEAD への bytes 注入。対象集合は campaign lock を作らない test に限る (A-R1): `test_campaign.py` の session 単体 (`_authorize_measurement` 直呼び)、
`test_p3_s4_loop.py` の pair CLI test (run_campaign stub)、`test_p3_s4_loop_job_contract.py`。node は実装後に確定し、期待 node 集合は exact 照合。

| ID | 位置 | 変異 (性質) | 向き | 殺す test (見込み) |
|---|---|---|---|---|
| M0 | loop.py | comment 1 行 (等価対照、drift 非感応の実証) | 等価 | SURVIVED 期待 |
| M1 | loop.py 再利用経路 | 束縛済み S を検査なしで受理 (再利用検査を丸ごと外す) | 負 | session 負例群 |
| M2 | 同 | claim record 内容の照合を外す (`created_utc` だけ違う record で単独理由化) | 負 | claim record 改変の拒否 |
| M3 | 同 | reservation の再検査を外す | 負 | 初回と再利用の間の期限切れ拒否 |
| M4 | 発行台帳 | 発行台帳の照合を外す (偽造・コピー S を受理) | 負 | foreign / copied session 拒否 |
| M5 | close | close を可逆にする (close 後の S を受理) | 負 | closed session 拒否 |
| M6 | 同 process | 発行 pid・record pid の照合を外す (両方で 1 性質) | 負 | pid 不一致 (模擬) 拒否 |
| M7 | receipt | 保存 receipt の再検算を外す | 負 | receipt 再検算失敗の拒否 |
| M8 | pre-write validator | 再利用時に validator を呼ばない | 負 | validator の再実行 |
| M9 | 束縛時点 | 束縛を評価成功後へ遅らせる | 負 | 認可後例外 → 次の認可が claim 1 回で通る |
| M10 | 再利用経路 | 正しい束縛でも拒否 (過剰拒否) | 正 | session 正例 |
| M11 | S 無し経路 | S 無しでも同 pid の既存 claim を再利用 (旧 2 起動形が通る) | 負 | S 無し 2 回目の `ClaimError` |
| M12 | p3_s4_loop.py CLI | pair × B-5 の拒否を外す | 負 | pair × B-5 rc=2 |
| M13 | 同 | pair 候補の coder opt-in 必須を外す | 負 | opt-in 無し pair の拒否 |
| M14 | 同 | stock に候補 context (authority 付き) を渡す | 負 | stock context に authority 無しの assert |
| M15 | 同 | stock に候補 checkout を再利用 | 負 | stock は新 checkout の assert |
| M16 | 同 | 候補例外で stock を試さず return | 負 | 候補例外後の stock 試行 |
| M17 | 同 | stock rc を常に優先 | 負 | 候補非零優先 |
| M18 | 同 | stock の run_campaign に S を渡さない | 負 | 同一 S が両 run_campaign に届く spy |
| M19 | job body | 旧 2 起動へ戻す | 負 | job の driver 1 起動 |
| M20 | job body | fixture + STOCK_CONTROL=1 を受理 | 負 | fixture pair の rc=2 |
| M21 | job body | 既定でも `--stock-control` を足す | 正 | 既定 argv exact |

**commit 群 C** — 変異を scratch commit に焼き (live = HEAD、closure 整合)、結合検査を走らせる。期待 = 結合検査 node だけが赤 (他は緑)。

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| C1 | p3_s4_loop.py | stock の run_campaign に S を渡さない | 結合検査が `ClaimError` で赤 (F1019 の再現) |
| C2 | loop.py | 束縛済み S でも claim を取りに行く | 結合検査が `ClaimError` で赤 |
| C3 | p3_s4_loop.py | stock の bench を落とす (`do_bench=False`) | 結合検査が stock BENCH_DONE 欠落で赤 (B-B1) |

単一理由性 (DW-M01) は実装後に各変異の拒否点で確認し、冗長で生き残るものは登録から外して記録する。fix 後は DW-M07。

## 4. 実行順

A1 (Codex author) → 親が統合 commit → A2 (Codex author、A1 commit 起点) → 統合 commit → 焦点走 (計算ノード) → 段 6 レビュー 2 本 → fix → 変異 (H 群: harness、C 群: scratch commit probe) → 受入 → 記録 → land。
生の計測 job (pair 再投入・4 巡目) は投入しない。
