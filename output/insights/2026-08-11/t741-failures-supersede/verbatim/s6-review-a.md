## 所見

### 1. topology の expected 順と新規 F の追加順が一致しない

- 判定: **real**
- 重要度: **must-fix**
- 根拠: [tools/spool_fold.py:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:100)、[tools/spool_fold.py:955](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:955)、[tools/spool_fold.py:1989](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1989)、[tools/spool_fold.py:2000](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:2000)
- 成果物影響: 変更前に受理されていた `新規` fragment 群が `failure-topology` で拒否され、E 節が許していない受理集合の縮小になる。

fragment は `(wave, seq, ledger rank, path)` 順ですが、F の `symbols` は `(wave, namespace, seq, offset, path)` 順です。同じ wave/seq で authored 日の異なる failures fragment は許可されており、両 fragment の先頭 F heading の offset が異なると、採番順は offset 順、`new_failure_entries` の追加順は path 順になります。

例えば path 順が A→B、heading offset が A=100/B=10 なら、採番は B=`F2`、A=`F3`、描画は `F3`→`F2` です。一方 expected は `F2`→`F3` なので、正当な fold が拒否されます。混在正例は単一 fragment 内しか試していません（[test_spool_fold.py:1400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1400)）。

是正案: 既存の採番結果を変えず、`allocated_failure_numbers` を実際の `new_failure_entries` 追加順に並べて expected を作る。symbol sort 自体の変更は既存出力 ID を変え得るため避ける。同一 wave/seq・異なる authored/path・異なる heading offset の 2 fragment 正例を追加する。

### 2. HTML comment で R4 の誤用検査を迂回できる

- 判定: **real**
- 重要度: **must-fix**
- 根拠: [tools/spool_fold.py:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:365)、[tools/spool_fold.py:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:438)、[tools/spool_fold.py:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:748)、[test_spool_fold.py:1340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1340)
- 成果物影響: supersede を再発として誤記録でき、failures 台帳の意味分類と後続監査の攻撃面認識が誤る。

次の recurrence payload は拒否されません。

```markdown
- **super<!--x-->sede: 2026-08-10** — 誤用
```

HTML comment は表示されないため、Markdown 上の可視文字列は `- **supersede: ...` です。しかし `_mask_html_comments` は comment を削除せず同じ長さの空白へ置換するため、検査文字列は `- **super        sede:` となり `startswith("- **supersede:")` を通り抜けます。現行テストは裸の完全一致と通常 prose だけで、comment 分割を固定していません。

是正案: fence 内を不可視のまま保ちつつ、R4 の prefix 判定用には HTML comment を空文字として連結した可視投影を使う。少なくともラベル内部・`- ` とラベル間の comment 分割を拒否し、fence 内の decoy は従来どおり受理するテストを加える。

### 3. Unicode line separator を受理後に黙って削除する

- 判定: **real**
- 重要度: **must-fix**
- 根拠: [tools/spool_fold.py:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:57)、[tools/spool_fold.py:764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:764)、[tools/spool_fold.py:1612](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1612)、[test_spool_fold.py:1239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1239)
- 成果物影響: 受理した supersede 本文と canonical へ挿入される本文の bytes が異なり、R1 の「`- ` + 解決後本文」契約を破る。

末尾 detail に U+2028 を含む次の item は validate を通ります。

```text
- F1 **supersede: 2026-08-10** — detail<U+2028>
```

regex は LF 以外を `[^\\n]` として許します。validate 側の `splitlines(keepends=True)` では U+2028 が candidate に残る一方、fold 側の `splitlines()` は U+2028 を行区切りとして除去します。そのため `_failure_symbols` の issue は空なのに、`_failure_parts` の本文から U+2028 が消えます。同型は U+2029 等にもあります。

是正案: LF-only 契約に合わせて両経路を `split("\n")` で統一して文字を保存するか、Unicode line separator 全般を shape 違反として明示的に拒否する。validate と fold の行モデルを必ず一致させ、U+2028/U+2029 の回帰テストを追加する。

## 変異 M1〜M10 の生存判定

実走していないため、以下はコード読解による判定です。

| 変異 | 判定 | 理由 |
|---|---|---|
| M1 | **KILLED 見込み** | [test_spool_fold.py:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1093) が `- ` を含む全 bytes を固定しており、`* ` では赤になる。topology は関与しない。 |
| M2 | **KILLED 見込み** | [test_spool_fold.py:1465](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1465) が F197 見出し位置への splice を固定しており、EOF 挿入では赤になる。 |
| M3 | **KILLED 見込み** | [test_spool_fold.py:1478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1478) が最終 LF 後への挿入 bytes を固定している。 |
| M4 | **KILLED 見込み** | [test_spool_fold.py:1108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1108) の期待列が recurrence→supersede。逆適用では行順が反転する。 |
| M5 | **KILLED 見込み** | [test_spool_fold.py:1329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1329) は既存長行の substring である短行を受理する正例であり、substring 拒否へ変えると赤になる。 |
| M6 | **KILLED 見込み** | [test_spool_fold.py:1239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1239) の `2026-13-45` case が、regex のみでは受理されて赤になる。 |
| M7 | **KILLED 見込み** | [test_spool_fold.py:1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1364) は validate 後の parser を monkeypatch して偽見出しを注入しており、postcondition 無効化時は `_raises` が失敗する。 |
| M8 | **KILLED 見込み** | [test_spool_fold.py:1340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1340) の bad fixture が issue code の完全一致を要求する。 |
| M9 | **KILLED 見込み** | [test_spool_fold.py:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1093) の byte-exact と、[test_spool_fold.py:1381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1381) の forged heading/topology の双方で赤になる。裁定どおり冗長 gate。 |
| M10 | **KILLED 見込み** | [test_spool_fold.py:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1093) が `supersede 追記` 単独 fragment なので、「新規必須」を足すと plan 前に赤になる。 |

## 総括

静的レビューでは **real / must-fix が 3 件**です。特に所見 1 は R4 以外の受理集合縮小、所見 2 は R4 の直接迂回です。所見 3 は validate と fold の parser 差による accepted-content の欠落です。

M1〜M10 はすべて KILLED 見込みですが、これは未実走判定であり、緑・closed は主張しません。編集、commit、pytest 実行はいずれも行っていません。