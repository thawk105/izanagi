## 総括

(P1) に沿い、**系列の campaign dir は維持し、pair job の候補と stock だけを iteration ごとの計測 campaign に置く**。これで job ごとに別の one-shot claim を取得でき、前 job の stock WAL による terminal skip も避けられる。`loop.py`、`campaign_claim.py`、`p3_s4_loop.py`、job body は変更しない。

## 変更計画 (file:line)

以下の行番号は現行ファイルに対する位置を示す。

- [p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:121): `default_cfg` は変更しない。pair 経路だけで `dataclasses.replace(cfg, search_config={**cfg.search_config, 'policy_iteration': iteration})` により計測 cfg を作る。`policy_iteration` は **正整数 `int`**。系列 cfg の `search_config` には入れない。
- 同ファイル [433 行付近](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:433): `drive_iteration` は系列 layout で state の読込・停止判定・counter 更新・履歴追記を続ける。pair 時には計測 cfg/layout を `run_one_iteration` に渡し、critic digest の admitted view も計測 layout から作る。生成した digest テキストの保存先は系列 layout のままにする。
- 同ファイル [387–426 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:387): `run_one_iteration` の `cfg` と `layout` を pair 時には計測用に揃える。gate reject の WAL、`run_campaign`、`_result_history` はすべてその計測 layout を使う。`_result_history` 自体の射影規則は変更しない。
- 同ファイル [365–384 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:365): `run_stock_control` に同じ計測 cfg/layout を渡す。`_stock_result` は同じ job の stock WAL を読む。`src_token == STOCK` の判定は維持する。
- 同ファイル [574–577、643–670 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:574): `main` の pair 分岐で、系列 layout の `loop_state.json` を一度読み、未作成なら初期 state を作る。その `iteration + 1` から計測 cfg/layout を導き、同じ state を `drive_iteration` に渡して二重読込を避ける。候補が例外を投げても、あらかじめ導いた同じ計測 cfg/layout と authorization session で stock を試みる。`stopped-before` なら stock を呼ばない。
- `run_campaign` の呼出箇所は候補の [419 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:419) と stock の [378 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:378) の **2 本のまま**。これは `test_campaign.py:5520,5603` の棚卸し pin に合う。
- bootstrap、r2、record-reject、emit-coder-input の cfg と layout は現行どおり。非 pair の `--run-iteration` も系列 cfg/layout のままとし、既存の単発測定の identity を変えない。`--replay-proposal` は既存の `evaluation_purpose=r2` と、loop state・履歴を更新しない性質を維持する。

## 系列 layout と計測 layout の割付表

| 処理・成果物 | pair 時の layout |
|---|---|
| `loop_state.json`、`policy_history.jsonl`、coder の `self_history` | 系列 |
| `run_one_iteration` の gate reject WAL、候補 `run_campaign`、`_result_history` の WAL | 計測 |
| `run_stock_control` の `run_campaign`、`_stock_result` の WAL | 同じ計測 |
| `L.make_critic_digest` と identity projection の admitted view | 計測 |
| `silo_policy_loop_digest.txt` の保存先 | 系列 |

critic digest は従来どおり**候補評価後、stock 評価前**の snapshot から作る。今後は当該 iteration の計測 campaign だけを材料とするため、過去 iteration の WAL は digest に混ざらない。runbook §1(g) の critic 入力は、系列 dir に保存されたその digest 本文、系列履歴の当該候補の実装、同じ job の stdout にある stock 値という **3 点のまま**。digest に実装や stock 値を新たに含めない。

## iteration 番号と失敗時の挙動

系列 state の既存 counter を唯一の番号源とし、argv は増やさない。`drive_iteration` は現行どおり停止判定の後に counter を 1 増やし、`finally` で系列 state を保存する（[444–468 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/p3_s4_loop_policy.py:444)）。

- 候補が例外で終わると、counter は 1 進み、系列履歴に `eval-exception` が 1 行残る。その後も同じ計測 identity と session で stock を試み、最後に候補例外を再送出する。
- stock が例外で終わると、候補による counter・履歴更新は残る。stock 例外を送出し、stock 用の履歴行は足さない。候補と stock の両方が例外なら、現行どおり候補例外を優先する。
- `stopped-before` では counter は進まず履歴行も増えず、stock と計測 claim は発生しない。
- **同じ iteration の再測定**とは、系列 state を巻き戻すなどして同じ番号の pair identity で再実行する場合である。`_authorize_measurement` は identity から同じ claim path を選び、`acquire_claim` の `O_EXCL` が既存 leaf に対して `ClaimError` を出す（[loop.py:370–409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/loop.py:370)、[campaign_claim.py:383–434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/campaign/campaign_claim.py:383)）。通常の連続実行では counter が進むため、別 identity になる。

## 焦点 test 計画

[test_p3_s4_loop_policy.py:599 付近](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop_policy.py:599) に、同じ `out_root` を使う **別 subprocess 2 回**の結合検査を追加する。親 test が `tmp_path` に小さな harness script と proposal を書き、各 subprocess がその script を起動して `P.main([... --campaign-env pegasus --run-iteration ... --stock-control])` を呼ぶ。monkeypatch は script 内で毎 process 適用する。

fixture は [test_p3_s4_loop.py:11565 付近](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2871-policy-loop-iter/orchestrator/tests/test_p3_s4_loop.py:11565) の pair 結合検査を手本に、site・attestation 観測と build・bench・trace の実処理だけを軽量化する。`loop._authorize_measurement`、`campaign_claim.acquire_claim`、`reservation.check_reservation` は実関数を通す。共有 output root の claims dir を事前作成し、両 process で有効な予約環境を設定する。候補と stock の WAL を admitted view が読める既存 fixture で生成し、stock の `BUILD_START.src_token == STOCK` を保つ。

2 回目終了後、異なる campaign ID の claim が **2 file**、両 stdout の stock outcome が `certified-stock`、系列 `loop_state.iteration == 2`、系列履歴が iteration 1・2 の **2 行**であることを assert する。両計測 campaign に候補と stock の attempt があることも確認する。負例は fixture 内で系列 state を iteration 0 に戻して同じ番号を再実行し、既存 claim に対する `ClaimError` と新たな計測 attempt がないことを確認する。計測関数を fixture に差し替え、process 起動と小さな WAL 処理だけにして数秒を目標とする。

## 変異の事前登録候補

- pair cfg から `policy_iteration` を削除する → 2 回目の subprocess が `ClaimError`、claim 2 file の assert が赤。
- `policy_iteration` を固定値 `1` にする → 同じく 2 回目の claim assert が赤。
- stock に系列 cfg/layout を渡す → stock が `certified-stock` にならない、または同一 session の identity mismatch で赤。
- `_stock_result` に系列 layout を渡す → stock の source/bench WAL を読めず `certified-stock` assert が赤。
- `drive_iteration` の state・履歴保存先を計測 layout にする → 系列の iteration 2・履歴 2 行の assert が赤。

## runbook 書き換え要点

- §1(0): bootstrap は従来どおり別 identity。加えて各 pair iteration も独立した計測 identity を持つため、前回 stock の terminal skip を受けないと明記する。
- §1(f): 系列 counter から driver が番号を決め、候補と stock は同じ iteration の計測 campaign・同じ authorization session を使うと記す。系列 state・履歴・digest の置き場と、計測 WAL の置き場を区別する。
- §1(g): digest ファイルは系列 dir にあり、本文は当該 iteration の計測 campaign の admitted snapshot から生成されると記す。critic に渡す 3 点とその意味は維持する。
- §3: 「1 loop campaign につき pair job 1 本だけ」の記述を除き、系列 state を継続しながら各 iteration の計測 claim を one-shot で取得する手順に更新する。同じ iteration の claim は再利用できず、claim を退避しないことを明記する。

## brief との食い違い

大筋はコードと一致する。ただし brief の「同じ iteration を 2 度測れば ClaimError」は、**counter が通常どおり進む再実行**には当てはまらない。同じ番号を再使用したときに限って成立する。また、現在の critic digest は stock より前に生成されるため、計測 layout に切り替えても digest 本文に stock の結果は入らない。

## scope 外候補

系列 state の手動巻戻しや同時起動を防ぐ新しい gate・台帳、他 driver への展開、生成器対照の系列制御は本計画に含めない。