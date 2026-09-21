## 実施

`author-t2825-probe-fix1` で所有範囲の 3 ファイルを修正しました。所有外の変更、`git add` / `git commit` はありません。

## 所見ごとの対応

1. **slot 制御:** 共通の `check_request()` を flock 内と series preflight から呼び、無効対後は同順序の取り直しだけを許可。
2. **L 文言:** 非該当時を「事前登録した L 伸長の判定条件を満たさない」に変更。ΔL・nodeid 交代・差縮小の注記は維持。
3. **台帳出所:** `git show <測定SHA>:<台帳path>` の bytes を使用。測定／worktree hash を別欄にし、不一致は警告のみ。
4. **suffix 解決:** 割付器と同じ base→`nodeid@group`→1.0 の順序で負荷と未登録件数を算出。
5. **条件別集計:** 採用した有効対だけから、A/B・shard 別の W/O/L/F/pre/post 中央値と対象走番号を JSON／Markdown に出力。

## 検査結果

| 検査 | rc |
|---|---:|
| `bash -n`：3 script | 0 |
| `python3 -m py_compile`：cache は一時 dir | 0 |
| `--selftest`：今回の 5 件の回帰を追加 | 0 |
| 実物 session の A 単走 dry 集計 | 0 |
| `git diff --check` | 0 |

実物では **W₀=382.090、L=229.056（gw5）、T-2724=8/8** を再現しました。

| gw33 item（略記） | rank | time 秒 | 推定開始 offset 秒 |
|---|---:|---:|---:|
| fake Codex experiment | 33 | 55.434 | 0 |
| loader filters | 77 | 0.001 | 55.434 |
| shared_base separates | 455 | 0.004 | 55.435 |
| active_v2 delegation | 456 | 189.183 | 55.439 |
| failed_launch preserves | 457 | 47.857 | 244.622 |

`…explicit_binding@real-repo` は **0.19 秒**で解決。shard-0 予測負荷は **7750.334→7749.524 秒（−0.81 秒）**、未登録件数は **368→367** でした。

両 script の誤 slot 投入も **rc=92、走番号未消費**を確認しました。

## 受理・拒否の含意

事前登録どおりの有効走・有効対と、無効対の同順序での取り直しを引き続き受理します。無効対を飛び越す次 slot、健全な片側の再利用、固定終了・上限後の投入を拒否します。

**通る正例:** slot 1 の A/B が skipped 不一致なら、次の `03 A 1` は要求照合を通過します。

## 未実走

warm、計算ノードへの投入、新規受入、A/B 測定系列は未実走です。実物 dry 集計は既存 session に合成 metadata を付けた検査です。

## 総括

指定の 5 件を修正し、回帰検査はすべて通過しました。
事前登録の閾値・分岐・符号は変更していません。
実物の主要指標と suffix による 0.81 秒差を確認しました。
修正済み 3 ファイルを親のレビュー・測定へ渡せる状態です。