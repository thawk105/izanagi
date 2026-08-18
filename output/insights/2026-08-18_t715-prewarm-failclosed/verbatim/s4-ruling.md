# 段 4 裁定 — [T-715] prewarm + fail-closed

親裁定日時: 2026-08-18 13:30 JST / base main `a160f4aa`
入力: `s1-brief.md`、`s1-measurement.md`、`m5-baseline.md`、`m8-q-compute.md`、`m9-critical-path.md`、
`s2-plan.md`、`s3-lensA.md`、`s3-lensB.md`

**判定: 実装する。ただしプラン v2 として下記 must-fix を必須にする。**
ユーザー裁定 (b) は不変で、別案へ戻さない。

---

## 1. 所見の裁定

| # | 所見 | real/refuted | 採否 | 根拠 |
|---|---|---|---|---|
| A1 = B1 | worker 側でも `pytest_collection_finish` が発火し worker ごとに prewarm する | **real** | **採用 (must-fix 1)** | 2 レンズが独立に同じ順序 (`remote.py:256-262` → `dsession.py:274`) を引いた。親も待機中に独立に指摘していた |
| A2 | 公開 consumer 経路の fail-closed は撤去しても全 planned test が緑になりうる (F366 型) | **real** | **採用 (must-fix 2)** | `_resolve_now` caller allowlist と private memo の miss test だけでは、公開 alias の例外 fallback を検出できない |
| A3 = B2 | conftest と consumer の memo module identity が機械固定されていない | **real** | **採用 (must-fix 3)** | 非修飾 import と canonical import は別 module object。分裂すれば 35 node が赤 |
| A4 | conftest の eager canonical import が既存契約 (`test_pytest_failure_digest.py:335`) を壊し、import 0.84 秒が consumer なし焦点走に乗る | **real** | **採用 (must-fix 4)** | conftest は repo root 外から単体 import される契約を持つ |
| A7 | 任意値 `--testrunuid` (`ci-job-42` 等) が新設検査で赤になる | **real** | **採用 (must-fix 5、縮小形)** | xdist は charset を制限しない。**UID を検査せず内容 hash から cache 名を作る**形に変え、正当な UID を拒否しない |
| A9 | prewarm 例外が隣接する `except Exception: pass` に飲まれ、診断が `cache-missing` へ潰れる (F389 型) | **real** | **採用 (must-fix 6)** | 既存 hook に実在する握り潰しの内側へ置いてはならない |
| B5 | `-p no:xdist` で xdist option が存在しない場合の guard が無い | **real** | **採用 (must-fix 7、1 行)** | `config.getoption("testrunuid", None)` の既定値付き参照で閉じる |
| B8(a) | `_prune_stale_caches` が prefix 全体を glob し、生きた lock file も unlink しうる | **real** | **採用 (must-fix 8)** | prune 対象を pickle cache に限り、現 session の key は除外する |
| B9 | 変異 M7/M8/M10 の期待 node が実 runner 範囲と対になっておらず MISMATCH を作る | **real** | **採用 (変異事前登録で解決)** | §3 で期待 node 集合を実 runner 範囲と対にして登録する |
| A5 | prewarm は汚染を 1 回に閉じると同時に全 consumer へ配る | **real** | **仕様として受容・記録のみ** | 裁定 (b) が選んだ設計の帰結そのもの。不変条件の言い方を §2 で訂正する |
| A10 | プランは「worker 起動前」を「test scheduling 前」へ弱めている | **real** | **採用 (等価性をコードで確認したうえで縮小を明示)** | §2 で扱う |
| A11 | T-813 引用は holdout scan 汚染の直接証拠でなく、110 は payer 数でない | **real** | **記録訂正のみ** | `output/pegasus-dispatch/` は `.gitignore` 済みで `--exclude-standard` から外れる。payer は 32 関数 / 35 node |
| A8 = B4 | 1.1 倍の静的上界がプランの q 取り違えで誤り | **real** | **採用 (land 条件を実測に一本化)** | 計算ノードの q = 19.70 秒で `173.10 + 19.70 = 192.80 秒` = 1.114 倍 > 閾値 190.41 秒。**静的上界では合格を主張できない** |
| A6 | pickle が型検査前に任意 reduce を実行する | **real** | **不採用 (scope 外・ユーザーへ返す)** | wave 前から在る信頼境界の穴で、本 wave が作ったものではない。closed-schema codec への置換は memo の外形を変えるため別 wave。裁定パッケージへ |
| B3 | production CLI 子プロセスは prewarm の対象外 | **real** | **不採用 (scope 外・主張を縮小)** | brief が既に R-e を scope 外としている。**S3 の「全実行経路」を「pytest session 内の全経路」へ縮める** |
| B7 | infrastructure 障害と test 失敗を結果レベルで区別できない | **real** | **一部採用** | 構造化 message (`IZANAGI_RECEIPT_MEMO_FAIL_CLOSED_V1` + JSON) までは採用。runner の rc 体系を増やす案は `tools/run_tests.py` の契約変更なので scope 外・ユーザーへ返す |
| B6 | `--forked` と worker crash 再起動 | **一部 real** | **不採用 (DW-G04)** | pytest-forked は未導入で `run_tests.py` も扱わない。発火条件を実在 artifact で書けないので設計メモに留める。crash 再起動は同じ read-only 経路を通るだけなので新機構を足さない |
| B8(b) | ノード跨ぎ shared FS の lock semantics | **refuted (この環境では)** | 不採用 | dispatch は 1 job = 1 計算ノードで controller と worker が同一ノード・同一 `/tmp` に居る。跨ぎ構成は存在しない |

## 2. brief の訂正 (親自身の穴)

- **(訂正 1) 不変条件の言い方。** 「本番 resolver の戻り object そのものだから受理集合不変」は時点を落としている。
  正しくは **「固定 snapshot X に対して全 memo consumer が同じ `R(X)` を観測する」**。
  prewarm はこの X を session 開始側へ寄せる変更であり、値の同一性ではなく**時点の同一性**を強める。
- **(訂正 2) 「worker 起動前」は実装不能。** xdist は `pytest_sessionstart` で worker を起動し
  (`dsession.py:83-91`)、controller は item を collect しない (`dsession.py:103-105`)。
  裁定 (b) の字面「worker 起動前」をコードで満たす経路は存在しない。
  **本 wave が満たすのは「test body が 1 本も走る前」**であり、
  裁定の目的 (session 中に production 経路が実 repo を再解決しない) はこれで達成される。
  この縮小は最終報告でユーザーへ明示する。
  併せて **collection 時に memo consumer が resolver へ到達しないこと**を meta-test で固定する
  (縮小が成立する前提そのものを機械化する)。
- **(訂正 3) T-813 と 110。** T-813 は「並行 writer が存在する」証拠としてだけ引用する。
  payer は 110 ではなく **32 関数 / 35 node**。
- **(訂正 4) 1.1 倍の判定方法。** 静的上界は 192.80 秒 (1.114 倍) で閾値を超えるため、
  **合格は段 6 の paired 実測 (同一経路・同一並列度・CPU 飽和度併記) でしか主張しない。**
  非飽和で 1.1 倍を超えたら land しない。

## 3. 変異事前登録 (DW-M01)

runner 範囲は各変異の期待 node をちょうど含む最小集合とし、期待 node 集合と対で登録する。
本走は `tools/mutation_harness.py` を dispatch recipe (`--force-dispatch`) で回す (DW-M07)。

| # | 変異 (wave 前の実在形へ戻す / 新設分を壊す) | runner 範囲 | 期待して落ちる node |
|---|---|---|---|
| M1 | `real_repo_receipt` の cache path 不明枝を wave 前の `if path is None: return _resolve_now()` へ戻す | 新設 memo 単体 test | fail-closed 単体 test の L1 case |
| M2 | lock open 失敗を wave 前の `_resolve_now()` fallback へ戻す | 同上 | L2 case |
| M3 | cache 不在を wave 前の resolve + store へ戻す | 同上 | L3 case |
| M4 | `_cache_load` が壊れ cache で `None` を返す wave 前の形へ戻す | 同上 + `test_receipt_memo_session_cache_round_trip_preserves_the_resolution` | L4 case と round-trip test の 2 node (**過剰決定を承知で登録**。既存 test が先に落ちるため単独理由性は無い — DW-M03 に従い冗長 gate と明記) |
| M5 | `_cache_store` の例外握り潰しを戻す | 新設 memo 単体 test | L5 case |
| M6 | 公開 `real_repo_receipt()` に「`get()` の例外を捕まえて `_PRODUCTION_RESOLVE` へ倒す」fallback を足す (**A2 の攻撃そのもの**) | 公開端 end-to-end 負例 | 公開端 negative test |
| M7 | conftest の xdist prewarm 呼出しを削除する | wiring meta-test + 代表 consumer 2 node | wiring meta-test と代表 consumer 2 node (prewarm 不在で fail-closed) |
| M8 | conftest の serial prewarm 呼出しを削除する | 同上 | 同上 |
| M9 | worker 除外 (`workerinput` guard) を外す (**A1/B1 の must-fix を壊す**) | worker 除外 meta-test | worker 除外 meta-test の resolver count 0 assertion |
| M10 | consumer 集合から代表 1 件を落とす / opt-out 2 本の一方を混ぜる | consumer inventory meta-test | inventory meta-test |
| M11 | conftest 側の import を非修飾へ戻し module identity を分裂させる (**A3/B2**) | identity meta-test + 代表 consumer 2 node | identity meta-test |

正例 (受理集合を縮小する wave の過剰拒否検出、DW-M01): 変異なしの baseline で
**consumer 35 node と opt-out 3 node が全緑**であることを同じ runner 範囲で確認する。

## 4. scope 確定

**実装する:** `orchestrator/tests/real_repo_receipt_memo.py`、`orchestrator/tests/conftest.py`、
`orchestrator/tests/test_s8b_binding_driftguards.py` (期待値変更 2 本 + 新設負例)、
`orchestrator/tests/test_real_repo_serialization.py` (meta-test 群)、
`orchestrator/tests/test_s8b_oracle_driver.py` (コメント訂正のみ)。

**実装しない (ユーザーへ返す):** pickle の closed-schema codec 化 (A6)、
runner の infrastructure failure 分類 (B7)、CLI 子プロセスの 2 回目解決 (B3 = R-e)、
`--forked` / remote xdist 対応 (B6 / A7 後半)。

**成果物影響 (DW-G05):** must-fix 1 を落とすと xdist 全走が構造的に成立せず
certified 選択・レポート・台帳が 1 つも生成されない。must-fix 2 を落とすと、
gate を撤去しても全走が緑を主張でき、prewarm miss 時だけ live working tree を再走査して
certified 材料の値が走行順で変わる。must-fix 3 を落とすと 35 node が一斉に赤になる。
must-fix 4 を落とすと failure digest の subprocess 経路が壊れ、赤の構造化レポートを失う。
