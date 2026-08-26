# 段 1 brief — 登録済み flake hold 3 件を解消して受入集合へ戻す

- wave: `dev-wave-flaky-holds-20260826` (branch `worktree-dev-wave-flaky-holds-20260826`)
- 基準: local main `e29084e0` を ff 取り込み済み。worktree clean
- 引数: 「フレークテストがあればそれを直してください」

## scope

`orchestrator/tests/flaky_test_holds.py` に登録済みの 3 件の hold を、テストが守る性質を
1 つも減らさずに解消し、台帳から外して受入集合へ戻す。

### S1. hold#1 / hold#3 は既に修理済みで、登録だけが残っている (撤去)

commit で確定した時系列。

| 時刻 (JST) | commit | 内容 |
|---|---|---|
| 08-25 21:22 | `26d7f74b` | hold#1 登録 (`test_control_lock_allows_peer_after_pending_hold_is_durably_released`、F480) |
| 08-26 03:11 | `35f0a5c6` | hold#2 登録 (`test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary`、F136) |
| 08-26 05:26 | `9cd011fe` | hold#3 登録 (`test_receipt_memo_real_xdist_order_has_no_worker_payer`、F480) |
| 08-26 09:17 | `639f2f28` | **hold#1 と hold#3 のテストを修理**して main へ入った (T-1719 の fix 子) |

`639f2f28` は hold#1 の `join(10)` を `join(60)` へ、hold#3 の合成 plugin を
`hookimpl(hookwrapper=True, tryfirst=True)` + `yield` 前記録へ変えた。どちらも登録行は消していない。

成果物影響 (DW-G05): 撤去しなければ、dispatch の control lock 解放と receipt memo の
payer 不在という 2 つの不変条件が受入全走の受理集合から**恒久的に外れたまま**になり、
この 2 経路の回帰が検出されずに land する。

### S2. hold#2 の真因は除外集合の作り方で、同じ真因が T-1856 の決定的な赤も出している (修理)

`orchestrator/tests/output_snapshot_ignores.py:9` の `git_ignored_output_prefixes()` は
`git ls-files -o -i --exclude-standard --directory -- output/` を使う。この command は
**実在する** ignored path しか返さないため、除外集合が `.gitignore` の規則ではなく
実行時の状態の関数になっている。ここから 2 症状が出る。

- **(D-a) 決定的な赤 = T-1856。** fresh worktree には `output/runs` が無い (実測: 不在)。
  よって `runs` が除外集合に入らず、`assert "runs" in ignored_prefixes` を持つ 3 つの検査が必ず落ちる。
  実測 (本 worktree、`tools/run_tests.py` の焦点走、rc=1):
  `assert 'runs' in ('pegasus-dispatch',)` が
  `test_s8b_oracle_driver.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes`、
  `test_real_repo_serialization.py::test_t080_output_snapshot_excludes_git_ignored_real_output_changes`、
  `test_s8b_floor_campaign.py::test_real_output_snapshot_excludes_git_ignored_real_output_changes`
  の 3 件で同時に発火した。
- **(D-b) flake = hold#2。** snapshot helper は entry 列の先頭に root を無条件で入れ
  (`test_s8b_oracle_driver.py:560-568`)、root の `st_mtime_ns` / `st_ctime_ns` を記録する。
  受入全走の別 shard が `output/runs` を**新規作成**すると `output/` 自身の mtime が動く。
  ignored な子の生成という、helper が設計として除外したはずの事象が root entry から漏れる。

同型の helper が 3 file に複製されている
(`test_s8b_oracle_driver.py:558`、`test_real_repo_serialization.py:541`、
`test_s8b_floor_campaign.py:1484`)。DW-G03 の「独立 2 例」は満たす。

成果物影響 (DW-G05): 直さなければ (i) hold#2 の node が受入集合から外れたままになり、
T-080 e2e builder が実 repo の `output/` を temp root にしない、という fail-closed 境界の
回帰が検出されない。(ii) fresh worktree の焦点走が 3 件の赤を常に出すため、
「焦点走が緑」を land 前の関門に使っている全 wave がその関門を通せない。

### S3. 修理済みの hold が黙って生き残ることを、今は何も検出しない (機構、provisional)

S1 が実例。hold は opt-in の抜け道が無く (`conftest.py:1721-1737` が無条件に
`pytest.mark.skip` を付ける)、受入だけでなく焦点走でも常に skip される。したがって
登録された node は**どこでも走らない**。修理が別 wave で入ると、登録行は誰にも気づかれずに残る。
独立 2 例 (hold#1 と hold#3 は別 wave が登録し、同一 commit が修理した) は満たす。

成果物影響 (DW-G05): 入れなければ、今後 hold を 1 行足すたびに受理集合が単調に縮み、
縮んだことを検出する経路が無い。

## 確定済みユーザー裁定

- 「並列数を上げたら落ちるフレークは、そのフレークが間違っているのでは」(worklog 991 に記録)。
  hold 登録による回避ではなく、性質を保ったままテストを直す。本 wave もこれに従う。

## 不変条件 (1 つも減らさない)

- hold#1: 結果 (`results == {"first": 0, "second": 0}`)、qsub 回数 2、`_orphan_hold_present` 不在
- hold#3: 各 hook 1 回ずつ、`prewarm-controller` 1 回、`prewarm-worker` 不在、
  `worker-hook` < `controller-hook` の順序、合成負例が赤になること
- hold#2 / T-1856: 「git-visible な変化を検出する」positive control と
  「git-ignored な変化を除外する」negative control の両方。除外側を広げるなら検出側の
  positive control を必ず対で足す

## 親の provisional 裁定 (攻撃対象)

- **(P1)** S3 の機構を本 wave の scope に入れる。形は「hold の行に、登録時点の対象 test 関数の
  source digest を持たせ、現在の source と食い違えば contract test が赤になる」。
  攻撃点: 無関係な編集でも再正当化を強制するコストが、検出する価値に見合うか。
  registry の既存 field 群と二重にならないか。
- **(P2)** (D-b) の修理方向は「ignored な子を持ちうる directory では mtime / ctime を記録しない」。
  攻撃点: helper の docstring が謳う「git-visible path の一時作成後削除も timestamp で捉える」
  検出力が落ちる。この検出力を独立に確かめる positive control は現状**存在しない**
  (既存の positive control は永続的な作成を見ており、mtime 単独の寄与を分離していない)。
  恒真ゲートを黙って残すのか、検出力を別機構で回復するのか、docstring を実態へ寄せるのかを裁定する。
- **(P3)** (D-a) の修理方向は「除外集合を実在ではなく規則から導く」。
  攻撃点: `git check-ignore` は存在しない path にも答えるが、`--directory` 相当の
  prefix 畳み込みが無い。候補名をどこから得るかで、また別の状態依存を持ち込みうる。
- **(P4)** 3 file に複製された helper を共通化するか、各 file で直すか。
  攻撃点: 共通化は編集面を広げ、並行 wave との競合面を増やす。

## 成果物の形

- `orchestrator/tests/flaky_test_holds.py` の `_FLAKY_TEST_HOLD_ROWS` が空になる
- `orchestrator/tests/test_flaky_test_holds_contract.py` が空 registry と S3 の機構に追随する
- `orchestrator/tests/output_snapshot_ignores.py` と 3 file の snapshot helper が (D-a)(D-b) を解消する
- 撤去した 3 node と、T-1856 の 3 件が焦点走・受入全走の両方で緑

## 並列分割方針

- 段 2 プランは 1 本 (変更面が 1 つの真因へ収束しているため)
- 段 3 敵対相談は 2 本。レンズを (a)「性質を減らしていないか / 恒真ゲートを作っていないか」、
  (b)「除外集合の作り替えが別の状態依存を持ち込まないか」で分ける
- 段 5 実装は 2 子。所有を「registry 撤去 + S3 機構」と「snapshot 族の修理」で分ける

## scope 外

- `test_dev_wave_cleanup.py` が受入全走で毎回 1 件落ちる件 (占有検査 rc=22、落ちる node が走ごとに動く)。
  並行 job が原因側を担当中。本 wave の受入で踏んだら DW-O18 に従い非帰属として扱う
- hold#1 の `reintroduction_task_id` `{{T:flaky-thread-join-upper-bound}}` に T 番号が
  割り当てられていない (`docs/spool/FOLDED.md` に allocation が無い)。撤去すれば消えるので追わない
