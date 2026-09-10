1. **所見 1: `verify` と production loader の受理集合は一致しない**

- 種別: must-fix
- 根拠: 条件別の照合結果は次のとおり。

| 条件 | `verify` | production loader |
|---|---|---|
| candidate path | argv の任意 path を capture (`tools/s8b_budget_approval_preflight.py:184-186`) | `root/BUDGET_APPROVAL_REL` 固定 (`orchestrator/campaign/s8b_holdout_freeze.py:1307-1312`) |
| nofollow capture | candidate と active v1 の双方 (`tools/...:166-185`) | approval candidate のみ (`s8b_holdout_freeze.py:1310-1312`) |
| sha256 | 計算して返すだけ (`tools/...:214`) | caller の pin と比較して不一致を拒否 (`s8b_holdout_freeze.py:1313-1315`) |
| strict JSON | 同じ `_strict_load_object_bytes` | 同じ |
| exact key 集合 | 同じ定数との比較 (`tools/...:187-188`) | 同じ (`s8b_holdout_freeze.py:1317-1318`) |
| canonical bytes | hash の照合前に実施 (`tools/...:189-190`) | hash 照合後に実施 (`s8b_holdout_freeze.py:1313-1320`) |
| scope、approver、timestamp | 判定は同一 (`tools/...:191-208`) | 同一 (`s8b_holdout_freeze.py:1321-1334`) |
| budget | 同じ `_validate_budget` と label。ただし戻り値を破棄 (`tools/...:209-213`) | 戻り値の deepcopy を approval に代入 (`s8b_holdout_freeze.py:1335-1338`) |
| holdout IDs | active v1 を固定 hash、schema、`HOLDOUTS` 集合まで再読 (`tools/...:166-181`) | caller の `holdout_ids` をそのまま使用 (`s8b_holdout_freeze.py:1307-1309,1335-1337`) |

  具体的な `verify` のみ受理例: active v1 に合う正常な canonical candidate の hash を H とする。`verify` は H を返すが、loader に同じ bytes と H 以外の pin を渡すと `:1313-1315` で拒否する。実 production は現在 pin が `None` (`s8b_holdout_freeze.py:52`) なので、`:1297-1304,1692` で loader より前に停止する。任意 path にだけ candidate があり canonical path が無い場合も `verify` のみ成功する。

  具体的な loader のみ受理例: `budget={"total_bench_s":0,"per_holdout_bench_s":{},"oracle_shared":true}` を持つ正常な canonical approval を、`holdout_ids=()` と一致する pin H で loader に渡せば受理される。`verify` は active v1 の `rr20`、`rr80` (`s8b_holdout_freeze.py:100-103`) を使うため `_validate_budget` の `:1281-1283` で拒否する。また active v1 が欠落していても、loader 単体は caller IDs があれば approval を受理できる。

  現行の full production caller は active v1 を `:1698-1707` で検査し、その holdouts を `:1709-1711` で渡すので、holdout 側の逆差は既定経路では表面化しない。canonical 比較順序の差は、不正 raw と不一致 pin が同時にある場合のエラー優先順位も変える。
- 反証条件: 同一 candidate bytes、同一 expected pin、同一 holdout IDs、同一配置条件について両関数を差分実行し、全入力で受理・拒否と失敗段が一致することを示す。現 API のままでは上記 pin、path、caller holdouts の各反例で不一致になる。
- 成果物影響: `verify` が H を受理済みのように表示しても、production の権威 pin は `None` または別値のままで本番受理集合には入らない。逆向きには loader API が caller-scoped で受理する approval を preflight が拒否する。

2. **所見 2: loader との乖離を検出する差分テストが存在しない**

- 種別: must-fix
- 根拠: `test_verify_success...` は `verify` だけを正例化している (`orchestrator/tests/test_s8b_budget_approval_preflight.py:208-242`)。負例群も `verify` だけを呼ぶ (`:244-307`)。loader を呼ぶ唯一の新規テストは、過剰決定された skeleton 拒否だけである (`:147-162`)。repository 内検索でも `_verify_candidate` と `_load_budget_approval` の結果を同じ raw で比較するテストは無かった。

  `:242` の直後に、active v1 を同じ temporary root へ置き、同じ raw を candidate path と `BUDGET_APPROVAL_REL` に配置し、H と同じ holdout IDsを loader に渡す差分テストを置くべきである。extra/missing key、duplicate key、noncanonical bytes、scope、空 approver、timestamp、budget key、負数、negative zero、holdout 欠落を表にし、双方の受理・拒否を比較すれば、書き写した条件の将来 drift を検出できる。さらに pin 不一致、任意 path、caller holdout 差は、現在の意図的な非対称として別テストで明示する必要がある。
- 反証条件: 上記のように両実装を同一 raw へ接続する既存 node を示し、loader の条件を一つ反転するとその node が失敗することを確認する。
- 成果物影響: loader に条件が追加または削除されても preflight テストが成功し続け、同じ approval bytes が片側だけの受理集合へ入る。

3. **所見 3: 現実装の承認者流入は candidate 本文だけだが、N1 の AST blacklist は容易に迂回できる**

- 種別: must-fix
- 根拠: 現コードの argv は `--out` と `--candidate` だけ (`tools/s8b_budget_approval_preflight.py:34-51`)。active v1 から読むのは `holdouts` だけ (`:166-181`)。skeleton は field 名一覧、固定 scope、`draft-not-an-approval` だけで、承認者・時刻・予算値を持たない (`:157-163`)。実値の approver は candidate JSON の `approval.get("approver")` だけから来る (`:184-195`)。環境変数、git config、v1 `confirmed_by`、既定補完の実経路は見当たらない。

  一方、N1 は属性名、import 名、固定文字列だけを blacklist 検査する (`orchestrator/tests/test_s8b_budget_approval_preflight.py:111-136`)。`from os import getenv as read_value`、`getattr(os, "get" + "env")`、`__import__("sub"+"process")`、別 module の helper、`--identity`、`"confirmed"+"_"+"by"` は同じ効果を持ちながら検査を通せる。skeleton 検査も top-level 三 key の不在だけなので、別名または nested な承認者候補値を防がない (`:138-144`)。
- 反証条件: 上記の各迂回変異を一つずつ入れ、N1 がすべて失敗することを示す。より直接には option 集合と skeleton bytes の完全一致、および許可された import・I/O call の allowlist を固定する。
- 成果物影響: 将来、環境や別 module から得た承認者値を skeleton や発行物へ流す回帰が N1 を通過し、人間確認で決まるべき approver と、それに対応する approval hash が自動入力で確定しうる。

4. **所見 4: `verify` 本体に明示的な file 書き込みはないが、無書き込みテストは cold-start と外部 sidecar を覆わない**

- 種別: nit
- 根拠: `verify` 経路は read-only capture、JSON 検査、hash 計算、stdout/stderr 出力だけである (`tools/s8b_budget_approval_preflight.py:184-230`)。例外前後にも temporary file や部分書き込み処理はない。したがって application-level の明示的書き込みは確認されない。

  ただし snapshot は module import 後に開始され、repo と candidate 一個だけを見る (`orchestrator/tests/test_s8b_budget_approval_preflight.py:23-24,208-241`)。candidate sibling、system temporary directory、失敗経路は対象外である。通常の Python cold-start では import が repository 内へ `__pycache__` を作る可能性もあり、絶対的な「何も書かない」はこのテストからは証明できない。
- 反証条件: bytecode cache の無い fresh copy で直接 CLI の成功・失敗を実行し、repo、candidate parent、temporary root の完全 snapshot が不変であることを確認する。
- 成果物影響: 現時点で approval、pin、production 受理集合に変化はないため nit とする。

## 総括

- 停止級所見はない。
- 最重点の結論は、`verify` と `_load_budget_approval` の受理集合が同一ではないことである。
- 共通 payload 条件は現在ほぼ一致するが、pin、path、holdout authority、検査順序が異なる。
- この drift を検出する differential oracle test は存在しない。
- 現実装に argv、環境、git config、v1 `confirmed_by` から approver を得る経路はない。
- skeleton は exact key gate で production に拒否され、承認として読める値も持たない。
- production file は targeted `git diff` と `git status` で未変更であり、production 受理集合は変更されていない。
- approval 発行、`--approver`、既定補完、pin 書き換えは無く、D287 違反は認めない。
- 指示どおり pytest および実測は実行していない。