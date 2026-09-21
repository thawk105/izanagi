# [T-2795] 段 6 裁定 — レビュー 2 本の所見と焦点走 1 の赤 (2026-09-21 09:5x JST、統合 tip 47b38fb06)

入力: `codex/s6-review-A.md` (正しさ境界、NO-GO、新規 must-fix 1 / should 2)、`codex/s6-review-B.md` (実効性と過剰、NO-GO、新規 must-fix 1 / should 2)、
焦点走 1 (`focus-1.log`、job 14717.nqsv、rc=1、失敗 100 = wiring probe 18 + job contract 72 + 結合検査 3、内訳は HANDOFF.md)。

## 1. 所見の裁定

| ID | 所見 | 裁定 | 処置 (fix 単位) |
|---|---|---|---|
| A-R1 / B-B1 | 変異 M4 (発行台帳の membership 検査を外す) は、直後の `_AUTHORIZATION_SESSIONS[session]` が `KeyError` / `TypeError` で落ちるので「偽造 session の受理」を証明しない | **real / must-fix** | 採用。M4 を性質変異へ再登録: 未発行・コピーの session を**受理して新たに束縛する**形 (`membership 検査を消し、欠落時に新規 entry を作る`) にし、負例 (未発行・コピー) が「claim 取得 0・`ExecutionGuardError`」で殺すことを確認する。例外型が違うだけの赤を権限受理の拡大として数えない |
| A-R2 / B-B2 | 変異 M18 の H 群検査が字面 (代入文と `**campaign_options`) だけで、転送の実効性を示さない | real / should | 採用 (fix2)。`run_campaign` を捕捉して `_run_one_iteration_resolved` と `_run_stock_control_resolved` を実行し、**同一の session object が両方へ届く**ことを確かめる挙動検査を H 群に置く (campaign lock 作成前で捕捉するので A-R1 と両立)。字面 pin は残すなら保証を「指定した代入削除の検出」に限定する |
| A-R3 | 初回 `_authorize_measurement` も `try` の内側にあるため `ClaimError` が `ExecutionGuardError` に包まれ、裁定 §3 の C2 の期待 (`ClaimError` で赤) と食い違う | real / should | 採用 (fix1)。**初回取得の例外は包まず透過**させる (変換は再利用検査の失敗だけに限る)。これで S 無し経路・pair の初回取得・C1 / C2 の期待が同じ型で揃う |
| B-B3 | 焦点走の対象から B-4 の実 consumer (launcher・proposal binding・closed critic・raw record producer・material report) が漏れている | real / should | 採用。焦点走 2 の対象に追加する (`test_p3_b4_launcher.py`、`test_p3_b4_proposal_binding.py`、`test_p3_b4_closed_critic.py`、`test_p3_b4_raw_record_producer.py`、`test_p3_b4_material_report.py`、`test_p3_s4_loop_sort.py`、`test_p3_s4_loop_trigger_gating.py`) |
| 既知赤 (a) wiring probe 18 node | `validator = kwargs["pre_write_validator"]` → `validator(identity)` が静的目録の「未解決ローカル代入の呼出し」に当たる | real / must-fix (実装起因) | 採用 (fix1)。**`pre_write_validator` を明示の keyword parameter にして parameter 呼出しとして表現**する。検査器 (`p3_b4_wiring_probe.py`) を緩めない・目録から除外しない。新設の `_run_stock_cli_step` も生成経路の逆到達集合に含まれることを確認する |
| 既知赤 (b) job contract 72 node | 契約断片の欠落集合が 1 つ増える。無変異の source 自体が旧 proposal 断片と一致していない | real / must-fix (実装起因) | 採用 (fix2)。欠落集合へ機械的に `proposal` を足す対症療法は不可。**各 pin の責務を分け** (共通 proposal 断片・pair argv・K2 展開・stock mode)、無変異の正例を先に緑にしてから変異期待を更新する (`test_p3_s4_loop_job_contract.py` の :459 / :708 / :1460 付近) |
| 既知赤 (c) 結合検査 3 node | 較正 samples をそのまま観測値へ複製しており、比較器が「較正中央値に対する各 sample の許容幅」を見るため外れ値 3080.935 で失格 | real / must-fix (実装起因) | 採用 (fix2)。**較正中央値から合成した観測**へ直す。実 `attest_and_build_receipt` / `receipt_matches_contract` は維持し、実認可・reservation・claim・layout・campaign lock・WAL・`pipeline.evaluate` の結合は残す |
| B 提案 (削る候補) | session 転送の逐語 pin、保存 record の pid / digest の重複比較、checkpoint bytes 比較後の重複 whiteboard assert | real / should | 採用 (fix1 / fix2)。重複検査は削るか、独立 KILLED として数えない旨を変異台帳に書く。受理集合を変える検査は削らない |
| 両レビューの本体経路評価 | claim 防壁・stock 成功条件・CLI 排他・job body の 1 起動・削除の妥当性に新規の破れなし | refuted 候補 (支持) | 変更なし |

## 2. 変異事前登録の更新 (段 4 §3 からの差分)

- **M4 → M4'**: 「未発行・コピーの session を受理して新規に束縛する」変異 (membership 検査を外し、欠落時に entry を作る)。期待 = 未発行・コピーの負例が KILLED、claim 取得が 0 であること。
- **M18**: 挙動検査 (同一 session object が両 `run_campaign` へ届く) を殺す形に変更。字面 pin は補助。
- **C2**: 期待を「初回取得の `ClaimError` がそのまま上がる」に統一 (A-R3 の fix 後)。C1 と同じ型で集計してよい。
- 他の M / C は段 4 のまま。fix 後に DW-M07 に従って anchor を取り直す。

## 3. fix 単位 (所有素集合、並列)

- **fix1** (worktree `t2795r-unit-a1`、所有 `orchestrator/campaign/loop.py`、`orchestrator/tests/test_campaign.py`): 赤 (a) の validator 明示引数化、A-R3 の例外透過、重複比較の整理、M4' が成立する形。
- **fix2** (worktree `t2795r-unit-a2`、所有 `orchestrator/campaign/p3_s4_loop.py`、`tools/pegasus/p3_s4_loop_pegasus.sh`、`orchestrator/tests/test_p3_s4_loop.py`、`orchestrator/tests/test_p3_s4_loop_job_contract.py`):
  赤 (b) の job contract pin の責務分離、赤 (c) の attestation 合成観測、M18 の挙動検査。
