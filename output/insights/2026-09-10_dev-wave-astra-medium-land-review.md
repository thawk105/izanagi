## 総括

**対象範囲でrealのblocking所見はありません。** docs修正は再試行と正式停止を整合させており、main側mergeによる当waveの変更消失も認めません。

手順から導かれる親の挙動は次のとおりです。

| 場面 | 親の挙動 |
|---|---|
| land rc=11 | `lock-busy`。終了・新turn要求をせず、既存branchで再試行する。 |
| main進行中foldのdirty | 他sessionの処理中と確認できるdirtyには触れず、終端を待ってmainを再照合する。任意のdirtyを許可する意味ではない。 |
| main進行でstale | 新mainを監査し、固定SHAをwave側へmerge。条件を再評価して再試行する。監査列はtested main..tested tipを維持する。 |
| postcondition failure | 停止する。mainが進んでいても成功扱いせず、HEAD・理由・既存branchと再開情報を報告する。 |
| ユーザー裁定待ち | 該当段へ進まず停止する。再試行指示で裁定を迂回しない。 |

根拠は [DW-O23](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-astra-medium/docs/dev-wave/operations.md:164) と [DW-STOP](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-astra-medium/docs/dev-wave/core.md:34) です。

**refuted**

- **競合時の不要な終了指示が残る**：Skill・command・DW-S09はいずれもDW-O23へ統一済み。DW-CTXの非0終了条件は外部supervisorの契約で、今回のCodex親にland rc=11で終了を要求するものではありません。
- **再試行が安全義務を弱める**：postcondition failure・裁定待ちの停止、検査、所有物保護、rebase／force／push禁止は保持されています。
- **main側変更がモデル／effort・受入runnerを変える、wave成果を消す**：incomingは9ファイルの文書差分。`32603d385..2ff0ce2c9`のpatchとmergeの第一親差分は完全一致し、元waveの変更6ファイルのblobもmerge前後で一致しました。astra／mediumと関連pin・fixtureは保持されています。
- **foldでfragmentが根拠なく消える**：`2ff0ce2c9`の追加receipt 5件すべてで、削除fragmentのSHA-256と一致し、tested_tipも直前親`eca05cd21`に一致しました。採番はD1936・D1937・F941です。受入関連の裁定記録はありますが、runner実装の変更ではありません。

静的照合と`git diff --check 5f2e23129..HEAD`を実施し、後者はrc=0。ファイル変更・commit・pytest・受入・land・全史provenance監査は実施していません。モデル可用性や旧receiptの再実走可能性は判定していません。