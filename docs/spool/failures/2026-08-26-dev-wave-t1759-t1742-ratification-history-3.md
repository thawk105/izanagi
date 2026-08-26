---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1759-t1742-ratification-history
seq: 3
---

## 新規

### {{F:canonical-jsonl-splitlines}}. canonical JSONL 検査が `splitlines()` のため CR を畳み、bytes と行の 1 対 1 性が成立していなかった [誤前提]

- 事象: 批准台帳の行検査 `_load_rows` は、各行が canonical JSON の bytes と完全一致することと
  末尾が改行であることを要求していた。ここから「blob の bytes と行 tuple は 1 対 1 である」と
  読めるが、実際には成立していなかった。行分割に `raw.splitlines()` を使っており、
  これは `\n` だけでなく `\r` と `\r\n` でも分割する。canonical 224 byte の blob と、
  1 行目の行末を CRLF にした 225 byte の blob が、同じ行 tuple を返すことを実測した。
- 根本原因: canonical 性の検査を「各行の bytes」に対してだけ行い、
  「行の連結が blob 全体と一致すること」を検査していなかった。分割器が改行の別種を
  受け入れる限り、行単位の canonical 検査は blob 単位の canonical 性を含意しない。
- 影響: 単独では受理 digest 集合を変えない (台帳へ書けること自体が hooks の外にある)。
  しかし本 wave は履歴検査を byte 前置比較から行 list 比較へ移す設計であり、
  その健全性の根拠にこの 1 対 1 性を置いていた。前提が偽のまま実装していれば、
  bytes が異なる 2 つの台帳が同じ受理集合を返し、byte 前置比較が拒否していた遷移を
  行 list 比較が受理する。
- 恒久対応: `raw.split(b"\n")[:-1]` へ変更し、CR を含む行は canonical 比較で落ちるようにした。
  {{D:ratification-history-dag-append}} の行 list 比較はこの 1 対 1 性に依存する。
  CR / CRLF を混ぜた台帳を拒否する負例テストと、
  この分割を `splitlines()` へ戻す変異を事前登録して検出力を固定した。
- 再発検知: 行単位の canonical 検査で blob 単位の canonical 性を主張する設計では、
  分割器が受け入れる区切り文字の集合を実測する。「行を連結すると元の bytes に戻るか」を
  1 例で確かめれば足りる。

## 再発

### F300

- **再発: 2026-08-26** — 同じ wave で 2 回連続して `rc=125` を踏み、**原因が本文の 2 系統の
  どちらとも違うことを実測で切り分けた。** 1 回目は変異走行中に親が同じ作業木へ spool fragment を
  置いた F383 型 (親の作法違反) だったが、2 回目は走行中に repo へ 1 byte も書いていない。
  変化していたのは**共有 main checkout の untracked 集合**である。観測は
  `--untracked-files=all` で行われるため、並行 wave が新しい未追跡 path を作るだけで bytes が動く。
  25 分の間に 24 行 851 bytes から 26 行 919 bytes へ増えていた。local main を進めなくても起きる。
  対処は本文の supersede が示すとおりで、**対象 commit だけを持つ独立 clone を `--source-repo` へ
  渡す**と観測点が clone 自身の 1 点に畳まれ、3 回目は `shared_snapshot_matches=true` / rc=0 で
  完走した (10/10 KILLED)。
  この機体で clone を用意する具体手順も記録する — submodule の URL が https のためオフラインでは
  そのままでは初期化できず、clone 内で `git config submodule.<path>.url` をローカルの
  `.git/modules/...` へ向け、`git -c protocol.file.allow=always submodule update --init --recursive`
  を使う必要がある (既定では `transport 'file' not allowed` で落ちる)。

### F357

- **再発: 2026-08-26** — enforcement source closure の member である
  `orchestrator/campaign/enforcement_source_ratification.py` を編集した状態で
  fixture consumer 3 file の焦点走を投入し、9 failed + 28 errors を観測した。
  描画された 21 件の error 理由はすべて `contract-loader-drift` の 1 型だった。
  統合 commit の後に同じ範囲を再走したところ 896 passed / 3 skipped へ解消し、
  実装差分由来の赤は 0 件だった。判定手順 (赤の理由行に `contract-loader-drift` があれば
  commit してから再走する) は既載のとおりで機能した。

## supersede 追記

- F600 **supersede: 2026-08-26** — 恒久対応を実施した。履歴検査を DAG の追記として定義し直し ({{D:ratification-history-dag-append}})、merge commit を台帳の改版と数えなくした。実測では現行 main で検査が通り、受理集合 1 件を読んだうえで終端が `enforcement-source-closure-unratified` に変わった。本エントリが挙げた「台帳が byte 不変のまま main を 1 commit 進めて緑のままであることを確かめる positive control」は負例テストとして実装済みである。ただし修理した module 自身が closure の member であるため closure digest は動き、本エントリが記録した `6d497998...` も現行値ではない。
