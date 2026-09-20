# pair job attempt-0001 (`13339.nqsv`) の診断メモ (親、2026-09-20 19:25 JST)

## 事実 (現物から)

- 投入: 19:12:26 JST、queue 待ち 10 秒、Started 19:12:36、Ended 19:13:45、Elapse 74 秒。host は `evidence/attempt-0001/reservation.json`。
  submit-tree `submit-tree-pair` HEAD `6a3e1580903434c734f050ed31738ade76d187e9` (= 着手時 local main、T-2795 launcher `c6eb77597` / `46cc32feb` を含む)、
  CCBench `511c9538…` (= `p3_s4_loop.PIN`、superproject gitlink は `e9e477ca…` のまま = T-2304 pin 前進後の main)。
- env: `IZANAGI_S4_STOCK_CONTROL=1`、proposal = round 3 の `proposal-4.json` (sha `bd3e5fd2…`、value 10)、K2 manifest wal-only (`396cd559…`)、
  `CODER_ROLE=coder-v4-autonomous-k2`、classification `known_result_conditioned_derivative`、de novo false。
- `compute-result.json`: `driver_rc=1` (= 候補 rc 0、stock rc 1 の集約。job body の `p3 S4 pair: candidate_rc=0 stock_rc=1`)。
- 候補 (driver 1 起動目): campaign `p3-s4-loop-s4-autonomous-b24749ae` (新 ID。round 3 の `409e13f8` と違うのは admission policy epoch が
  T-2304 で `949ddcc2…` → 新 sha に動いたため、T-2795 insight §0 の「identity の維持は約束しない」どおり)。
  variant `002642c7ac96`、build trace `6c87eb2ecf19686e` / perf `7a60310d588b89c7`、verify serializable (522,868 commits / 121,826 aborts / 0 anomalies)、
  bench median 811,956 tps (CV 0.98%)、`1 committed / 0 aborted / 0 skipped`、outcome=certified、iteration=1、停止判定 continue。
- stock (driver 2 起動目、`--stock-control`): stdout は `=== 段 4 stock control (stock_root=…/submit-tree-pair/external/ccbench, isolate_worktree=True) ===`
  の見出し行だけで outcome 行が無い。stderr の traceback:
  `_run_stock_control_resolved` (p3_s4_loop.py:1986) → `run_campaign` (loop.py:517) → `_authorize_measurement` (loop.py:236) →
  `campaign_claim.acquire_claim` (campaign_claim.py:430) →
  `ClaimError: campaign claim は既に 2080612 が所有している`
  (claim path `submit-tree-pair/output/env/pegasus/claims/p3-s4-loop-s4-autonomous-b24749ae.claim`、`FileExistsError` が直接原因)。
  pid 2080612 は候補側 driver process (同 job、既に終了)。
- したがって stock は condition gate (`_require_condition_gate`、stock 形) を正常復帰した後 (相談 A の訂正、traceback が `run_campaign` 内)、`run_campaign` の認可段で停止し build / verify / bench に到達していない。WAL は候補の 5 record だけ (`wal_outcomes.py` で実測、stock 期待 variant `602b4ce9c788` は不在)。
  **STOCK 成立 (inert、`src_token == STOCK`) は未確認**。pair は不成立。

## 機構の読み (code、worktree HEAD `6a3e15809`)

- `loop._authorize_measurement` は `reservation.is_reservation_required(contract.isolation_policy)` (Pegasus 計算ノード契約で真) のとき必ず
  `campaign_claim.acquire_claim(claim_root, record)` を呼ぶ。claim path は `<out_root>/env/pegasus/claims/<campaign_identity>.claim`
  (identity = `ident.campaign_id(bound_cfg)` = campaign dir 名)。
- `campaign_claim.acquire_claim` は module docstring「single-process campaign の one-shot claim leaf」、docstring「claim は crash 後も残す。stale 判定、
  自動削除、release は意図的に存在しない」。同 path は `O_EXCL` で作り、存在すれば所有者の生死を見ずに `ClaimError` (D464 の生存判定は
  **別 path の同 protocol digest** の走査 `_scan_protocol_conflicts` にだけ効く)。
- D2183 の設計「stock は候補と同じ campaign (同 identity・同 WAL) に `run_campaign` → `pipeline.evaluate` で入れる」は、同 out_root で
  2 つ目の process が同 identity の claim を取る形であり、one-shot claim leaf (D464 / D553 の single_process 強制) と構造的に矛盾する。
  T-2795 wave の test (TL: `_run_stock_control_resolved` の stub `run_campaign`、TJ: job body の static / 実 shell + stub driver、TV: pipeline の
  verify) はこの経路 (実 `run_campaign` の `_authorize_measurement` + reservation 必須契約) を通していない。T-2795 insight §0 は
  「1 job も投入していない」「実 compiler での STOCK 成立は未測定」と正直に書いていたが、claim 排他との矛盾は挙げていない。
- 同 campaign の候補の再評価 (`--run-iteration` の 2 回目) も同じ理由で同 out_root では通らない。K2 loop が毎巡 fresh tree だったのは
  walltime だけでなくこの claim でも必然だった (round 2 / 3 の記録は walltime を理由に挙げている)。

## 親の provisional 裁定 (攻撃対象)

- P-A: 「launcher も claim leaf も変えずに同 job・同 campaign の stock 対照を得る既存経路は無い」。
- P-B: ユーザー指示「成立しなければその走を対照成立と認定せず報告して止める (再投入で救済しない、launcher 改修は scope 外)」に従い、
  本 wave は 4 巡目を投入せず、記録 (round 3 README への pair 未達の追記、本 wave insight、worklog fragment、failures) と裁定パッケージ
  (launcher / claim の整合案) を残して正式停止する。
- P-C: 裁定パッケージの択: (i) job body が候補の driver 終了後に同 identity の claim を「同 job 内の直列再取得」として扱える経路を driver 側に足す
  (claim record の job_id / host / boot_id 一致 + 所有者 DEAD の同 identity path を通す = D464 の生存判定を同 identity path にも適用する拡張)、
  (ii) stock を候補と同じ driver process 内で評価する (1 process = 1 claim; `--run-iteration` に stock を続ける口)、
  (iii) job body が候補後に claim を退避 (rename) してから stock を起動する (「手動回収だけが裁定済み経路」に反するので却下候補)、
  (iv) stock を別 out_root (同 job・別 layout) で走らせ「同 job・別 campaign」の pair とする (D2183 の「同 campaign」を改める)。
- P-D: failures への記録型 = 「実機で 1 job も通していない launcher を裁定 (D2183) と共に land し、環境契約 (claim leaf) との矛盾を初回投入で発見」。
  既存 F に同型 (実機生死確認の欠落、説明と実装の食い違い) があれば再発追記、無ければ新 F。
- P-E: 候補 10 の再評価値 811,956 tps (2026-09-20、job 13339、tree 6a3e15809、policy epoch 新) は round 3 の 815,983 tps (09-19、job 10761、
  tree a99425b66) と別 tree・別日・別 policy epoch で、同時刻対照ではない。差 (−0.49%) を改善・退行の根拠にしない。記録には「4 走目の
  非同時刻点」として載せる。

## 訂正 (段 4 の相談 A と段 6 レビューの後、本文は当時のまま)

- 「機構の読み」3 点目の「TL: `_run_stock_control_resolved` の stub `run_campaign`」は不正確。`orchestrator/tests/test_p3_s4_loop.py` の stock 経路 test には実 `loop.run_campaign` を
  戻すものがある (verify option の伝達、COMMIT・digest 更新・再実行時 skip、非 STOCK evidence の admission 拒否) が、共通 fixture が site を `OTHER` (`linux-baremetal`、
  `single_process=False`) に固定するため `_authorize_measurement` の reservation / claim 分岐に入らない。欠落は「同 durable root・Pegasus 契約での候補→stock 連続起動」の結合検査 (相談 A #3、レビュー nit)。
- 「K2 loop が毎巡 fresh tree だったのは walltime だけでなくこの claim でも必然だった」は断定が強い。code が示すのは「既存 claim を残した同 out_root・同 identity の再起動が拒否される」
  ことまでで、claim の所在は output root に従う (fresh な source tree そのものの必要性は導けない) (レビュー should)。
