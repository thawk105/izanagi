## 判定

**GO（本レンズ：must-fix 0、should-fix 3、nit 2）**

対象は `5f9e8c549..068f664dd`。範囲外の実装変更や、spool fragment 以外の必須成果物の欠落は見つかりませんでした。

## 所見

| ID | 重大度 | 根拠 | 提案 |
|---|---|---|---|
| B-F1 | should-fix | [README §7](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/output/insights/2026-10-01/t2853-r2-fig10/README.md:200) と結論5の「測定の汚染は無い」「延びたのは wall と確保 node 時間だけ」は観測より強い。probe 通過・rounds 1・bench 所要の一致は記録されているが、性能への影響全般の不存在までは示さない。 | 断定を削り、既存 probe 通過、追加 round なし、bench 所要が原 attempt と同程度だった、という観測に限定する。追加検査は不要。 |
| B-F2 | should-fix | [README §7 案1](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/output/insights/2026-10-01/t2853-r2-fig10/README.md:202) の「原 attempt と同じ1 jobあたりの所要なら約2.2 node 時間」は前提と合わない。記載された原 Elapse なら `5 × (386 + 841 + 1218) / 3600 ≈ 3.40`。 | 削除を優先し、lock 局所化の案だけ残す。2.2を残すなら、待ち時間などの控除項と算式を明記する。 |
| B-F3 | should-fix | [README §6](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/output/insights/2026-10-01/t2853-r2-fig10/README.md:174) の式は、3 request の Elapse 合計にさらに「3 request ×」を掛けている。記載結果の22,995 node秒・6.39 node時間は正しい。 | 式を `5 node × (1531 + 1527 + 1541) s = 22,995 node秒` に直す。 |
| B-F4 | nit | [caption 置換2](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig10/output/insights/2026-10-01/t2853-r2-fig10/verbatim/s5-author.md:46) は原 attempt の説明とR2の説明を重ね、「research verdict ではない」を二度述べる。段4で保留された冗長性は実在する。 | 置換2を省くか、R2の outer status の意味を一文に縮める。原 attempt の文脈は既存の出所情報で追える。 |
| B-F5 | nit | README の結論2・§4冒頭・§8で非合成を反復し、§5.1では§0項8の受理条件を再列挙している。前例fig11にもある構成だが、本題を短くできる。 | **§0は変更しない。** 必須の「言えないこと」は§8に残し、途中の限定は参照へ縮める。結論3・4も図と表の一項にまとめられる。 |

## 確かめたこと

- 必読4資料を読了。差分19ファイルを確認した。変更は insight 配下18ファイルと `docs/phase3.md` の4行追記だけで、driver・policy・生成器・既存図・原 attempt の変更はない。
- 投入・Elapse・完走・outer status・効果・正しさ・対照表・R2図・条件差・言えないことが記載されている。同梱ログ、表、provenanceとの整合を確認し、PNGも目視した。図・表・provenance・record のSHA-256はREADMEと一致した。
- §7は実際の費用超過の原因と引継ぎの記録であり、節そのものは範囲内。「本 wave では実装しない」と明記され、案を実装済みと装っていない。新しいgate・検査基盤・一般台帳も追加していない。
- phase3の追記は、他のR2行と同じ「実施条件・結果・成果物・残件・記録先」の構成。超過費用の記載も今回固有の事実として妥当。
- 親briefの段2・3省略は、前例と固定済み§0、段4のP1/P2処置から妥当。レビュー2本は入力・正しさと過剰・削除で役割が分かれており、追加段階も削減も不要。
- §0は投入前commitから変更されていない。

## 確かめていないこと

- テスト、再描画、計測、編集、commit、子agent起動は実施していない。実行成功は同梱ログの記録との照合である。
- repo外のraw・receipt全件、node上のprocess状態、継続承認の通信原文は独立検証していない。
- spool fragmentは指定どおり対象外。依頼逐語が参照する `common.txt` は指定ディレクトリに存在せず、その共通条件は未確認。

## 総括

再実行と記録という依頼の範囲は守られています。§7を削除する必要はありません。汚染不存在の断定を観測へ戻し、費用の式と試算を整理すれば、記録の精度が上がります。