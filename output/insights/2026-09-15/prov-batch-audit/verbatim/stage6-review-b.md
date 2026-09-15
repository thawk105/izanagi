## 所見

静的検査のみ。指定5ファイルを読み、書込み・pytest・性能測定は行っていません。以下の短縮表記は `checker = tools/check_ai_provenance.py`、`tests = orchestrator/tests/test_check_ai_provenance.py` です。

### Q-1 — should-fix：実object欠落・packed格納での失敗検査が残る

**file:line：** `checker:1202`, `checker:1226`, `checker:2143`、`tests:7206`, `tests:7380`

**具体的な入力・状況：** 正常OIDと存在しない完全長OIDの混在、祖先索引作成後のobject消失、pack破損。

- `_git` はGitの非ゼロ終了を `RuntimeError` にし、一括取得はそれを捕捉して全廃fallbackする。途中stdoutがあっても採用しない。
- 通常の履歴監査では先に祖先索引を作るため、最初から欠落しているOIDは `rev-list` 側で失敗し、一括取得まで到達しない可能性がある。
- 一括取得段で失敗した場合は既存 `show` に戻り、そこでの例外は `main:3210` からrc=2になる。
- 現fixtureの `missing` は**出力recordの欠落**、`log-error` は注入例外であり、実object欠落ではない。Gitが実際に返すrc・stderr・部分stdout、およびpacked／loose両形態は未検査。

**影響：** repository障害時の復帰経路を実走で確認した、と段6で報告するには証拠が不足する。

### Q-2 — should-fix：巨大出力のメモリ増分は未計測

**file:line：** `checker:1194`, `checker:1230`, `checker:1242`, `checker:2148`、`author.md:78`

**具体的な入力・状況：** 全史stdout約10.7 MB、巨大messageの増加、複数checkerの同時実行。

`subprocess.run` の出力バッファ・decode後文字列に加え、`output[:-1]` のコピーと `split` 後のフィールド文字列が一時的に重なる。返却後もmessage辞書は監査中保持され、既存の祖先索引と共存する。messageを辞書へ入れる際は文字列参照なので、ここでさらに全文コピーするわけではない。

10.7 MB × 48 = **513.6 MBはstdout量だけの条件付き算術**であり、peak RSSではない。32 workerはスレッドで辞書を共有する。また、48 checker同時起動が実運用で生じる証拠は射影内にない。

`MemoryError`／OOM killは `checker:1226` のfallback対象ではない。

**影響：** メモリ不足時には旧取得へ戻れず、監査失敗や再dispatchで速度利益を失う可能性がある。裁定どおり、まず段6の測定で閉じる事項。

### Q-3 — should-fix：速度成果と小範囲での損益分岐は未確定

**file:line：** `checker:2148`, `checker:2161`, `checker:3160`、`author.md:17`, `author.md:25`, `tests:7304`

**具体的な入力・状況：** worker 32で数十件だけ監査する場合、または一括取得が失敗してfallbackする場合。

一括取得はworker起動前の直列処理になる。旧取得との損益分岐は概ね、**一括取得・decode・検証時間が、旧worker内取得を除いたことで短縮できるwallを上回る点**。件数だけでは決まらず、静的に「N件以下」とは確定できない。fallback時は旧経路の前に一括試行の費用が追加される。

- 少数件経路はCLIの `--range` に存在する。ただし運用頻度は射影外。
- `--message-file` は `checker:3160` から別経路に入り、一括取得の固定費を追加しない。
- `42.52s` は47テストの走行時間。schedulerはserialとあるが、HEAD・実行資源・負荷等が揃わず、監査の速度成果には使えない。
- 呼出し数検査は固定履歴の**4要求・3ユニークOID**で、正常経路log=1、oracle経路show=8を検査している。全史速度の測定ではない。

**影響：** 段6前に速度改善率を成果として採ると、短い範囲監査や障害時の退行を見落とす。

### Q-4 — nit：L-4の残存費用は線形成長だけではない

**file:line／残存処理：**

| 処理 | 箇所 | 増加要因 |
|---|---|---|
| `_ai_agent_values` | `checker:1324`、呼出し `1480`, `1610` | message parse用Git起動。適用経路によって再実行 |
| 隔離parse | `checker:1266`, `1272`, `1279` | tempdir・子directory・Git起動。複数parser呼出しあり |
| 実装path取得 | `checker:2011`, `1636`, `1698` | 親取得とdiff。mergeでは親数・候補path数にも依存 |
| 祖先索引／pickaxe | `checker:1899`, `1903`, `1908`, `1915` | 選択集合の祖先閉包全体。bitset総記憶量は長い履歴で二次的に増え得る |

**具体的な状況：** commit数の増加、変更pathの多いmerge、選択件数は少なくても祖先閉包が大きい範囲監査。

次に調べる暫定順は **trailer subprocess → 隔離parseのfilesystem操作 → path取得 → 祖先索引／pickaxe**。これは実測順位ではなく、mergeの多さや履歴長によって逆転する。特に祖先bitsetは長期のメモリ成長で先行し得る。

本waveの追加実装要求ではなく、段7へ渡す調査順位とする。

## 親が段 6 で測るべき実測項目

1. **同一監査対象HEAD・同一OID列・同一設定で旧新比較。** 旧新checkerのhash、Git/Python版、locale、Git設定、CPU割当、格納形態を記録。**worker 1と32 × 静穏時と負荷時**で旧新を交互に複数回実行し、wall・CPU・実効worker数・結果を残す。
2. **件数別の損益分岐。** 空集合、1、数十件、200件、全史について同じ比較を行う。一括取得＋検証時間、監査全体wall、message取得の呼出し数を分離。`--message-file` は別経路として確認する。
3. **peak測定対象。** 実際に `_audit_history` を実行する**checker Python processのVmHWM／peak RSS**を測る。dispatch待機親だけを測らない。併せてGit子を含む専用cgroupの `memory.peak`・OOM eventsを記録する。単一processの最大RSSを子孫の同時合計と扱わない。
4. **取得前・取得中・監査中のメモリ。** 祖先索引作成後、一括取得／split中、worker実行中を区別し、旧新差を測る。実際の同時checker数も記録。48個という仮定は実運用と分ける。
5. **実Git障害fixture。** loose／packedで正常OID＋欠落OIDを一括helperへ渡し、rc・stderr・部分stdout・fallbackを確認。履歴監査では、祖先索引より前の欠落と、一括取得直前の欠落を分けて検査する。
6. **残存費目。** worker 1／32・静穏／負荷の各条件で、trailer起動回数、隔離parse、path取得、祖先索引／pickaxeを計測。並列処理の費目時間合計を、そのまま全体wallとしない。

性能測定は計算ノードで行う。

## 反証できなかった点

| 境界・攻撃 | 実装の扱いとfixture |
|---|---|
| 空message | `checker:1223` の明示LFで空値にもfieldが成立。`tests:7156` にfixtureあり |
| 1 MiB message | 同じ取得・split経路でサイズ上限なし。`tests:7169` にfixtureあり。メモリ上限の検査ではない |
| 非UTF-8／encoding header | Gitの出力変換後、`checker:1198` のtext decode。失敗は `1226` でfallback。`tests:7170`〜`7172` にfixtureあり |
| CR／CRLF終端 | Git出力内でLFを加えてからtext modeで改行変換。`tests:7161`, `7162` にfixtureあり |
| 本文NUL／SOH | Gitが出力したNULがframingを壊せば `1231` で全廃。SOHは区切り扱いしない。`tests:7165`, `7166` に生bytes fixtureあり |
| root／merge | 親数に依存せずOIDで取得。`tests:7182`〜`7187` がrootと2親mergeを生成 |
| 重複OID | `checker:1215`, `1224` で取得を重複排除し、`2164` では元の要求列を監査。`tests:7304` に検査あり |
| 空集合 | helperは `1218`、監査全体は `2130` で早期return。`tests:7264` に検査あり |
| 単一OID | 通常の3field処理。`tests:7345`, `7355` に単件監査あり |

指定された基本形状にfixture欠落は見当たらない。ただし、境界文字列の多くは取得helperの比較であり、全形状のCLI完走やpacked形態まで証明してはいない。

また、以下は崩せなかった。

- **stdinのpipe deadlock：** `checker:1194` は `subprocess.run(input=..., stdout=PIPE, stderr=PIPE)`。10443 SHA-1 OIDは約428 KBだが、手書きwriteによる相互待ちの構造ではない。
- **Git出力順への依存：** `checker:1242` はOID辞書化し、`2156` で元commitから引く。`2164` は元の `commits` を `pool.map` に渡すため、`--no-walk=unsorted` の出力順保証に依存しない。

## 総括

静的検査で、実装差分のblockerは確認できませんでした。  
基本的な境界入力、stdinの通信方式、元commit列での監査順は確認できました。  
残る受入事項は実object障害、peakメモリ、同一条件での速度と小範囲の損益分岐です。  
現時点の成果は正常経路の取得呼出し数削減までとし、全体速度・成長限界は段6の実測後に確定してください。