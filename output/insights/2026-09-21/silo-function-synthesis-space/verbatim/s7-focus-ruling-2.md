# 焦点再レビュー 2 巡目の裁定 (2026-09-21 22:4x JST)

- 入力: codex focus `codex/s7-focus-2.md` (NO-GO、閉包 23 件中 closed 18 / partial 5、must-fix 2・nit 3、refuted 2)。
- 判定: must-fix 2 件と nit 3 件を real として採用する。どれも既存規則の文面の訂正で、新しい gate・台帳の追加ではない (レビューが明記)。

| # | 所見 | 処置 (README の節) |
|---|---|---|
| f1 (must-fix) | `/ %` の結果型を「左辺の型」とした型表が C++17 の通常算術変換と不一致。literal の型の決め方、`unsigned long` と `unsigned long long` の別型、min/max の「同じ型」の意味が未固定 | §2.7 に「型の体系」を追加: 対象は LP64 の GCC、U32 = `unsigned int`、U64 = `unsigned long`、literal 接尾辞は `u` / `ul` だけ (`ull` 系を拒否して `unsigned long long` を排除)、`u` literal は値で U32 / U64、`ul` は U64。型表を通常算術変換どおりに書き直し (`/ %` も含む)、複合代入は代入先の型へ変換、`?:` と min/max は完全に同じ型だけ |
| f2 (must-fix) | namespace scope の `constexpr` も静的記憶域を持ち「静的・thread 記憶域の変数を定義しない」と衝突。宣言の型集合、void 補助関数の呼出し文、メンバ読出しの記法が未確定 | §2.5 / §2.7 / §8 と fragment 決定 5: 「書換え可能な持続状態 (静的・thread 記憶域の可変変数) を定義しない、namespace の constexpr 定数は可」に統一。§2.7: PolicyState メンバ・constexpr・局所変数・戻り型・引数の型を列挙、呼出し文 `helper(args);` を追加、代入先を 3 種に限定、メンバ読出しは `名前.メンバ` (引数名は自由)、switch の条件型と case label、末尾 return 規則の狭い読み |
| f3 (nit) | 字句規則を外す自己試験の期待が強すぎる (`<:` や単項 `bitand` は後段でも赤) | §3.3: 合法な二項の `x bitand y`・`a and b` を使う |
| f4 (nit) | 「時刻・set の大きさ・競合位置・共有状態を外すことは…A・B・auditor が支持」が広すぎる | §2.5: 時刻と共有状態は A 所見 6・B 所見 9 が支持、set の大きさと競合位置は草稿 §6 が外し A が型 15 の代理と評価、に書き分け |
| f5 (nit) | C 段合計は受入を先に丸めた値 | §6: 丸めずに足すと 2.40〜4.11 h と併記 |

- DW-O16 の 3 巡上限の 2 巡目。訂正後、codex focus 1 本 (3 巡目、最終) で閉包を確認する。3 巡目でも NO-GO なら fix を重ねず、親が残る所見を real / refuted に裁定して閉じ、根拠を worklog に書く。
