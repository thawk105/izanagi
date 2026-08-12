## 総括

- real 所見: **0 件**
- must-fix: **0 件**
- nit: **2 件**
- 最も危険だった候補: raw 行番号のずれによる fail-open。ただし全指定境界で parser と raw 分割の行境界が一致するため **refuted**。
- pytest/build: **実行 0 件**。静的査読のみで、緑とは報告しない。

### 1. raw 行分割 — refuted

[parser](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/diff_quarantine.py:556) の universal-newline 変換と、[raw 分割](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:85) は、いずれも `\n`、`\r`、`\r\n` を同じ行境界として数える。

- CR-only: 境界数は一致し、raw 側だけ直前 payload に `\r` を残すため hole なら拒否。
- CRLF/LF 混在: 境界位置は一致。CRLF hole は拒否、LF hole は exact 時のみ受理。
- 末尾改行なし: 両方とも最後の segment を1行として保持。
- 空ファイル: 両方1個の空 segmentだが marker がなく拒否。
- `\n\r`: 両方2境界。CR 側の空行は raw では `b"\r"` となるが、後続行の添字はずれない。
- 複数行 hole: slice 長は `hole_last - hole_first + 1` で、旧 `hole_text` の要素数と一致する。空 hole も双方0行。

したがって行番号ずれによる fail-open はない。

成果物影響: certified 選択・レポート・台帳の受理集合や参照は変わらない。

Nit: 混在改行、末尾改行なし、`\n\r` の専用回帰テストはない。ただし現実装の境界対応は静的に成立している。

### 2. 受理集合 — refuted

新実装が受理するには raw hole が厳密に `I + E_m`（`I = b"  "`）でなければならない。この場合、parser 側の同じ1行は `"  " + E_m` となり、旧条件でも

```text
strip("  " + E_m) == strip(E_m)
```

が成立する。従って `A_new ⊆ A_old`。変更前に拒否され変更後に通る安定した source はない。

CR、余分な空白、tab、複数行は縮小側にだけ倒れる。

成果物影響: 承認外の新規 certified 候補や台帳 commitment は生成されない。

### 3. 例外境界 — refuted

binary 再読と分割で通常発生し得る `OSError`、`UnicodeError`、`TypeError`、`ValueError` は [既存 catch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:101) 内にある。slice は範囲外でも `IndexError` を出さない。正規表現も固定 pattern と `bytes` の組合せで、新しい通常例外種は見当たらない。

`MemoryError` は catch 外だが、旧 parser もファイル全文の text read/splitを行うため新規の例外種ではない。新実装は発生閾値を多少下げるものの、現 source は22,709 bytes・728行で、追加常駐量は概ね0.1 MiB未満。通常の成果物経路の must-fix とはしない。

なお直接 `evaluate()` では [BuildAdmissionError 専用 catch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:813) を抜けるが、標準 campaign caller は [外側で `Exception` を abort 化](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/loop.py:266)する。

成果物影響: 通常入力では admission-error の分類、certified 値、レポート、台帳参照は不変。

Nit: 極端な巨大 source では追加割当てにより `MemoryError` の閾値が下がり得る。

### 4. 性能・観測者効果 — observer-effect 懸念は refuted

binding 付き評価では binary 再読は実際に経路へ入る。ただし [build 前の admission](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:798)で一度だけ実行され、trace-disabled binary の benchmark 計時区間には入らない。

追加コストは22.7 KiBのread、728行分のregex走査・小規模割当て。静的見積りでは campaign wall timeへの小さな固定費で、`fitness_tps`、CV、certified 判定には加算されない。

成果物影響: 性能値・選択・レポート・台帳の測定値は変わらず、変わり得るのは成果物外のpre-build所要時間だけ。

### 5. 裁定遵守 — 違反なし

未commit差分は次の3ファイルだけだった。

- `axis_trigger_gating.py`
- `pipeline.py`
- `test_campaign.py`

共有 parser、`emit_predicate`／`canonicalize_predicate`、例外文言、8c所有ファイルは未変更。A-7のbinding省略経路への結線も追加されていない。drift検査はBEGIN/ENDを各1件に限定した閉区間内で `#if/#else` を探している。

成果物影響: plan-v2で認可された「binding付き lane の受理集合縮小」以外へ、certified選択・レポート・台帳の意味は拡張されていない。