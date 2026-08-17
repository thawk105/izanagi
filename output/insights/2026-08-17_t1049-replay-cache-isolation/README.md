# [T-1049] replay cache の test 間汚染 — 起票時の衝突源は 89723b89 で既に消えていた

wave: `dev-wave-t1049-replay-cache-isolation-r2` / 2026-08-17 / branch
`worktree-dev-wave-t1049-replay-cache-isolation-r2` / base `699c9cae`

## この材料が答えたこと

依頼は「process 全体で共有される `_OPERATION_REPLAY_CACHE` の test 間汚染を test 側で隔離する」
であった。段 1 の前提実測 (`DW-S01`) で、**隔離すべき汚染が現 main に存在しない**ことが分かった。

**結論: 実装しない。T-1049 は前提解消済みとして完了へ送る。**

起票 (2026-08-13) 時の失敗機序は、`_origin_public_inputs` を使う 5 本の test が
`terminal_operation_id="public-origin-terminal"` という**同一の定数**を、
`tmp_path` の違いによって**異なる payload** とともに使っていたことである。xdist の同一 worker に
2 本以上が載れば、2 本目が必ず `FormalReceiptError(REPLAY)` を投げた。
この定数は 2026-08-15 の commit `89723b89` (`feat(t244)`) で
`"public-origin-terminal-" + sha256(str(tmp_path))` へ変更され、衝突源そのものが消えている
(`orchestrator/tests/test_p3_autonomous_workload_trial.py:6493-6497`)。

## 実測 1 — 汚染は現 main で再現しない (親の一次資料)

すべて Pegasus login node、`python3 tools/run_tests.py` の bounded local 走、checkout は
`worktree-dev-wave-t1049-replay-cache-isolation-r2` の base `699c9cae`。

| 走 | 対象 | scheduler | 結果 |
|---|---|---|---|
| 1 | `test_reflux_origin_client.py` + `test_reflux_formal_consumer.py` | loadgroup | 72 passed / 3.73 秒 |
| 2 | 上記 + `test_p3_autonomous_workload_trial.py` + `test_reflux_origin_ledger.py` | loadgroup | 285 passed / 119.88 秒 |
| 3 | 到達しうる 6 file 全部 (`-n 0`) | serial | **403 passed / 204.78 秒** |
| 4 | clear fixture を持つ `test_reflux_formal_consumer.py` を外した 5 file (`-n 0`) | serial | **353 passed / 210.40 秒** |

走 3 は「全 test が同一 process に載る」最悪ケースである。走 4 は、
`test_reflux_formal_consumer.py:196-202` の autouse clear が衝突を**隠している**可能性を
狙って潰したものである。どちらも緑。

## 実測 2 — 到達閉包 (敵対レンズが親の過大集合を訂正した)

親は `consume_formal_consumer_receipt` に到達しうる test file を 6 本と見積もったが、
段 2 plan と段 3 レンズ A が独立に、**実行到達するのは 4 本**だと訂正した。

- `orchestrator/tests/test_reflux_formal_consumer.py:698-767`
- `orchestrator/tests/test_reflux_origin_client.py:352-528`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py:6561-6737`
- `orchestrator/tests/test_reflux_originless_compatibility.py:581-594`

`test_reflux_origin_ledger.py` は signature 検査と subprocess 内の `read_origin` だけ、
`test_trial_registry.py` は projection の直列化だけで、cache に到達しない。
親の 6 本は安全側の過大集合であり、実測 (走 3・走 4) はその上位集合で行ったので結論は変わらない。

live cache に同時に残り得る ID は `"typed-terminal"`、`"terminal-replay"`、
および test ごとの `"public-origin-terminal-" + sha256(str(tmp_path))` だけで、互いに異なる。
`"fixture-formal-terminal-operation"` の再利用は既存の file-local fixture が隔離している。

`_ISSUED_RECEIPTS` は `operation_id` を鍵にせず、receipt ごとの新規 `object()` を鍵にする
(`orchestrator/campaign/reflux_formal_consumer.py:219,237`)。dict が鍵 object を強参照するため
identity の再利用も起きない。test 間残留は不要な object 保持だけで、隔離の理由にならない。

## 訂正 — 親の推論のうち誤っていた 1 点

親は「`pytest-randomly` が未導入なので test 順序はファイル順で決定的」と書いたが、
これは **false** である。`tools/run_tests.py` は並列時に `--dist loadgroup` を付け、
xdist は scope を test 数の降順へ並べ、次の work unit を受け取る worker は完了時刻で決まる。
したがって worker への同居は非決定的である。

結論 (衝突なし) が維持されるのは、順序が決定的だからではなく、**現行 writer の
`operation_id` が互いに異なるから**である。根拠を差し替える。

なお受入形は `--ff` / `--lf` / `-p` / `-o` を構造的に拒否する
(`tools/run_tests.py:97-101,519-579`) ため、collection 順そのものはファイル順で固定される。

## なぜ共通 autouse fixture を入れないか

段 1 brief の (P1)「共通 conftest の autouse fixture が最小」と (P2)「before/after clear と
fixture 無効化を殺す回帰 test で必要十分」は、どちらも段 3 で崩れた。

1. **不変条件を破る。** `orchestrator/tests/test_pytest_failure_digest.py:953-964` は
   外側 test の途中で `pytest.main(..., plugins=[C])` を再入する。共通 autouse fixture は
   内側 session にも登録されるため、内側 test の setup/teardown で canonical な formal cache を
   clear する。これは「同一 test 内の replay 検出状態を途中で消さない」の直接違反である。
   (現在の当該外側 test は formal consumer を使わないので現 HEAD の赤ではないが、
   共通 clear 案に対する実装上の反例である。)
2. **今回の再発そのものを隠す。** 旧定数へ戻しても、test 境界の clear が REPLAY red を消す。
   隔離ではなく検出力の破壊になる。
3. **族一般化の条件を満たさない** (`DW-G03`)。worklog (519) と (535) は同一事象の 2 回観測であって
   独立 2 例ではない。広い「process-local test state 汚染」族の独立例としては F306 があるが、
   formal replay cache 族としては 1 例のみである。
4. **費用が全 suite に乗る。** `orchestrator/tests` の `test_*.py` は 212 file、
   `def test_` の定義は 8,421 件 (親の実測。段 3 レンズ B は 8,430 件と述べたが再現しなかった)。
   parametrize があるので実 node 数はさらに多い。

## なぜ pin assertion も入れないか

「`terminal_operation_id` が `tmp_path` 由来であること」を pin する assertion 1 本は
suite コストを増やさないが、**事前登録変異を作れない** (`DW-M01` の単一理由性)。
旧定数への巻戻しは、既存の `:6561` と `:6720` が同一 process に載れば既に殺す。
xdist で別 worker に分かれれば survive するため、変異 verdict が worker 分配に依存し、
新 assertion 固有の kill として記録できない。DW-G05 の成果物影響も
「将来の CI red 復活」までしか書けないため nit とした。

## 成果物影響 (DW-G05、段 3 レンズ B の訂正を採用)

現行 scope で変わるのは主に pytest の受入判定であり、certified 選択・実運用の report・台帳は不変。
実際に衝突した test では一時 run root の report 欠落と lifecycle の indeterminate 化が起き得る
(`orchestrator/campaign/p3_autonomous_workload_trial.py:2286-2296,3210-3221,3272-3287`)。

## 既存追跡へ収容した所見

段 3 レンズ A は「`--confcutdir` を suite root 下へ向けると共通 conftest を迂回でき、
受入形判定もそれを許す (`tools/run_tests.py:85-93`)」を挙げた。親が実測確認したところ、
`tools/hold_inventory.py:124-133` が `pytest-confcutdir-below-suite` を
`known-unresolved-bypass` として登録し、`orchestrator/tests/test_hold_inventory.py:588-617` が
その登録を exact に機械検査していた。ただし同 entry の `tracking` field が指す `T-930` は
2026-08-13 (worklog 515) で完了済みであり、現在の所有者は台帳の task ではなく
inventory の登録 entry 自身である。本 wave は共通 conftest へ依存を足さないため新規起票はしない。

## 逐語

- `verbatim/brief.md` — 段 1 brief (現 main で改訂したもの)
- `verbatim/s2-plan.md` — 段 2 Codex plan
- `verbatim/s3-lensA.md` — 段 3 敵対レンズ A (正しさ境界と到達可能性)
- `verbatim/s3-lensB.md` — 段 3 敵対レンズ B (整合と実効性)
- `verbatim/s4-adjudication.md` — 段 4 裁定

段 2・3 の Codex 子は read-only sandbox で走り、pytest を 1 度も実走していない。
子の結論はすべて静的検査であり、緑の報告ではない。テストの実測は親だけが行った。
