# 段 4 裁定 (consult A の所見 19 件 + 代替候補 2 件)

| # | 判定 | 採否 | 処置 |
|---|---|---|---|
| 1 S1 の台帳不一致 (intro 0.63 分、story 0) | real / must-fix | 採用 | stage_walls.py を訂正 (intro の終端 = brief-s1.md、story は起点 = brief で下界 0) |
| 2 「親のみ」は残差 | real / must-fix | 採用 | 「未分類残差 (合計 − 子・走・land・撤去の union)」へ改称。S1・段 7 区間を残差の「うち」と書かない |
| 3 非加法・第 3 位の順位依存 | real / must-fix | 採用 | 加法分解 (優先順位 A / B) を追加。全 12 では第 3 位が配賦で変異 ↔ codex、impl 7 では残差 > 変異 > codex で安定、と書く |
| 4 起点の出所 (first 4 + worklog 1、backup は gate) | real / should | 採用 | backup の起点を gate へ。出所欄を表に残し、平均は「今回の構成 (impl 7 / docs 5) の標本平均」と明記 |
| 5 抜き取り検算 | refuted (一致) | — | — |
| 6 PRR の誤記 (母集団 = t2803/t2804/t2813/t2153 の変異 + t2807 の prerun 6、fig13 は含まない; queue_wait_s 0.1〜30.8 秒; 53 秒 + 隙間 7.5 秒 = 60.5 秒) | real / must-fix | 採用 | 本文を訂正 |
| 7 qsub→compute-visible は代理区間 | 判定不能 → 表記変更 | 採用 | 「ノード側で可視になるまでの代理区間」と書き、PRR 帰属は D805 + peer 観測に整合する仮説として書く |
| 8 self-run で gate は弱まらない | refuted (弱まらない) | — | 「観測誤りは MISMATCH または PARSE_ERROR (F71) の fail-closed に落ちる」へ表現を直す。fig13 1 file の実績であり全 test への同値性証明ではないと書く |
| 9 self-run の適用条件不足 | real / must-fix | 採用 | v2: 適用は「自走の node 集合が `--collect-only` と一致し login 実行が許される test file」に限定、conftest / autouse fixture・環境変数・import 副作用・parametrize・pytest 専用 allowlist は dispatch probe へ |
| 10 ERROR / Skip / node 形式 | real / should | 採用 | v2: 「観測集合は自走の FAIL と ERROR を含め、F71 の形式へ正規化」を 1 句で書く (fig13 m1 = 1 failed + 3 errors = 4 node で final 一致) |
| 11 sha256 だけでは DW-O19 を満たさない | real / should | 採用 | v2: 「復元は `DW-O19` に従う」を主文にし sha256 は付記。DW-M05 の編集停止は self-run 中も適用と書く |
| 12 DW-M05 削減が独自 harness の義務を弱める | real / must-fix | 採用 | 削減 3 を取り下げ (DW-M05 本文不変)。不足 bytes は DW-M08 内の圧縮と workers 前文で賄う |
| 13 「後は結果値と commit だけ」が記録後検査と矛盾 | real / must-fix | 採用 | v2: 「確定済み事実の本文と検査手順の準備」に限定、未測定欄・placeholder を作らず、記録後検査 (DW-S07) は省かない |
| 14 効果算術 | real / must-fix | 採用 | 5 本平均 10.17 分、t2344 (7.2) を入れた 6 本 9.68 分、impl 7 本 (t2807 = 0) では 5.72 分 / wave = 3.4%。3 分への短縮は未実測の条件付き試算と書く |
| 15 (b) は CLAUDE.md 9 の具体化 | real / should | 採用 | 記録に「純増は dev-wave 固有の指定 (前倒しできる物・できない物)」と書く。「親は待つだけ」は撤回 (final 中の login 監査あり) |
| 16 削減 1・2・4・5 は安全義務を落とさない | refuted (落とさない) | — | 採用のまま |
| 17 −9 bytes は改行処理で確定 | real / should | 採用 | 実 file へ当てて layer_bytes.py と check_docs で実測 |
| 18 却下候補の見積り精度 | real / should | 採用 | 裁定パッケージでは「資料から示せる規模」と「仮説 / 上限例」を分ける。fix の同木再利用は DW-S05-A に既にある → 候補から外し「t2344 は fix ごとに別木を作った (DW-S05-A からの逸脱)」の観察として記録 |
| 19 (b) の配置は DW-M05 | real / should | 採用 | (b) を DW-M05 末尾へ。「1077 bytes で最大」は撤回 (DW-O01 1231) |
| 代替候補 (i) preflight で即停止走を防ぐ (impl 平均 0.5 分) | 規模が小さい | 不採用 | 裁定パッケージにも入れない (観察として記録) |
| 代替候補 (ii) 焦点走の実行場所判定 (fig13 focus-2 wall 24 分 vs test 106 秒) | 実行場所は runner の gate (login 拒否 rc=16、D612 系) | 不採用 | 受入・実行場所の gate は変えない (引数)。裁定パッケージへ「焦点走の wall と test 時間の差 (上限例)」として載せる |

**(b) の確定:** 手順変更 = 「変異 final の待ちは job dir で確定済み事実の本文と検査手順の準備に充て、未測定欄・placeholder は作らず、記録後検査は省かない」を DW-M05 末尾へ。効果は「final 終了 → 受入投入の直列区間 (impl 6 本 平均 9.7 分、7 本 平均 8.3 分) の一部」であり、短縮量は条件付き試算 (準備可能な部分を 3 分へ寄せられれば impl 7 本平均 5.7 分 = 3.4%)、本 wave では実測しない (本 wave は変異 final を走らせない docs-only)。

**(a) の確定:** DW-M08 に self-run を「既定」でなく「適用条件を満たす test file の既定」として書き、条件と戻し先を明記、復元は DW-O19 主文。

**変異 matrix:** 実装面差分ゼロ (docs-only) → 免除 (DW-S04)。受入全走は免除しない。段 6 = 独立 read-only レビュー 1 本 (改訂後 docs と一次資料・所見の照合) + check_docs + spool dry-run + 三軸走査 + 受入全走。
