## 実施

所有の [t2825-probe/](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2825-probe/t2825-probe) 5 file を実装しました。`git status` はその 5 file の新規追加のみ。`git add` / `git commit` は実行していません。

## 下敷きからの差分

| file | 変更 |
|---|---|
| `run-measure.sh` | leader の argv 先頭一致、load1 ≤60、門番設定の再読込、台帳だけの tracked 差分検査。login collection・top JUnit・実物の nested request/receipt を sha256 付きで複製 |
| `run-series.sh` | 指定の AB / BA / AB 列、warm・分類・系列無効・固定終了を検査 |
| `run-warm.sh` | 固定 A/B tree に対応。shard env を除去し、collect-only・HEAD/clean・pyc を記録 |
| `gate.conf` | 指定の 1 / 60 / 120、周期 100+乱数41、jitter 乱数46 |
| `t2825_ab_analyze.py` | W_0 判定、W_max 補助、ΔL、collection、移動量、台帳負荷、item 列、赤本文、JSON/Markdown、selftest |

warm の `--force-dispatch --collect-only -q -p no:cacheprovider` は現行 source で受理される経路を確認しました。`IZANAGI_ACCEPTANCE_SHARDS=3` が残ると不適格になるため除去しています。

## 検査結果

| command | rc | 結果 |
|---|---:|---|
| `bash -n t2825-probe/run-measure.sh t2825-probe/run-series.sh t2825-probe/run-warm.sh` | 0 | 構文正常 |
| `python3 -m py_compile t2825-probe/t2825_ab_analyze.py` | 0 | cache は一時 dir に生成・削除 |
| `python3 t2825-probe/t2825_ab_analyze.py --selftest` | 0 | 指定 (a)〜(h)、skipped・系列順序・warm の検査に合格 |
| `python3 -B t2825-probe/t2825_ab_analyze.py --job <一時dir> --collection <固定input/login-collection.log>` | 0 | 実物 dry 集計成功 |

## 実物での dry 集計

受入 session `9d955ce2…` を、投入 metadata を合成した A の 1 走として集計しました。

- **W_j = 382.090 / 257.404 / 166.567 秒**。W_max の argmax は shard-0。
- 最大占有 worker は **gw33、O=292.479693679 秒**。
- **L=229.056 秒、gw5**。nodeid は `test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]`。
- collection は **26,808 件一致**。旧 L 候補は全 4 parametrize を出力。
- T-2724 は **8/8 件で worker・rank・time が固定入力と一致**。delegation は gw33 / rank456。
- 1 走なので判定は「判定不能 (反復不足)」。一時成果物は削除済みです。

gw33 の全 item 列も確認しました。

| item（略記） | rank | time 秒 | 推定開始 offset 秒 |
|---|---:|---:|---:|
| fake Codex experiment | 33 | 55.434 | 0 |
| loader filters | 77 | 0.001 | 55.434 |
| shared_base separates | 455 | 0.004 | 55.435 |
| active_v2 delegation | 456 | 189.183 | 55.439 |
| failed_launch preserves | 457 | 47.857 | 244.622 |

## 未実走

計算ノード投入、warm、受入、A/B 系列は未実走です。

## 既知の限界

- ΔW は A−B、ΔO・ΔL・Δ(O−L) は B−A と実装。L の伸長規則は shard-0 に適用しています。
- 開始時刻は累積推定で、item 間の空白は未観測です。
- JUnit の逆対応が未解決なら、login collection の照合結果を残して走を無効にします。実物では全件対応しました。
- 別 tree・node・page cache の差は残ります。入力 1 走の190秒群・40秒群が B の順位を決め、builder/waiter の役割や copy の因果は断定できません。

## 総括

指定 5 file の実装と静的検査・selftest を完了しました。
実物 dry 集計で W_0=382.090 秒と T-2724 の全 8 node を再現しました。
所有外の変更、commit、計算ノードへの投入は行っていません。
親による job dir への複製・レビュー・実測に渡せる状態です。