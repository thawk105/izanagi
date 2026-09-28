# [T-2871] 段 4 裁定 (親) — 2026-09-28 08:18 JST (file mtime)

入力: s1-brief.md、codex/plan-a.md・plan-b.md (段 2)、codex/consult-a.md (正しさ境界)・consult-b.md (実効性・過剰) (段 3)。
裁定 inbox の再走査: local main は wave 開始時の 51f896352 から進んでいない。T-2871 に関わる新しい裁定は無い (worklog 837 行の起票文のみ)。

## 1. 設計 (plan v2)

- **採用: 案 1 (P1)。** plan-A・plan-B が独立に同じ案へ収束し、plan-B の 3 案比較で案 2 (K2 型: job ごとに別 out_root) は系列状態の出所が tree をまたぐため、案 3 (B-5 型) は pair を 1 測定点と定義すれば案 1 と同型になるため、それぞれ退けた。
- **受理単位の変更 (段 7 で decisions に記録):** Pegasus の one-shot claim の単位を「loop 系列に 1 本」から「系列の iteration に 1 本」へ移す。claim leaf (`campaign_claim.py`) の bytes・release/stale なし・同じ path の `O_EXCL` 拒否は不変。同じ計測 identity の 2 度目は従来どおり `ClaimError`。
- **計測 identity:** pair 経路 (`--run-iteration --stock-control`) だけで、系列 cfg の `search_config` に `policy_iteration` (正整数 `int`、値 = その pair が消費する系列 iteration 番号) を足した計測 cfg を作る。`default_cfg`・bootstrap・r2・record-reject・emit-coder-input・preview・非 pair の `--run-iteration`・`--replay-proposal` の cfg と layout は不変。
- **番号の出所:** 系列 layout の `loop_state.json` の counter だけ。argv では受けない。`main` の pair 分岐が系列 state を 1 度読み、その `iteration + 1` から計測 cfg / layout を導き、同じ state object を `drive_iteration` に渡す (再読込しない)。
- **layout の割付 (consult-B must-fix 1 を実装要件とする):**
  - 系列 layout: `loop_state.json`・`policy_history.jsonl`・`silo_policy_loop_digest.txt` の保存先・停止判定。
  - 計測 layout (候補と stock で同一): 候補の `ensure_resumable_attempts`、gate reject の WAL (`L.record_diff_reject`)、候補の `run_campaign`、`_result_history`、critic digest の admitted view (`require_admitted_campaign` と `make_critic_identity_projection`)、stock の `ensure_resumable_attempts`・`run_campaign`・`_stock_result`。
  - 候補と stock は同じ計測 cfg と同じ authorization session を使う。候補が例外で終わっても同じ計測 cfg / layout / session で stock を試みる (現行どおり)。`stopped-before` では stock を呼ばず、計測 claim も作らない (現行どおり)。
- **強制終了の窓 (consult-A must-fix): real・scope 内。** 現行は counter の保存が `finally` だけ (driver:444・465) で、claim 取得後に SIGKILL (PBS の walltime 超過など) されると系列 state が旧番号のまま残り、次の job が同じ計測 identity を選んで `ClaimError` で止まり続ける。復旧は claim の手動退避 (依頼で禁止) か state の手編集しかなく、「claim を退避せず複数 iteration 回す」という依頼の目的そのものを壊す。**修正: `drive_iteration` で counter を進めた直後、計測より前に系列 `loop_state.json` を保存する** (`finally` の保存は残す)。強制終了した番号は欠番になり、系列履歴にその番号の行は残らない (計測 dir と claim file は証跡として残る)。gate・台帳・再測定契約は足さない。欠番の読み方は runbook §3 に書く。
- **critic digest (consult-A should): 受け入れる。** digest の材料は当該 iteration の計測 campaign の admitted WAL (候補だけ。stock は従来どおり digest 作成後なので入らない) になり、過去 iteration と login の record-reject は digest から消える。coder は系列履歴 (`self_history`) で系列全体を見続ける。系列 WAL へ複写する代案は lock・admission の整合を新しく扱うため採らない。runbook §1(g) に材料の範囲を明記する。
- **番号と計測 dir の対応 (consult-A should): 最小で採用。** 系列履歴の行と driver の stdout JSON に `measurement_campaign_id` (pair の行だけ文字列、他は `null`) を 1 field 足す。coder 入力の射影 (`make_policy_coder_input` の 7 key) には入れない。新しい台帳は作らない。
- **系列 dir を certified campaign として読まない (consult-B should):** runbook に書く (docs、親)。
- **完了判定 (consult-B should):** 生死確認は各計測 dir の候補・stock の WAL、各 job stdout の stock `certified-stock`、系列 state の iteration と履歴行を突き合わせる。job の `driver_rc` だけで判定しない。

## 2. brief の訂正 (consult-A・B が指摘、全件 real)

- 「終端済みの variant は skip」→ retryable abort を除く terminal (loop.py:779-787)。stock の既存 commit が skip される主張は維持。
- 「loop の状態を job をまたいで継続した Pegasus の先例は無い」→「確認した K2 (T-2795)・B-5 (T-2797)・T-2849・T-2850・方策系列 A/B の実走は、いずれも job をまたいで loop 状態を継続していない」に限定する。
- 「同じ iteration を 2 度測れば ClaimError」→ 同じ計測 identity (同じ番号・同じ cfg・同じ out_root) を再使用した場合に限る。通常の次回起動は counter が進む。
- 負例「iteration key を外すと ClaimError と stock skip」→ 2 本目は claim で止まり stock skip には到達しない。負例の期待は ClaimError だけ。
- 見積り ≈ 3,722 s (≈ 1.03 node 時間) は成功例の単価に基づく計画値。再投入分は発生時に加算する。

## 3. scope

- scope 内: driver (`orchestrator/campaign/p3_s4_loop_policy.py`) と焦点 test (`orchestrator/tests/test_p3_s4_loop_policy.py`) を Codex author 1 本が書く。runbook §1(0)(f)(g)・§3 は親。
- 変えない: `loop.py`・`campaign_claim.py`・`p3_s4_loop.py`・job body・`tools/pegasus/README.md`。run_campaign の呼出し 2 本。正しさゲートの順序と受理集合。
- scope 外 (起票しない、insight に記録): 同じ系列への並行投入の番号予約、強制終了した番号の再測定契約、系列全体の admitted digest の再構成、生成器対照の系列制御 (事前登録文書の不足部品)、walltime 予算の変更。

## 4. 焦点 test (実装子へ)

- 既存 test は全面書換えしない。pair の cfg/layout 引渡しを見る test (test_p3_s4_loop_policy.py:599 付近) を 2 layout 契約へ合わせる。
- 新しい結合検査: 1 つの使い捨て out_root と proposal を用意し、driver `main([... --campaign-env pegasus --run-iteration <p> --stock-control ...])` を **別 process で直列に** 呼ぶ。子 process は `python -c` か小さな harness script で、既存 pair fixture (test_p3_s4_loop.py:11565 付近、test_p3_s4_loop_policy.py:599 付近) の site・attestation・build・trace・bench の差し替えだけを適用する。`loop._authorize_measurement`・`campaign_claim.acquire_claim`・`reservation.check_reservation`・`loop.authorization_session` は実物。数秒で終わる形。
  - T1 (正例 2 本): 2 process の後、`<out_root>/env/pegasus/claims/` に別名の claim が 2 file、両 stdout の stock が `certified-stock`、各計測 dir の WAL に候補と stock の attempt、系列 `loop_state.iteration == 2`、系列履歴が iteration 1・2 の 2 行で各行の `measurement_campaign_id` が対応する計測 campaign、系列 dir の digest が 2 本目の計測 WAL 由来 (2 本目の候補 variant を含む)。
  - T2 (強制終了): 1 本目の子を claim 取得後 (例: 差し替えた build の中) に `os._exit` で落とし、次の子が次の番号で新しい claim を取り、候補・stock とも評価されること。系列 state は iteration 2、履歴は 2 本目の 1 行だけ。
  - T3 (one-shot 不変): 同じ計測 identity の再使用 (系列 state を 1 本目の直前へ戻して再実行) は実 `ClaimError` で止まり、新しい計測 attempt が増えない。

## 5. 変異の事前登録 (DW-M01、実装後に単一理由性を確かめ、成り立たなければ登録を外して再照準する)

| id | 壊す箇所 | 赤になるべき assert |
|---|---|---|
| M1 | pair の計測 cfg に `policy_iteration` を足さない (系列 cfg のまま計測) | T1 の 2 本目が `ClaimError` / claim 2 file |
| M2 | counter の計測前保存を外す (`finally` だけに戻す) | T2 の 2 本目が `ClaimError` |
| M3 | `_stock_result` に系列 layout を渡す | T1 の stock `certified-stock` |
| M4 | 系列 state・履歴の保存先を計測 layout にする | T1 の系列 `loop_state.iteration == 2` / 履歴 2 行 (1 本目直後に見る) |
| M5 | critic digest の admitted view を系列 layout に戻す | T1 の digest が 2 本目の計測 WAL 由来 |

## 6. 計算ノードの生死確認 (段 6 後、親)

- 受入済みの tip から新しい submit checkout を作り (HEAD と骨格 patch の SHA-256 を確認)、login で `prop-2.json`・`prop-3.json` (`output/insights/2026-09-27/t2865-silo-policy-iter2/verbatim/llm/`) の preview を取り、auditor digest が一致することを確かめてから、pair job を `prop-2` → (完了後) `prop-3` の順に直列投入する。bootstrap は省く。**liveness 専用系列**と明記し、系列 A・B や研究系列の値と合算しない。
- 判定: §1 の完了判定 (WAL・stdout・系列 state・履歴を突き合わせる)。
- 見積り: 計画値 ≈ 3,722 s ≈ 1.03 node 時間 (pair 1,572 + 焦点走 200 + 変異 750 + 受入 1,200)。2 node 時間を超えそうになったら投入前に止めてユーザーに確認する。
