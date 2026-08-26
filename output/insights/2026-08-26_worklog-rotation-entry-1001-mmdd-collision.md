# worklog rotation が entry 1001 で塞がる — archive の file 名文法が entry 番号を MMDD と読む

- 日付: 2026-08-26
- wave: dev-wave-t1879-cir-cvn (branch `worktree-dev-wave-t1879-cir-cvn`)
- 発見の経緯: 本 wave の land が ff-only の直後の fold で `status=fold-failed` を返した。
  main は 1 bit も動かず `b253e0b7` のまま、fold の途中状態も残っていない。
- 一次資料: land 結果 JSON (`fold_gate_uncovered_families: ["rotation"]`)、
  `tools/check_docs.py` の `_archive_filename_entry_range` と `ARCHIVE_MMDD_TOKEN_RE`

## 何が起きたか

land は次の理由で fold を拒否した (原文は 22 件の違反の先頭 6 件)。

```
generated canonical validation failed (check_docs: 22 件の違反
  - docs/worklog.md:119: [T-139] の carry 参照先 entry (1001) が全域番号 universe に実在しない — 宙吊り参照
  - docs/worklog.md:120: [T-337] の carry 参照先 entry (1001) が ...
  ...)
```

fold は worklog が 100,000 bytes (`WORKLOG_ROTATE_BYTES`) を超えると最古の entry を archive へ
移す。本 wave の entry を足すと超えるので、entry 1001 が
`docs/archive/worklog-phase3-0826-1001.md` へ移される計画だった。
ところが移した先が「番号付き archive」として認識されず、`(1001)` を指す **821 本の carry stub**
が全域番号 universe から外れて宙吊りになる。

## 原因 (実測で確定)

`tools/check_docs.py` の `_archive_filename_entry_range` は archive の file 名を
`worklog-<phase>-<tail...>.md` の tail で分類する。tail の全 token が MMDD なら
**日付範囲の archive (`unnumbered`)** と判定し、`MMDD + entry` の形なら番号付きと判定する。
判定は前者が先に書かれている。

**entry 番号 `1001` は MMDD としても読める** (10 月 01 日)。したがって tail = `["0826", "1001"]` は
「2 つの日付」に見え、file は `unnumbered` になる。番号付き archive の集合へ入らないので、
その中の entry 1001 は全域番号 universe に現れない。

実測 (同 module を import して `_archive_filename_entry_range` を直接呼んだ結果):

| file 名の entry token | 分類 | entry range | MMDD として妥当か |
|---|---|---|---|
| `999` | numbered | (999, 999) | 否 |
| `1000` | numbered | (1000, 1000) | 否 (日 `00` は不正) |
| `1001` | **unnumbered** | **None** | **可 (10/01)** |
| `1002` | **unnumbered** | **None** | **可 (10/02)** |
| `1031` | **unnumbered** | **None** | **可 (10/31)** |
| `1032` | numbered | (1032, 1032) | 否 (日 `32` は不正) |
| `1101` | **unnumbered** | **None** | **可 (11/01)** |
| `1231` | **unnumbered** | **None** | **可 (12/31)** |

**塞がる entry 番号は 1001〜1031、1101〜1130、1201〜1231 である** (以後 2001〜2031 等も同型)。
**1000 が無事だったのは偶然である** — 日にあたる `00` が MMDD 文法で不正だからにすぎない。

## 射程 — これは 1 wave の問題ではない

- **worklog は現在 95,933 bytes で、閾値まで 4,067 bytes しかない。**
  次に rotation を起こす wave は、内容によらず entry 1001 を archive へ送ろうとして同じ赤になる。
  **land 経路は事実上いま塞がっている。**
- 本 wave の branch は受入緑 (`dev-wave-acceptance-receipt/v5`、`verdict=child-green`、
  `tested_main=b253e0b7`、`tested_tip=fb11265c`) まで到達しているが、この欠陥のため land できない。
- land の結果 JSON 自身が `fold_gate_uncovered_families: ["rotation"]` と報告している。
  **`spool_fold.py --dry-run` はこの赤を手前で出さない** — dry-run は計画 JSON を出すだけで、
  生成後の canonical 検査を走らせないからである。**wave 側の安い関門では検出できない。**

## 直し方の候補 (実装は本 wave の scope 外)

いずれも `tools/check_docs.py` の実装面であり、Codex `role=author` と専用の受入が要る。

1. **判定順を入れ替える。** `len(tail) == 2 and is_mmdd(tail[0]) and is_entry(tail[1])` を
   `all(is_mmdd(...))` より先に評価する。ただし
   `worklog-phase3-0826-0901.md` のような**日付 2 つの範囲名**が既存にあるなら、
   その族を番号付きと誤判定する。既存 archive の実名を全件走査してから決める。
2. **番号側に接頭辞を付けて曖昧さを消す。** 生成側 (`spool_fold.py`) が
   `worklog-phase3-0826-e1001.md` のように entry を明示する。既存 file 名は不変なので、
   文法は新旧両方を受理する必要がある。
3. **file 名でなく本文で決める。** archive の H2 見出しから entry 番号を採り、file 名は
   索引の補助に留める。最も曖昧さが少ないが、変更面は最も広い。

### 既存 file 名の棚卸し (本 wave で実施済み)

`docs/archive/` の `worklog-*` を全件見た。**「日付 2 つの範囲名」は実在する** —
`worklog-phase3-0702-0713.md`、`0714-0716`、`0721-0722`、`0722-0724` など。
4 token の混在形 (`worklog-phase3-0726-12-0727-19.md` = mmdd, entry, mmdd, entry) もある。

**それでも案 1 は既存 file を壊さない。** 既存の日付範囲名は 2 つ目の token が
`0713` のように先頭 0 を持ち、entry token の文法 `[1-9][0-9]*` に一致しないからである。

**しかし案 1 は将来の曖昧さを消さない。** 10 月以降に
`worklog-phase3-1001-1015.md` のような日付範囲名が作られると、
`1001` は MMDD、`1015` は entry token の両方に一致するので、今度は逆向きに
「entry 1001〜1015 の範囲」と誤読される。**4 桁 token が [1001..1231] に入り MMDD の形をしている限り、
file 名だけでは entry 番号と日付を区別できない。** これは順序の問題ではなく文法の問題である。

**したがって案 1 は当座を通すだけの緩和であり、恒久対応は案 2 (番号側に接頭辞) か
案 3 (本文で決める) のどちらかである。** 案 2 は新旧両方の文法を受理する必要があり、
案 3 は変更面が最も広い。**どちらを採るかは裁定に値する。**

## 併せて記録すべきこと

- **fold gate は rotation 族を覆っていない。** 生成後の canonical 検査で初めて落ちるので、
  wave は受入まで全部通してから land で落ちる。**安い関門を先に緑にする規律が、この族では効かない。**
  gate 側に rotation を含める改修も候補に入れてよい。
