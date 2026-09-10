# 8c 事前登録 条件 C12 / C04 の production consumer 配線 (C11 は実測で成立済み)

wave branch: `worktree-dev-wave-s8c-c12-c04-c11`
起点 main: `38f173cb` → wave 中に `54baeb86` を ff 取り込み (t1333 が land したため)
実装 commit: `ce8c2f50`, `80a785f2`, `a1a9f1b9`, `a026cc37`

## 何をしたか

8c 事前登録の 12 条件のうち、UNSATISFIED だった C12 と C04 の production consumer を
`orchestrator/campaign/p3_autonomous_workload_trial.py` の `run_trial` へ配線した。

- **C12 (allocation-enforcement-consumer-absent):** `run_trial` の preflight 末尾、
  lifecycle start より前に予約束縛を消費する。予約が要る isolation policy のときだけ
  `reservation.read_binding` → `reservation.check_reservation` を呼び、PBS job 不一致・
  boot 不一致・予約期限までの残時間不足を launch 前に拒否する。判定は `reservation` へ委譲し
  p3 側で再実装しない。
- **C04 (crash-policy-cell-partial):** crash 捕捉経路が戻る前に
  `mark_experiment_indeterminate` を通り、registry の `forbid_trial_restart` と
  indeterminate terminal 記録を**独立に試行**して、両方の失敗を元例外へ集約したうえで
  元例外を再送出する。`reject_started_trial` を preflight から呼び、重複起動を
  lifecycle start より前に拒否する。
- **C11 (completion-proof-not-machine-checkable):** **変更なし。** 実測で既に成立していた。

判定器 (`s8c_preregistration_evidence.py`)、契約 JSON、凍結 record は 1 byte も触っていない。

## 判定器の実測 (library 経路。CLI は全条件を evaluator-exception へ潰すので一次資料にしない)

| 条件 | wave 前 | wave 後 |
|---|---|---|
| C04 | UNSATISFIED / crash-policy-cell-partial | EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable |
| C11 | EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable | 同左 (変更なし) |
| C12 | UNSATISFIED / allocation-enforcement-consumer-absent | EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable |

**`EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` は機械検査を全通過した
合格終端である。** `SATISFIABLE_CONDITION_IDS` が空集合で、機械検査可能条件が `SATISFIED` を
返すと `evaluate_all` が `ERROR / evaluator-internal-error` へ潰すため、到達可能な最良状態が
この値になる。「未定義だから未実装」ではない。

判定器は working tree でなく **commit** を読む。したがって status の反転は統合 commit を
作ってはじめて観測できる。実装子が書いた反転テストが実装直後に赤いのは、この理由による。

## 変異 matrix

本走: **baseline PASSED・12/12 KILLED・SURVIVED 0・MISMATCH 0** (`mutation/mutation-out.json`)。
runner は `python3 tools/run_tests.py -q -rf --force-dispatch` で
`test_p3_autonomous_workload_trial.py` と `test_trial_registry.py` を対象とする。

probe (`mutation/mutation-out-probe.json`) は期待 node 集合の導出用で、
**1 件 (`s8c.m5-required-s-one`) が SURVIVED した**。`required_s=max_wall_s` を
`required_s=1` へ落としても既存の対照が 1 件も落ちなかった。既存の残時間不足対照が
deadline を現在時刻の約 1 秒後に置くため、要求時間がいくつでも同じく拒否され、
**「予約の残時間が trial の実行時間上限をまかなうこと」という束縛そのものを検査していなかった**。
残り約 1800 秒の有効な予約に `max_wall_s=3600` を要求する対照
(`test_run_trial_reservation_rejects_when_remaining_time_is_less_than_max_wall`) を足して塞ぎ、
本走で KILLED になった。probe の結果は erratum として同梱する。

過剰拒否の正例は `s8c.m3-always-required-positive-control` (予約要否判定を常に真にする)。
57 node が落ちる。受理集合を縮小する wave の過剰拒否検出として登録した。

## 変異が本走前に見つけた実害 3 件

いずれも「謳うだけで発火しない保証」型で、敵対レビューまたは変異が見つけた。

1. **`add_note` の恒真な握り潰し。** `try: cause.add_note(...) except BaseException: pass` は
   実行環境の Python 3.10 では `add_note` が存在しないため**必ず失敗し必ず握り潰され**、
   failure-atomic の集約 note は 1 度も発火していなかった。`__notes__` fallback へ置換した。
2. **予約 gate の site 誤認。** `do_build=False` のとき実行 site を transport opt-in flag から
   推定していたため、実際に Pegasus compute で走る no-build 実行が opt-out なら `OTHER` と
   誤認され、**予約検査が丸ごと迂回された**。逆に OTHER の no-build + opt-in は過剰拒否された。
   実 site を preflight で一度だけ解決して共有する形へ直した
   (`do_build=True` 経路の `_current_site()` 呼び出し回数と順序は不変)。
3. **`restart_forbidden` に読み手が居ない。** 立てるだけで誰も読まないなら恒真である。
   `record_trial_start_once` が同一 process の flag を読んで拒否する consumer を足した。
   durable な start row による拒否は二重の防壁として残した。

## 段 6 fix 子が 2 度「期待値が誤り」と判断して止まった

1 巡目と 2 巡目の fix 子は編集せずに停止した。診断は 3 件とも正しく、親が独立に実測して
real と裁定した (Python の version、fixture の残時間、テストの観測対象)。
ただし 2 巡目は**独立な 3 作業のうち 1 件の停止条件で 3 件とも止めた**。
prompt に「作業は独立である。1 つが止まっても他は進めよ」を明記して 3 巡目で回収した。

## scope 外として裁定パッケージへ返した 5 件

1. 予約 gate の支配性が 8c launcher に限られる (`p3_s4_loop_trigger_gating` の CLI と将来の
   PBS dispatch は `run_trial` を経ずに `loop.run_campaign` へ到達できる)。
2. `_finish_trial` の `Exception -> partial` が C04 の意味的要求を骨抜きにしている
   (reason code `crash-policy-cell-partial` が指す穴はここである)。着地済みの設計テストを
   反転させる変更になるため、ユーザー裁定に返す。
3. campaign launch 直前の予約再検査 (preflight→launch の時間差ぶん余裕が目減りする)。
4. 予約事実の report / lifecycle への永続束縛。
5. 判定器へ `reject_started_trial` の reachability を追加するか
   (契約は 3 consumer を要求するが判定器は 2 つしか見ない。自分の実装を判定する門を
   同じ wave で書き換えないという理由で見送った)。

## 構成

- `verbatim/` — 段 1 brief、段 2 プラン、段 3 レンズ A/B、段 4 裁定、段 5 実装子、
  段 6 レビュー A/B、段 6 fix (1 巡目の停止・3・4・7 巡目)。
- `mutation/` — 本走 spec と ledger、probe spec と ledger (erratum)。
- `parent-measurements.md` — 親が計算ノードで採った実測値。
