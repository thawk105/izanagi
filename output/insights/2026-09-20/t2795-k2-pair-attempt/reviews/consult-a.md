## 攻撃 1

**P-A を覆す既存経路は無い。** ただし断定範囲は、今回読んだ claim leaf 全文、`_authorize_measurement`、stock 評価関数・CLI 分岐、job body、output root 解決経路に限る。

- **env・flag・record 一致による再取得:** 同 identity の既存 claim は無条件に `ClaimError`。job_id・host・boot_id が一致しても受理する分岐はない。record の self 一致検査は再取得許可ではない（`orchestrator/campaign/campaign_claim.py:400`、`:421`、`:428`）。
- **claim root 切替:** `IZANAGI_EXPLORATION_OUTPUT_ROOT` は存在する。ただし claim と campaign layout が同じ base root に従うため、切替は WAL の所在も変える。同 ID を維持できても、D2183 の「同 WAL」を満たす救済ではない。job body に起動間の切替もない（`orchestrator/campaign/layout.py:389`、`:594`、`orchestrator/campaign/loop.py:215`、`tools/pegasus/p3_s4_loop_pegasus.sh:596`）。
- **reservation 不要契約:** `linux-baremetal` には存在するが、Pegasus 計算ノードは `pegasus` 契約へ写像され、`single_process=True`。別契約への変更は今回の環境契約・identity を維持する経路ではない（`orchestrator/campaign/env_contract.py:260`、`:300`、`orchestrator/campaign/p3_s4_loop.py:120`、`:150`、`orchestrator/campaign/reservation.py:278`）。

D2183 は同 identity **かつ同 WAL** を要求するため、別 root で同名 campaign を作るだけでは充足しない（`docs/decisions.md:69134`）。

## 攻撃 2

**claim 機構の読みは正しい。ただし到達地点の診断に明確な誤りがある。**

`_scan_protocol_conflicts` は `excluding_path` と一致する path を明示的に除外する。`acquire_claim` は自分の identity path を除外指定し、その後 `O_EXCL` で作成する。同 path が存在した場合は record を読んで例外を出すだけで、生存判定しない（`orchestrator/campaign/campaign_claim.py:355`、`:409`、`:421`、`:428`）。

一方、診断メモ22行の「stock は condition gate も……走っていない」は誤り。stock は `_require_condition_gate` を実行してから `run_campaign` に入る。`BACKOFF_FIXED=-1` は早期 return 対象ではなく、supply・meaning・admission を検査し、不受理なら例外になる。今回の traceback が `run_campaign` 内へ到達したことから、**stock の condition gate は正常復帰した**と読める。未到達なのは campaign pipeline の build・verify・bench である（`orchestrator/campaign/p3_s4_loop.py:1953`、`:1969`、`:1986`、`:423`、`:456`、`:513`、証拠 `job.stderr:29`）。

また、D464 本文の「DEAD は通す」「両者が死ねば次の投入が通る」は、同 identity path の例外を明記していない。**実装の説明としては親が正しいが、D464 の文面まで同 path 永久拒否を明確に裁定していると扱うのは強すぎる。** D553 は claim 取得を追加する裁定で、この文言差を解消してはいない（`docs/decisions.md:19326`、`:19350`、`:22568`）。

## 攻撃 3

**「実 `run_campaign` ＋ reservation 必須契約を通していない」は支持。ただし「TL は stub だけ」は誤り。**

stock テストには、実 `loop.run_campaign` を戻すものがある。

- verify option の伝達検査：`orchestrator/tests/test_p3_s4_loop.py:10107`
- stock の COMMIT・digest 更新・再実行時 skip：同 `:10171`、`:10179`、`:10187`
- 非 STOCK evidence の admission 拒否：同 `:10205`、`:10215`

これらの共通 fixture は site を `OTHER` に固定する。契約は `linux-baremetal`、`single_process=False` なので、実 `_authorize_measurement` に入っても reservation・claim 分岐を通らない（同 `:9676`、`:10209`、`orchestrator/campaign/env_contract.py:300`、`orchestrator/campaign/loop.py:205`）。

job contract テストは実 shell を走らせるが、代用 `python3.10` が `-m` 呼出しを記録し、指定された rc で終了する。実 driver・claim は実行しない（`orchestrator/tests/test_p3_s4_loop_job_contract.py:1248`、`:1256`、`:1265`、`:1889`）。

したがって欠落は、**同じ durable root・Pegasus 契約で候補→stock を連続起動する結合検査**である。

## 攻撃 4

**stock の claim 失敗自体は、先に完了した候補の certified 記録を無効にしない。**

stdout は候補の serializable、0 anomalies、811,956 tps、`1 committed`、`outcome=certified` を記録した後に stock 起動を記録している。job body は別プロセスの rc を集約するだけで、候補を巻き戻す処理を持たない（証拠 `job.stdout:223`〜`:231`、`tools/pegasus/p3_s4_loop_pegasus.sh:599`、`:616`）。

stock の例外は `run_campaign` の WAL 修復・評価より前に発生しているため、この例外による候補 COMMIT の取消しもない（`orchestrator/campaign/loop.py:517`、`:542`、`:554`）。

ただし本検査では候補 WAL・receipt 自体を再監査していない。結論は「この失敗を理由に無効化しない」であり、**pair 成立は認定できない**。両 attempt の WAL outcome が必要という brief・D2183 の条件は未充足である（親 job root の `brief.md:22`、`docs/decisions.md:69140`）。

## 攻撃 5

**stdout／stderr から、claim 以外の独立した失敗原因は確認できない。**

stderr の CMake 警告は未使用 `CMAKE_C_COMPILER`。stdout の feature probe の `failed`／`not found` の後にも configure・build が完了し、候補は certified になっているため、それらを今回の終了原因とは認定できない（証拠 `job.stderr:1`〜`:10`、`job.stdout:125`、`:193`、`:204`、`:226`）。

stock の唯一の traceback は `FileExistsError → ClaimError`。scheduler 記録には残時間10,726秒があり、walltime 枯渇を示さない（証拠 `job.stderr:13`〜`:37`、`:51`）。

full／short PIN の admission 問題も今回の発火原因ではない。stock は admission より前の claim で停止しており、D2183 は STOCK evidence 限定 resolver を既に採用している。ただし claim 解消後の STOCK token 成立まで、この走行で証明されたわけではない（`orchestrator/campaign/loop.py:517`、`orchestrator/campaign/p3_s4_loop.py:1992`、`:2001`、`docs/decisions.md:69143`）。

## 成立しなかった攻撃

- 「所有者が終了していれば同 path も通る」：同 path は生存走査から除外され、`O_EXCL` が拒否する（`orchestrator/campaign/campaign_claim.py:356`、`:428`）。
- 「root 切替で同 WAL のまま救済できる」：root は claim と campaign layout の双方に使われる（`orchestrator/campaign/loop.py:215`、`orchestrator/campaign/layout.py:599`）。
- 「job 全体の rc=1 が候補 certified を取り消す」：rc 集約に取消処理はない（`tools/pegasus/p3_s4_loop_pegasus.sh:616`）。
- 「claim 以外の実失敗がログにある」：確認できた終端原因は claim 衝突のみ（証拠 `job.stderr:13`）。

## 総括

P-A は、今回の Pegasus 契約・同 identity・同 WAL・既存 launcher の範囲で支持する（`orchestrator/campaign/loop.py:205`、`campaign_claim.py:428`）。
親の「stock condition gate 未実行」は訂正必須で、gate は claim より前に正常復帰している（`orchestrator/campaign/p3_s4_loop.py:1969`）。
テスト欠落は実 loop 全体ではなく、reservation 必須契約での連続起動である（`orchestrator/tests/test_p3_s4_loop.py:9676`、`:10107`）。
候補の完了記録は保持し、pair 未成立と分けて扱うのが妥当（証拠 `job.stdout:225`、`docs/decisions.md:69140`）。
証拠ログの所在は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-k2-pair/evidence/attempt-0001/`。書込み・テスト実行は行っていない。