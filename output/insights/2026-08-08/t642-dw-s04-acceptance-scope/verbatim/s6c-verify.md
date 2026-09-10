結論は **NO-GO** です。受入全走に関する前 2 巡の誤読は閉じましたが、matrix 免除条件の A2 が回帰しています。

## 所見対応表

| 所見 | 判定 | 静的根拠 |
|---|---|---|
| (i) 通常経路の受入義務を弱める読み | `closed` | `だけ` は「変異 matrix」にだけ係り、句点後は「受入全走は免除せず」と独立して免除を否定する。[core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:79)。通常経路の受入再走も入口に残る。[入口:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:51) |
| (ii) 受入全走を特殊経路だけの義務に見せる読み | `closed` | 現文は特殊経路だけに正の義務を与える文ではなく、免除を否定する文である。特殊経路の文脈を引き継いでも、通常経路の義務を反対解釈で消す文法要素はない。 |
| 「免除」語彙／旧「対象外」の係り先 | `closed` | 現 snapshot の完全一致は `対象外=0`、`免除=2`、`省略=3`。「省略」は引数・子・prompt 内容の省略を指し、検査義務の免除とは競合しない。「対象外」と `scope 外` の混線も消えた。 |
| A2 matrix 免除の通常経路への漏出 | `regressed` | `CでもP` の `でも` は譲歩・添加であり、C を P の必要条件にしない。唯一の限定辞 `だけ` は「変異 matrix」に係り、`「実装しない」かつ実装差分ゼロ` には係らない。そのため matrix 免除を通常経路にも延長する読みを排除できず、入口51行目と衝突する。段4裁定が要求した「実装差分ゼロなら」の束縛にも戻っている。[段4裁定:28](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:28) |
| A3 実行点・期限 | `closed` | 「段7の記録前」が維持されている。[core.md:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:80) |
| A4 byte を理由に安全義務を削除 | `closed` | 受入実走・結果記録は維持され、実測も上限内。今回の A2 は byte 論法ではなく条件の係り受けの回帰。 |
| A6 docs-only 確定 | `closed` | `git status --short` は `docs/dev-wave/core.md` の変更だけ。実装面の差分はない。 |
| A7 brief scope と記録成果物 | `closed` | 規範編集と段7記録成果物を分ける裁定が維持される。[段4裁定:33](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:33) |
| B1 約束だけで充足 | `closed` | 「実走し、結果を worklog へ書く」という完了義務が残る。 |
| 条件の否定側 A1/A5/B4 | `scope 外` | 判定主体・不存在証拠・記録は裁定パッケージへ返されている。本判定では欠陥理由にしていない。 |
| `DW-S04` の推奨案要求 | `closed` | 選択肢 (a)〜(c) に対して明示的に **(b) を推奨**し、旧 decisions についても前向き supersession を推奨している。[段4裁定:51](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:51)、[同:57](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:57)、[同:62](/work/1/SFC/tanab/dev-wave-jobs/t642/s4-adjudication.md:62) |

## byte 実測

| ファイル | bytes |
|---|---:|
| `core.md` | 8,641 |
| `workers.md` | 4,575 |
| `mutation.md` | 3,674 |
| `operations.md` | 8,301 |
| **合計** | **25,191 / 25,200** |
| **余白** | **9** |

`wc -c` による静的実測です。pytest、`tools/run_tests.py`、`check_docs.py`、受入全走は実行しておらず、緑とは判定していません。

## 総括

**NO-GO。**  
受入全走に関する二つの誤読は closed だが、`でも` が matrix 免除を特殊経路の必要条件へ束縛せず、A2 が `regressed`。