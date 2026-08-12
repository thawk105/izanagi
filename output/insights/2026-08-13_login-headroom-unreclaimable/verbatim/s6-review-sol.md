静的レビュー結果は、blocker 1 件、must-fix 2 件、nit 1 件です。現状のまま land すべきではありません。Web・pytest・変異実走は行っておらず、緑判定はありません。

## 仕様 §1〜§4 の照合

| 仕様項目 | 実装 | 判定 |
|---|---|---|
| required 5 キー維持 | `login_headroom.py:365-380` | 適合 |
| slab / unevictable は optional | `login_headroom.py:466-467` | 適合 |
| `memory.current` 2 度読み | `login_headroom.py:436,453` | 形は適合。ただし blocker あり |
| `c2` は `memory.stat` 後 | `login_headroom.py:452-453` | 適合 |
| base は `max(c1,c2)` | `login_headroom.py:459` | 適合 |
| frozen dataclass と新規 field | `login_headroom.py:209-225` | 適合 |
| clean file 算式 | `login_headroom.py:243-251` | 適合 |
| `reclaimable > base` は `None` | `login_headroom.py:252-253` | 適合 |
| unknown は base へ fallback | `login_headroom.py:256-261` | 適合。ただし回帰テスト不足 |
| raw field の意味維持 | `login_headroom.py:231-237,460` | 適合 |
| admission 2 経路 | `login_headroom.py:880,1087-1092` | 適合 |
| 診断の必須 4 要素 | `login_headroom.py:843-860` | 文字面は適合。ただし原因診断は不十分 |
| raw-current peak の明記 | `login_headroom.py:1117-1120,1135-1140` | 適合 |

定数 `CEILING_BYTES`、`RESERVE_BYTES`、`MAX_LOCAL_BUDGET_BYTES`、`MIN_LOCAL_BUDGET_BYTES` は `login_headroom.py:29-32` で HEAD と同一です。比較演算子も `required > effective_ceiling` のままです。

## 所見 1: endpoint の `max(c1,c2)` では transient cache の ABA を検出できない

- 深刻度: blocker
- file:line: `orchestrator/campaign/login_headroom.py:436,452-459,240-254`、`orchestrator/tests/test_login_headroom.py:266-308`
- 再現条件: `c1=1000` の時点では全量が回収不能、`memory.stat` 読取時だけ clean file 900 bytes が追加され、`c2` 前にその cache が消えて再び回収不能 1000 bytesになる。実装は `base=max(1000,1000)=1000`、`reclaimable=900`、`admission=100` とする。`reclaimable <= base` のため snapshot 不整合にもならない。天井を `RESERVE_BYTES+200`、estimate を 100 bytes とすれば実装は exact boundary で LOCAL、実際の危険量では DISPATCH になる。
- 成果物影響: 本来 DISPATCH の試行が LOCAL に受理され、OOM・同居プロセス圧迫によって certified 選択、材料レポート、試行台帳の実行集合や結果が変わる。

現在のテストは c1 と c2 の単調な増減だけを検査し、stat 読取中だけ reclaimable が増減する ABA schedule を扱っていません。段 3 の非原子 snapshot 所見は完全には閉じていません。

## 所見 2: unknown fallback が必ず `unreclaimable_base_bytes` を使うことをテストできていない

- 深刻度: must-fix
- file:line: `orchestrator/campaign/login_headroom.py:256-261`、`orchestrator/tests/test_login_headroom.py:266-308,344-408`
- 再現条件: `current=100`、`unreclaimable_base=200`、`slab=None`、天井 `RESERVE_BYTES+101`、estimate 1 byte とする。現実装は 200 へ fallback して DISPATCH するが、fallback を `memory_current_bytes` へ戻す変異なら 100 となり LOCAL になる。既存 degrade テストはすべて `current == base == 100` なので、この危険な変異が生存する。
- 成果物影響: c2 増加と optional stat 欠落が重なったとき、試行台帳の受理集合が DISPATCH から LOCAL へ拡大し、certified 選択とレポートの入力試行が変わる。

`c2 > c1` と unknown を同一 node で組み合わせ、判定反転まで固定する必要があります。

## 所見 3: `_decision_locked` の理由だけでは閾値超過を再構成できない

- 深刻度: must-fix
- file:line: `orchestrator/campaign/login_headroom.py:843-860,879-889`、`tools/mutation_fanout.py:1571-1575`
- 再現条件: admission 100 bytes、予約 0、天井 `RESERVE_BYTES+200`、estimate 101 bytes とする。理由文には raw current、回収不能量、判定占有量、予約しかなく、estimate、固定 reserve、effective ceiling、required が出ないため、1 byte 超過した事実を理由文から再構成できない。
- 成果物影響: mutation fanout のレポートへ保存される `admission.reason` が拒否算術を証明できず、レポートから受理・拒否判定を監査できない。

optional 欠落キー名、`snapshot 不整合`、raw current、判定占有量は正しく出ています。文字列結合も正規の観測値では例外になりません。しかし、段 3 で real とされた「何で落ちたか」はまだ部分的にしか閉じていません。

## 所見 4: grant 用テストは仕様記載の LOCAL／DISPATCH 反転になっていない

- 深刻度: nit
- file:line: `orchestrator/tests/test_login_headroom.py:734-763`
- 再現条件: `grant_budget` の available を旧 `memory_current_bytes` へ戻すと、テスト条件では available 100 bytes、`min_bytes=1` のため DISPATCH ではなく 100-byte LOCAL になる。テスト自体は期待予算 900 bytesとの差で赤になる。
- 成果物影響: 変異は現状でも予算 assert により検出されるため成果物変更の見逃しはないが、plan-v2 §5 の「旧式なら DISPATCH」という帰属説明とは一致しない。

## 例外・テスト弱体化の確認

新 property は不正な手作り dataclass 値なら `TypeError` を投げ得ますが、production の値は `_parse_uint64()` 由来です。また admission 中の評価は、`admit()` の `login_headroom.py:1174-1192`、`reserve()` の `:1215-1235`、`grant_budget()` の `:1075-1159` がそれぞれ `Exception` を捕捉して DISPATCH へ倒します。例外が LOCAL を許す経路は見つかりません。

既存 `test_every_observation_failure_is_none_and_dispatch[stat_missing]` は `test_login_headroom.py:566-570,620-670` に残っています。既存 assert の削除、期待値の緩和、xfail、skip の追加はありません。既存 helper の固定 field は同じ既定値を持つ keyword 引数へ置換されており、既存期待値の変更ではありません。

## 総括

- blocker: stat 読取中だけ cache が出入りする ABA schedule で、判定占有量を真の回収不能量より過小評価する。
- must-fix: unknown fallback を c2 込み base から c1 へ戻す危険な変異を現行テストが殺せない。
- must-fix: `_decision_locked` の診断は閾値算術を欠き、成果物レポートから拒否原因を監査できない。