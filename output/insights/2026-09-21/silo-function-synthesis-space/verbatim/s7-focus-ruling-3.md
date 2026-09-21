# 焦点再レビュー 3 巡目 (最終) の裁定と閉鎖 (2026-09-21 22:4x JST)

- 入力: codex focus `codex/s7-focus-3.md`。判定は NO-GO。2 巡目の f1〜f5 は 5 件とも closed。新たな must-fix 1、nit 1、refuted 3。
- DW-O16 の 3 巡上限に達した。fix を重ねた 4 巡目は回さない。親が残る所見を real / refuted に裁定して閉じ、根拠を worklog に書く。

| # | 所見 | 判定 | 処置と閉じる根拠 |
|---|---|---|---|
| g1 (must-fix) | 代入式を部分式に埋め込める。`(a.m = 1u) + (b.m = 2u)` を `helper(s, s)` で呼ぶと、同じ対象への順序づけられない 2 回の書込みで UB になる | real | README §2.7: 代入・複合代入は独立した式文だけに限り、部分式には書けないようにした。`++` `--`・カンマ演算子の禁止も明記した。§2.7 の「構造的に除く UB」と §3.3 の契約負例に追加した。fragment 決定 4 も同じ。**閉じる根拠 (親の検算)**: 残る副作用は、式の中の自前関数の呼出しの本体の中の代入だけになる。C++17 [intro.execution]/18 では、呼出し側の評価と呼ばれた関数の本体の実行は不定順序 (indeterminately sequenced) であり、順序なし (unsequenced) ではない。したがって UB にならない (結果は未規定になりうるが、未定義ではない)。これは受理集合を狭めるだけの訂正で、2 巡目までに閉じた規則を変えない |
| g2 (nit) | literal の説明 (`ull` を拒否すれば `unsigned long long` は現れない) は根拠が不正確 | real | README §2.7: `UINT64_MAX` 超の literal を拒否すると明記した。対象では `unsigned long` と `unsigned long long` がともに 64 bit で、候補型の列で先に `unsigned long` に収まる、という理由に直した。fragment は変えない (結論は同じ) |
| g3 (nit、所見 4 の補足) | 初期化と return の変換に代入表の同型制約が自動では掛からない (`return true;` が U32 を初期化しうる) | real | README §2.7 の型表: `=`・局所宣言の初期化・`return` の値・実引数に同じ変換規則を適用すると明記した。`return true;` を §3.3 の契約負例に追加した |
| 所見 3・4・5 | 数値の結果型・narrowing、宣言・文・constexpr の整合、帰属と fragment の整合 | refuted (不一致なし) | 処置なし |

- 閉鎖: 3 巡の焦点再レビューで閉包表の全項目が closed になった (1 巡目 → 2 巡目 → 3 巡目の f1〜f5)。3 巡目の新規所見 g1〜g3 は、上表の訂正で閉じたと親が裁定した。
