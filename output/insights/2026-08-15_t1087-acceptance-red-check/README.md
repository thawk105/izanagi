# [T-1087] 非帰属 checker の判定不能 — 実測台帳

wave: `dev-wave-t1087-acceptance-red-check` (2026-08-15)

## 1. 依頼が名指しした 2 機序は main で不再現 (親の直接実行)

| 走 | log | 赤 | 時刻 (JST) | 所要 | rc | status |
|---|---|---|---|---|---|---|
| 1 | 合成 (実在 node 1 件) | 1 | 07:34:44→07:36:02 | 78 秒 | 1 | attributable-red |
| 2 | 2026-08-13 の実受入 log 逐語複製 | 2 | 07:40:40→07:43:15 | 155 秒 | 1 | attributable-red |

- receipt の `source=dispatch-receipt` と PBS request_id (走 1 が 1 件、走 2 が 2 件) が
  実 dispatch を証明する。
- **削除の証拠は receipt の削除 path field ではない** (削除より前に組み立てられる自己申告)。
  実際の証拠は清浄性検査を計 6 回通過して判定へ到達したこと。
- collect 段の timeout は両経路とも 5100 秒で対称。

## 2. 本番受入 2 走 (本 wave 自身)

| 走 | 時刻 (JST) | 全走 | 赤 | checker | 待ち手 |
|---|---|---|---|---|---|
| 1 | 08:17–08:21 | 1 failed / 11033 passed / 65 skipped / 141.52 秒 | signal handler フレーク | attributable-red | rc=70 |
| 2 | 08:24–08:33 | 1 failed / 11033 passed / 65 skipped / 126.98 秒 | dev_waves 統合テスト | **rc=2 not clean** | rc=70 |

## 3. 手動再現による真因特定 (固定 commit の使い捨て worktree)

判定器と同じ 2 コマンドを手で流し、各段で同じ `git status` を採った。

| 段 | 修正前 (main) | 修正後 (`2a357ff1` の親 commit) |
|---|---|---|
| worktree 作成直後 | (空) | (空) |
| collection 後 | `!! output/pegasus-dispatch/` | — |
| 単独再走後 | `!! output/pegasus-dispatch/` + **`!! tools/dev_waves/__pycache__/`** | `!! output/pegasus-dispatch/` のみ |
| 生成 `.pyc` | **11 本** | **0 本** |

11 本の内訳: `__init__` `checker` `daemon` `effort_levels` `git_state` `ledger` `protocol`
`receipt` `redaction` `schema` `worker`。`cli` `launch_authority` `time_values` は含まれない。

collection 段で bytecode が 1 本も出ないことが、抑止変数は計算ノードの pytest まで届いている
ことの証拠である。したがって書き手はそこから起動された子である。

## 4. 変異

`mutation-spec.json` / `mutation-ledger.json` を同梱する。

- anchor は fix 後の commit で再検証 (置換対象は各 1 箇所)。
- runner 範囲は `test_dev_waves_worker.py` と `test_dev_waves_integration.py`。
- 結果: **2/2 KILLED・SURVIVED 0・MISMATCH 0**。どちらも新設回帰テストちょうど 1 本だけを
  落とし、baseline は失敗 node 0 件。

## 5. 非帰属経路の発火実績 (全件走査)

job 領域の checker receipt を打ち切らずに列挙すると 10 件。赤を持つ 9 件はすべて
`attributable-red` で、node は 11 件すべて `rerun_rc=0`。本 wave の受入 1 走目を加えて
**12 node すべてが帰属判定**であり、`non-attributable-only` は 1 件も無い。

## 6. 主張の射程 (敵対レビューによる縮小)

- 「受領証残渣は再現しない」は**正常な受領証告知経路**に限る。告知なし・非一意・rc 不一致の
  各経路は削除へ入る前に例外となり、root が空でなければ削除もしない。いずれも倒れる向きは
  判定不能なので受理集合は緩まないが、「残渣経路は存在しない」とは言わない。
- 「bytecode の書き手は 1 箇所」は**偽**。checkout 内の CLI を `PATH` だけの環境で起動する
  既存テストが別に実在する。`orchestrator/` と `tools/` の `env=` 指定起動は 174 箇所ある。
  本 wave が主張できるのは「今回の本番 rc=2 を起こした経路を特定して塞ぎ、修正後の不再現を
  実測した」までである。
- 「フレークは必ず帰属に倒れる」も全称としては**偽**。持続性フレーク等は再走でも赤になりうる。
  実測が言えるのは 12/12 が帰属だったことまでである。
