## 依頼文の読み

**推奨は B：計算ノードを使わず、commit 済み branch を残して land を保留する。**

[依頼の最終行](/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/request-md_1.txt:53)「計算ノードは使わない。」は、対象を限定しない独立した禁止である。生死確認の直後ではなく、記録・scope 外の指定を経た末尾にあり、**受入・変異も含む依頼全体の制約**と読むのが妥当。「probe だけ」という限定は本文にない。

他の依頼で受入が日常的に計算ノードを使う事実は、通常手順を説明する。しかし、本依頼の明示的な禁止を解除する根拠にはならない。

また、[段6裁定](/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s6-fix1-ruling.md:13)も、この禁止を理由に変異を未実施としている。受入だけを対象外とする根拠は、同裁定にある「login で走る」という前提だったが、その前提が誤っている。

## 各案の帰結

| 案 | 帰結 |
|---|---|
| **A：受入3 shard を実行して land** | 切り替えを前進させられるが、計算ノード禁止に違反する。受入が緑になっても、未実施の変異の扱いは別途残る。 |
| **B：計算ノードを使わず land 保留** | 禁止と land 条件を両方守り、実装・記録を保存できる。一方、変更を取り込まない後続 wave は sol・medium のままで、主目的は未完了となる。 |
| **C：login 実行・縮小受入・先行 land 等** | 現在の条件では採れない。計算ノードを使わず正式受入を完遂できる経路も、適用可能な免除も確認できない。 |

実装では、明示 shard は [login admission の対象から外れ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/tools/run_tests.py:2526)、[dispatch 分岐へ進む](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/tools/run_tests.py:2650)。shard を外しても、一般形は余裕不足や実行中のメモリ上限到達で dispatch しうる。「login から起動する」ことは、計算ノード不使用を意味しない。

[DW-S04](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/dev-wave/core.md:90)は、land が再検証した縮小受入以外の全走免除を認めていない。[DW-O27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/dev-wave/operations.md:202)の「lease を待たない」も資源使用の許可ではない。

## 推奨

**親は B を選び、必要なユーザー裁定を具体化して返すべきである。**

1. commit 済み branch と証跡を保持し、「実装・記録済み、正式受入・変異未実施、未 land」と報告する。
2. README と段6裁定の「明示3 shard は login で走る」という記述には、元の裁定を追跡できる訂正記録を添える。過去の焦点走は参考値のまま扱う。
3. 裁定待ち項目を「本 wave の正式受入3 shard と変異 matrix に限る計算ノード使用の可否」とする。変異の未実施記録を、免除の承認として扱わない。
4. 許可後に残る検証を実施し、[DW-O23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/dev-wave/operations.md:177)の通常経路で land する。README にある supervisor digest 変更のため、land 直前の daemon 稼働確認も必要となる。

これは [DW-STOP](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/docs/dev-wave/core.md:35)の「承認前提を覆す新事実・裁定/権限待ち・許可範囲で復旧不能」に該当する。今回の新事実は、正式受入を login 内で完遂できるという前提の崩壊である。

## やらない理由の最も強い形

A を今やらない最も強い理由は、**禁止された資源を使うと判明した後に、通常運用や完成の必要性を理由として親が禁止の適用範囲を狭める権限はない**ことである。必須の受入条件は land の条件であり、計算ノード使用の許可を生まない。

B への最も強い反論は、**切り替えが着地しなければ、ユーザーが求めた運用変更が後続 wave に届かず、完成直前の成果が止まり続ける**ことだ。他依頼で通常使う検証資源のために、再びユーザー手番を要求する負担もある。

この反論は重い。ただし、そこから導けるのは裁定を最小限・具体的にして早く解消することまでであり、明示的禁止を親が解除することではない。なお、[README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/output/insights/2026-09-30/codex-astra-ultra/README.md:68)によれば repo 外の next-tasks script は既に改訂済みなので、「切り替えは全く反映されていない」とも報告すべきではない。

## 総括

**B を推奨する。計算ノード不使用を守り、未 land の成果を保存し、受入・変異の実行許可をユーザー裁定へ返す。** 主目的は未完了と明記する。

本相談では静的確認のみ実施し、計算ノード使用・テスト実行・変更・子への委任は行っていない。