# 段 6 fix 指示 — 親の裁定

段 6 の敵対レビュー 2 本 (sol 3 件 / luna 10 件) と、親が実走した焦点走の赤 4 件を裁定した。
**F-1 から F-9 がこの fix の全 scope** である。

## 親の裁定 (レビュー所見の real / refuted)

| 所見 | 判定 | 対応 |
|---|---|---|
| R-1 台帳 digest が list marker を含まない | **real / must-fix** | F-2 |
| R-2 candidate が正当な非 carry 項目を包含する | **real / must-fix**。親が実測で確認: `[T-500] (D837)` `[T-500] (Python 3)` はいずれも candidate=True・strict=False となり、**正当な入力が赤になる** | F-3 |
| R-3 / V-7 target 単位 dict が occurrence 数を潰す | **real / must-fix** | F-4 |
| sol「恒真テスト 2 件」 / V-8 streaming テスト | **real / must-fix** | F-7 |
| V-1 採番 archive 正例に許可外の第 2 補正 | **real / must-fix** | F-6 |
| V-2 / V-3 / V-4 / V-5 変異 M3・M4・M5・M8 が診断文字列だけの kill | **real / must-fix** | F-8 |
| V-6 変異 M10 を殺すテストが無い | **real / must-fix** | F-9 |
| V-9 共有 fixture は空台帳 + opt-in helper が最も安全 | **real / must-fix。この案を採用する** | F-1 |
| V-10 定数 specialize は旧実装 control を阻む | **nit / 見送り** | 対応しない。setup error と偽緑は区別できており、旧実装 control は親の実測が担う |

## F-1 共有 fixture から合成 archive を外す (最優先。赤 4 件の原因)

実装子は `_KNOWN_CARRY_ID_MISMATCH_ARCHIVE` (entry 73〜78、日付 2026-07-26) を
`_build_min_repo` / `_archive_readme` / `_write_archive_index` の 3 箇所へ**無条件に**入れた。
これが次の 4 件を赤にしている。**この 4 件の期待値は絶対に変更しない。**

```
test_placeholder_guard_entry_rotation_keeps_ledger_green
  → 「最終 archive と現行 worklog 先頭の順序を一意に決定できない」
test_placeholder_guard_missing_target_family_is_violation
  → placeholder 台帳の観測数が全部 0 になった
test_spool_fold_rotation_output_passes_real_check_docs
  → 「global ordinal 境界日 2026-07-26 の系列が (1) から始まらない」
test_spool_guard_accepts_only_explicit_exact_complete_active_transaction
```

採用する構成は V-9 のとおり。

- **基本 fixture** (`_build_min_repo` の既定) では、複製した checker の
  `KNOWN_CARRY_ID_MISMATCHES` を `{}`、`EXPECTED_KNOWN_CARRY_ID_MISMATCHES` を `0`、
  `MIN_EXPECTED_CARRY_REFERENCE_COUNT` を `0` へ specialize する。合成 archive は入れない。
  `_archive_readme` と `_write_archive_index` も元の形へ戻す。
- **専用 helper** (opt-in) だけが、実台帳の 4 digest と合成 archive 73〜78 を**同時に**入れる。
  台帳と archive を片方だけ入れる経路を作らない (片方だけだと必ず不整合になる)。
- 置換はすべて `count(...) == 1` を assert してから行う。置換対象が 1 でなければ setup を失敗させる。

**production 側の値は変えない。** specialize するのは合成 repo へ複製した checker だけである。

## F-2 台帳 key を list marker 込みの物理行 digest にする (R-1)

現行は `_top_level_items` が返す `item_text` (marker を除いた論理項目) の digest を内側 key に
している。そのため `- [T-208] ...` を `1. [T-208] ...` へ書き換えても同じ digest になり、
既知として受理されてしまう。

内側 key を **list marker を含む raw 論理行**の digest へ変える。複数行に折り返された論理項目でも
一意になるよう、項目の開始行頭から論理項目の終端までの raw slice を使う。
確定 4 件の期待値は次のとおり (親が base d8f777a4 で実測した物理行 digest)。

| task ID | 物理行 | sha256 (新しい内側 key) |
|---|---|---|
| `[T-208]` | `- [T-208] 変わらず ((73) 参照)` | `34209a9f738fe90a9f3cd57531c3ef900085884b79fc6c1dd833fdf3c46ee45c` |
| `[T-209]` | `- [T-209] 変わらず ((73) 参照)` | `f46fe17fc7831678f44471bf5c7c460be6bd65bac6a7e5a47cd0535c150a54a6` |
| `[T-210]` | `- [T-210] 変わらず ((73) 参照)` | `f5e03b5bb559682274a1731a73e6d4dca0208c7846fabe312cad1834bc74c14e` |
| `[T-211]` | `- [T-211] 変わらず ((73) 参照)` | `5e4a6cb7d118a27df5b710ca20351ea9e5e45ef764ed559b597dc9931140b666` |

外側 key (entry 77 の H2 raw 行 digest) は変えない:
`6bc0dfb4679d3be38c2a97c7c81c595b62a2b033800e5b27d7f9a63b75c3814b`。

marker を書き換えた行が**既知として受理されない**ことを固定する負例テストを足せ。

## F-3 candidate 述語の過包含を直す (R-2)

親の実測:

| item_text | 現行 candidate | strict | 判定 |
|---|---|---|---|
| `[T-500] (D837)` | True | False | **正当な入力が赤。直す** |
| `[T-500] (Python 3)` | True | False | **正当な入力が赤。直す** |
| `[T-500] (953)` | True | True | 正しい |
| `[T-500] (073)` | True | False | 正しい (捕まえたい不正形) |
| `[T-500] (73 )` | True | False | 正しい (捕まえたい不正形) |
| `[T-500] 変わらず ((73) 参照)` | True | True | 正しい |
| `[T-500] 変わらず ( (73) 参照)` | True | False | 正しい (捕まえたい不正形) |
| `[T-500] backlog (2 件)` | False | False | 正しい |
| `[T-500] 実装 (D95) を守る` | False | False | 正しい |

短縮形の候補述語を**括弧の中身が空白と数字だけ**の形へ絞れ
(先頭ゼロと余分な空白は候補に残すこと — それが捕まえたい不正形である)。
legacy 風の候補は `変わらず` と `参照` の両方を含む条件のままでよい。

**不変条件: 厳密 parser の受理集合は candidate 集合の部分集合でなければならない。**
これを壊すと正常入力で `candidate != parsed` が発火する。
`[T-500] (D837)` `[T-500] (Python 3)` が候補にならないことと、
`(073)` `(73 )` `変わらず ( (73) 参照)` が候補として赤になることを、両方向のテストで固定せよ。

## F-4 target 単位 dict をやめ、分類ごとに occurrence を全件数える (R-3 / V-7)

`missing_by_target` と索引三分類の 3 つの dict は target を key に `setdefault` するため、
同じ target を指す 25 件の occurrence が 1 件へ縮退し「他 0 件を抑止」と表示される。
異なる target が 404,326 個ある最悪経路では、dict を全保持したうえ最後に sort するので
メモリが O(C)、時間が O(C log C) になる。

各分類を **(occurrence の total counter) + (最大 20 件の sample list)** に置き換えよ。
target 単位の dict を保持しない。sample の選び方は先着順でよい。

**既存挙動との整合:** `test_backlog_guard_dangling_carry_reference_is_violation` は
dangling 1 件の入力なので、occurrence 単位でも同じ finding が 1 件出る。
このテストは変更してはならない。もし変更が必要になったら、それは実装が誤っている。

## F-5 抑止行の語を曖昧にしない

`他 N 件を抑止` の N が occurrence 数であることが読み手に分かる語にせよ。
F-4 で全分類が occurrence 単位になるので、分類名と単位を揃えること。

## F-6 採番 archive 正例の第 2 補正を外す (V-1)

許されている fixture 補正は「**参照先の次の一手に同じ ID を置く**」だけである。
現在は archive entry 1000 の次の一手へ `T-002` を足すのと同時に、
current entry 1 へ `- [T-002] consumed` も足しており、**無関係な rotation transition まで
修復している**。後者を外し、entry 1 が元から消費する ID を archive target と carry に使う形へ直せ。
2 つの条件を同時に変えないこと。

## F-7 恒真なテストを直す (sol「恒真テスト」/ V-8)

1. `test_backlog_guard_carry_target_index_states_are_distinct` の `kind="missing"` は、
   carry 固有の key 不在分岐を削除しても universe/index 集合不一致 finding で通ってしまう。
   **carry 固有の finding** (source path、task ID、target を含む文字列) を assert せよ。
2. `test_backlog_guard_carry_references_are_streamed` は即座に `list(references)` するため、
   全件 materialize してから `iter(list)` を返す実装でも通る。
   最初の `next()` の前後で先読みが起きていないこと (例えば `scan.parsed_count == 1`) を
   確認する形へ直せ。source/item 側も一手ずつ消費を記録できる generator を与えること。

## F-8 変異 M3・M4・M5・M8 を単一理由で殺せる入力へ再照準する (V-2〜V-5)

`DW-M03` により、**診断文字列だけの赤を kill と数えてはならない**。
各変異について、**その層だけが拒否理由になる**入力へテストを直せ。

- **M3** (登録 key ごとの `actual == expected` 検査を撤去): 現在は occurrence を消すと
  parsed 数も減って母数下限が別理由で赤にする。合成 checker の下限を 0 にするか、
  同数の有効 carry を足して、**台帳照合だけ**が拒否理由になる入力にせよ。
- **M4** (台帳総数の固定値照合を撤去): 現在は未観測のゼロ digest を登録するので
  per-key 検査が別 finding で赤にする。**台帳は実在する 4 件のまま
  `EXPECTED_KNOWN_CARRY_ID_MISMATCHES` だけを 5 へ変える**入力にせよ。
- **M5** (candidate == parsed の同数検査を撤去): 現在は individual な invalid sample が
  findings に残るので赤のままになる。sample を同数違反の付帯情報へまとめるか、
  **同数検査の finding だけが拒否理由になる**入力を作れ。
- **M8** (occurrence を target 単位へ collapse): 現在は collapse で既知 3 件も消えて
  台帳の `actual=0` が赤にする。**台帳を既知 1 occurrence だけに specialize し、
  同じ target / 同じ ID の未登録 source を 1 件足す**入力にせよ。

## F-9 変異 M10 を殺すテストを足す (V-6)

`numbered_archive_input_complete=False` を direct に渡し、
**停止 finding 以外の carry finding (同一 ID 不一致・台帳・母数・candidate・universe/index) が
1 件も増えないこと**を assert するテストを足せ。
これが無いと、早期 `return` を撤去する変異を誰も殺せない。

## 費用の上限 (親が実測済み。超えてはならない)

- 緑経路: `python3 tools/check_docs.py` は現在 wall 12.50 秒 / maxrss 162MB
  (baseline 10.52 秒 / 157MB の 1.19 倍)。**倍化させないこと。**
- 最悪赤経路 (全 carry 不一致): 現在 wall 10.44 秒 / maxrss 134MB / finding 21 行・4,983 bytes。
  F-4 の変更でメモリと時間が**増えない**ことが要件である (dict 廃止なので減るはず)。

## 実走について

計算ノードへ dispatch できない可能性が高い。走らせられる範囲だけを走らせ、
走らせた nodeid を報告せよ。走らせられないものは「実装済み・未実走」と明記せよ。
**緑を偽って報告する方が、走らせないことよりはるかに悪い。**
