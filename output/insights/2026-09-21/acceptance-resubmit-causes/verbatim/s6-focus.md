**NO-GO。数値と費用配賦の訂正は一致しましたが、所見3の「3件とも同一tip」に裏付け不足が残ります。** 書込み・検査の再実行はしていません。

以下、`R`＝[診断README](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/output/insights/2026-09-21/acceptance-resubmit-causes/README.md)、`J`＝`/work/1/SFC/tanab/dev-wave-jobs/`、`Q`＝`J/dev-wave-acceptance-resubmit-causes/`。job名はすべて `J/dev-wave-<名前>/` を指します。

| 所見 | 判定 | 根拠（READMEの節・一次資料・再計算値） | 残る指摘 |
|---|---|---|---|
| 1 | **closed** | R §4.2・§4.3・§5 D4・§6。storyの `acceptance-final.chain.log:1,44` と `acceptance-final-1.started.txt:1` は19:45:19→21:05:57＝4,838秒。backupの `acceptance-final2.chain.log:1,26` は20:26:29→21:05:25＝2,336秒。合計 **7,174秒＝119.5667分→119.6分**。D3の145秒、D4初回門番の745＋158＋171＋254＝1,328秒を加えると **8,647秒＝144.1167分→144.1分**。D4再門番・失敗外側も下記のとおり一致。 | なし |
| 2 | **closed** | R §5 D3・D4・E、§8。t2797の `acceptance-final2.chain.log:1`、`acceptance-final2-1.started.txt:1`／`.finished.txt:1` は04:38:06→04:40:32→04:52:36。**門番146秒＋外側724秒＝870秒＝14.5分**、各表示は2.4＋12.1分。final3の1,515秒＝25.2分は最終緑側として明確に除外。t2803の `acceptance-final2.chain.log:1,5,11` は23:32:04→23:34:29→23:34:33、**145＋4＝149秒＝2.5分**。D4再門番も分類別会計への非加算を明記。 | なし |
| 3 | **partial** | R §5表(ii)・B（109・115行）。[worklog:726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-resubmit-causes/docs/worklog.md:726) はT-2817の2件について、同一tipの単独再走と、追記commit後の受入再投入を明記。`Q/timelines-all.txt:427,438,448` の投入tipも異なる。backupの `HANDOFF.md:24,25` は焦点走2/2緑と、その後の競合解消mergeを記録する。 | **1759まで「同一tip」とする証拠がない。** `focus-1.log:6,10,13` はcwd・2件・2 passedを示すが、実行tipを示さない。「3件とも同一tip」をT-2817の2件に限定し、1759は「焦点走2/2緑、tip一致は資料から未確認」とする。must-fix。 |
| 4 | **closed** | R §5表・B・G、§8、§10。`operations.md:162–164` のpost-claim mergeと事前取り込み条件を区別し、D2/D3の条件適合は未確認と明記。storyの `acceptance-final.chain.log:44–46` はD1の停止を裏付ける。B/Gの「防げない」は「防止可能性を確定できない」へ訂正。 | なし。「逸脱は見つからない」は同じセルの未確認範囲を含めて読む限り、遵守認定にはなっていない。 |
| 5 | **closed** | R §8候補2・3（142・143行）。inventoryへの追加、修正方法、未測定費用の指定はなく、検討・調査の要否に限定。`verbatim/origin.md:3–8` の診断範囲と整合する。 | なし。訂正文にgate・台帳・一般化の追加や、受理集合・門番・holdの意味論変更、規律2の緩和を指示する文は見つからない。 |
| 6 | **closed** | R §9（149–152行）。値なし前方参照を削除し、値と証拠ファイルを記載。`Q/three-axis-scan-2.log:20` の候補32,091、同`:39–44,59–64` の各holdout 4件、本waveへのhitなしと一致。`Q/check_docs-2.log:1` は「違反なし」。 | なし。保存ログ自体に終了コードは明記されていないため、rc値の独立確認まではしていない。受入未実施の明記は結果placeholderではない。 |
| 7 | **closed** | R §5 E・§8候補1はDW-O12へ訂正。`operations.md:93–95` に最終受入は記録commit後という命令がある。D1のF902は解消例、D3は類例へ限定。D3の直接根拠はt2803の `acceptance-final2.chain.log:9–11` の著者行不足とpreflight停止。 | なし |
| 8 | **closed** | R §4.1（62行）を「試行番号付きreceiptが各1本」に訂正し、保存記録から証明できる範囲も明記。不変の `verbatim/classification.md:71` は旧機械出力として維持されている。 | なし。今回のclosed対象は指摘されたreceiptの数え方。主要表全体の再監査を行ったとの意味ではない。 |

D4の検算は以下のとおりです。時刻の終点・外側区間は各jobの `acceptance-final-1.started.txt:1`／`.finished.txt:1`、再門番の終点は `acceptance-final-2.started.txt:1` で照合しました。

| job | 再門番の一次資料・時刻差 | 失敗側外側wall |
|---|---|---|
| t2814-cleanup-command | `gate-loop-final.log:11`、02:48:28→02:50:30＝**122秒＝2.0分** | 02:46:42→02:47:28＝**46秒＝0.8分** |
| t2804-provenance-timeout-contract | `gate-loop-final.log:6`、23:14:06→23:16:38＝**152秒＝2.5分** | 23:11:55→23:13:06＝**71秒＝1.2分** |
| t2243-collection-diag | `acceptance-final.chain.log:8`、22:55:12→22:57:43＝**151秒＝2.5分** | 22:53:53→22:55:12＝**79秒＝1.3分** |
| t2153-witness-requested-us | `acceptance-final.chain.log:12`、21:18:17→21:20:37＝**140秒＝2.3分** | 21:15:50→21:18:17＝**147秒＝2.5分** |

失敗側外側は計343秒＝5.7分、範囲0.8〜2.5分。§6のt2804／t2153の **1.2／2.5分、再門番2.5／2.3分**も一致します。

**新規1：焦点再レビュー未実施という工程記録が古くなる〔should〕**

- **根拠：** R §9b末尾（169行）は「焦点再レビューは投げていない」と記すが、今回の依頼で実施している。
- **影響：** 今回の結果を反映した記録としては工程が事実と食い違う。`operations.md:88–90` の実施手順を記録する規律にも関わる。
- **提案：** 今回の対応表と結果に置き換える。数表の再集計が不要であることと、訂正した派生値の原データ照合は区別する。

## 総括

**NO-GO**

- **must-fix：1件 — 所見3。** 1759を含む「3件とも同一tip」を、一次資料が示す範囲に限定する。
- **should：1件 — 新規1。** §9b末尾を今回の焦点再レビュー実施・結果に更新する。
- **nit：なし。**