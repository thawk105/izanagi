# fix 仕様 — 段 6 レビュー (レンズ C / D) の must-fix 7 件に対する親の裁定

`final2-c.md` と `final2-d.md` の所見を親が裁定して確定した。**本書が fix の正本。**

## F1 (最優先・land blocker) — `_rotate_worklog` の分割点を projected entry 込みで選ぶ

**根拠**: レンズ D 所見 1。`_rotate_worklog` は `original_entries[-1]` を必ず現行 worklog に残すため、
ruling 5 件 + 本 wave の記録 (計 6 fragment) を畳むと、ローテーション後でも **104,462 bytes** となり
閾値 100,000 を超え、`rotation-capacity` で **plan 段階から失敗する**。本 wave の記録を最小にしても
回避できない (レビューは最小 fragment で計算している)。これを直さないと実 land に到達しない。

**裁定**: 分割点を「新 entry を含む projected worklog」に対して選ぶ。

- 新 entry が追加される場合、**元 worklog の最新 entry も archive へ移せる**ようにする
  (現行 worklog に残るのは新 entry なので、空にはならない)。
- 古い方から連続して移し、**現行 worklog が閾値以下になるまで**移す。
- ローテーション境界の連続性 (archive 最新の末尾 → 現行の先頭) は保つ。
  entry を飛ばして移してはならない。
- 新 entry が無い (= worklog fragment が 1 件も無い) 場合の挙動は**変えない**。
- 移しても閾値以下にできない場合は従来どおり `rotation-capacity` で失敗する。

## F2 — completion item の fence 判定が list 相対 indent を見ていない

**根拠**: レンズ C 所見 1。`FENCE_OPEN_RE` は raw 行頭 indent を 0〜3 に限定するが、item の継続行は
2 spaces 以上。`- ` の list container 幅 2 を除いた後の 2-space fence = **raw 4-space opener** は
CommonMark 上有効で、未閉鎖 fence は item 終端まで続く。実装はこの opener を見落とし、
fence 内の `  remaining: none` を trailer field と数えてしまう。

**裁定**: completion item の field 群を判定するときは、**list container の幅を考慮した fence state**
を使う。top-level 用 tokenizer (`_visible_markdown_lines`) の indent 許容を単純に 5 spaces へ
広げてはならない (`tools/check_docs.py` と別の過剰不可視化になる)。
item block 用の判定として分けること。
backtick / tilde、4-space / 5-space、未閉鎖 fence の負例をテストで固定する。

## F3 — 追記の replay guard が raw block の部分文字列で過剰拒否する

**根拠**: レンズ C 所見 2。`append.suffix in original` (対象 block 全体の raw 文字列) で判定するため、
継続行の例示や既存 prose に同じ byte 列があるだけで正当な初回追記が拒否される。

**裁定**: 判定対象を **対象 item の先頭行 (実際に追記される行)** に絞り、
**その行の末尾が suffix と一致するか** (`head_line.rstrip("\n").endswith(suffix)`) で判定する。

- 継続行・comment 内・fence 内・prose の部分文字列は判定に使わない。
- 同一 fold 内の重複 (`seen`) は従来どおり exact 一致で拒否する。
- 過去 fold の完全な replay は `FOLDED.md` の content hash が既に拒否している。
  ここで塞ぐのは「wrapper bytes だけ変えた再投入」と「同一 fold 内の重複」である。
- error ID `deferred-append-duplicate-suffix` は変えない。

テストに**正例**を足すこと: 対象 item の継続行や comment 内に同じ byte 列があっても
初回追記が受理されること。

## F4 — 項目 15 (空 / 空白 suffix) を別 node に分ける

**根拠**: レンズ C 所見 3。空 suffix と空白 suffix を同一テストで扱うと、shape gate を緩める変異
(N15) を入れたとき空文字が downstream の `"" in original` に必ず一致して
`deferred-append-duplicate-suffix` で赤くなる = 受理集合が変わっていないのに診断差で kill される。

**裁定**: 項目 15 を 2 つの独立テストに分ける (空 suffix / 空白のみ suffix)。
F3 で判定が `endswith` になると `"" ` の扱いも変わるので、**空 suffix は shape gate で確実に
拒否されること**を単独 node で固定する。

## F5 — 項目 25 と resume の oracle を構造検査にする

**根拠**: レンズ C 所見 5。項目 25 は rendered worklog の active 集合しか見ないため、
**実装が append を完全に捨てても緑になる**。resume も最終 bytes と `resumed_paths` しか見ておらず、
同じ after bytes を再書込みする実装を検出できない。

**裁定**:

- 項目 25 は `_parse_worklog_delta` の返値を直接検査し、
  **append が `operations` に不在かつ `deferred_appends` に存在する**ことを固定する。
  active 保存則の検査は残してよい (両方書く)。
- resume は、append を含む phase target を既に after 状態にしたうえで
  **phase への write が発生しないこと**を検査する (write を数える形にする)。

## F6 — producer 文書に `見送り追記` の閉じた文法を書く (**親が docs を書く。実装子は触らない**)

レンズ D 所見 2。`docs/spool/worklog/README.md` に次を明記する (親担当)。

- `見送り` が無くても `見送り追記` 単独でよい。両方ある場合だけ後順。
- section を置くなら 1 件以上、suffix は空白以外を含む。
- suffix 内 placeholder は許され plan 時に解決される。
- 日付・発火回数・「発火記録:」は author が書き、fold は補わない。

## F7 — 変異の再登録 (**親が行う。実装子は `output/` を触らない**)

レンズ C 所見 4。N01 は gate 無効化だけだと直後の `remaining[0]` で `IndexError` になり、
入力は依然拒否されたまま node が赤くなる (偽 kill)。P02 は `更新` と `見送り` が別 branch なので
片方だけの変異で項目 7 が赤くなり、非単一帰属になる。

親が spec を書き直す: N01 は「欠落時に安全に no-issue へ進む」形の anchor にし、
P02 は `更新` 用と `見送り` 用に分割する。

## 分担

- **fix 子 A**: `tools/spool_fold.py` のみ (F1, F2, F3)
- **fix 子 B**: `orchestrator/tests/test_spool_fold.py` のみ (F1 の land/rotation 正例、F2 の負例群、
  F3 の正例、F4 の分割、F5 の構造 oracle)
- **親**: F6 (docs)、F7 (変異 spec)、実走、統合 commit

**既存テストの名前・期待値は変更しない。**実装を甘くして緑にしない。
codex sandbox から計算ノードへ dispatch できないので、走らせられないなら「走らせていない」と書く。
