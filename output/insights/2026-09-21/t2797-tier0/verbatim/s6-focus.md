**NO-GO。must-fix 1件。** F1〜F6の修正は静的に確認できました。F7も実装されていますが、M18の実測は未提示です。別途、Tier0通過・投入後の`duplicate-skip`でB計上を消す経路が残っています。編集・commit・テスト実行はしていません。

表中の略号は次の実ファイルを指します。

- P = [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/p3_s4_loop.py)
- D = [b5_generator_contrast.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/b5_generator_contrast.py)
- R = [b5_generator_contrast_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/b5_generator_contrast_report.py)
- T = [test_b5_tier0.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/tests/test_b5_tier0.py)
- S = [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/tests/test_p3_s4_loop.py)

実測の扱いには限界があります。[f4:37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/focus-f4.log:37)は **4,813 passed／20 skipped** ですが、個別nodeの結果・skip理由を列挙していません。同log:1は受入全走ではない旨を明記しています。[probe2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-tier0/mutation-probe2-summary.txt)の実変異の記録名は`MISMATCH expected=SURVIVED`です。以下では、これを正式なKILLED判定へ読み替えず、記録された失敗nodeを根拠にします。

| 所見ID | 状態 | 根拠 file:line | 根拠の実測 |
|---|---|---|---|
| A1／B1／F1：通常挿入点検査 | closed | T:149、272、291、332。legacy／v2の計16ケースにreceipt依存skipなし。順序・perf binary・拒否・例外同一性を検査 | probe2:22 M2で順序を含む16node、:39 M3でv2順序等5node、:75／82／89 M9／M10／M10bで拒否6node、:96 M11で両build-I/O＋ASTが失敗。f4は集計上失敗なし |
| A2／B2／F2：既存seam追従 | closed | S:10856の共通fixtureで準備・build・smoke通過を供給。S:10894のauthority／submission照合、:10920のduplicate非復元検査を維持 | f4:37の集計。両node個別のPASS表示はない |
| A3／B3／F3：自走入口 | closed | T:504の`pytest.main([__file__, "-q"])` | f4:37の集計。自走入口単独の実行記録はない |
| B4／F4：追加writer認可 | closed | P:2550から準備・buildへ進み追加認可なし。後続`run_campaign`へ認可入力を渡すP:2608は維持 | f4:37は回帰集計。削除そのものの根拠は静的照合 |
| B5／F5：ReviewReceipt削除 | closed | P:2201〜2217はGeneratorReceipt／Noneと不正型拒否 | f4:37は回帰集計。型集合の根拠は静的照合 |
| F6：comment変異でもdriftで落ちる | closed | T:193でidentity準備を差し替え。P:2469／3164の両呼出しに有効 | probe2:3でM0 **SURVIVED、rc=0、失敗0件**。M2等の失敗nodeも残る |
| F7／BのT-2632合成懸念 | partial | P:1519にoutcome追加、:1656でvariantなしなら空WAL参照、:3203で実provenance公開。S:7487にケース追加 | f4:37の集計は失敗なし。ただしprobe2:3〜130にM18はなく、事前登録した負例の実測は未確認 |
| A補足／Bの親生死確認：実perf cache再利用・verify／bench継続 | not-addressed（提示実測上） | T:454〜472に実buildの確認は残るが、T:122の任意receiptに依存 | f4・probe2にはcache hit／hash一致／実verify・bench継続を特定できる記録なし |
| B nit：重複parameter／gateway assert | not-addressed（裁定どおり不採用） | T:73〜75、driver test:935、report test:717 | probe2:107に両arm、:123に`applies_to`を含む失敗node。削減されていないことと整合 |

fixture変更については、次の範囲で検査の実効性を保っています。

- **fix1cのlegacy契約選択**：T:173〜178はOTHERにPegasus契約を対応させていますが、P:2535ではsiteがOTHERなので`env_contract`を追加せず、P:2583のlegacy buildへ進みます。T:278は呼ばれたAPIと`trace=False`を検査します。ただし実OTHER環境のadmission／build互換性を証明するfixtureではありません。
- **fix1dのidentity差し替え**：identity回復は検査対象外になりますが、Tier0、smoke、gateway、parser、bench lock、sidecar writer、provenance writer、早期return、rc 3は差し替えていません。T:239のprofileは観測用です。M0と配線変異の結果は、driftだけで赤になる状態からの改善を支持します。
- **fix2のseam**：S:10870は実際にsmokeを恒常passedへ置換しています。このseamをTier0の正しさの証拠には数えられません。一方、目的である後続authority・submission・duplicate非復元のassertは残り、Tier0自体はTの通常挿入点検査が担います。
- **規律1／2**：P:2594のsmoke結果はsidecarに入り、D:352では3項目へ射影されます。性能入力はD:468、certified判定はD:417、endpoint選択はD:440で別途成立条件を要求します。probe2:116のM15には数値非流出testの失敗が記録されています。今回確認したfixture変更が、本番のverify／anomaly／benchを迂回させる経路は見つかりませんでした。

**新規所見 N1 — must-fix：投入済みduplicateでBを取り消す残存経路**

対象は[D:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/campaign/b5_generator_contrast.py:367)です。これはfixが新設した分岐という指摘ではなく、今回の「投入後＝B」という要求との残存不整合です。

具体的な経路は、P:2604でsubmission公開 → `run_campaign`がskip → P:2620で`duplicate-skip` → P:3203でprovenance公開成功 → CLIがduplicateを出力、です。classifierはD:334で認めた`submitted=True`をD:367でFalseへ戻します。初回attemptならD:647でBが増えず、D:807で`proposal-rejected`になって系列停止します。R:315〜318はterminal eventのあるslotを回収対象から外すため、reportでも補正されません。

**放置時の成果物：最初のsearchでこの経路を通ると、有効なsubmissionがあるのに台帳・reportはA=1／B=0となります。certifiedへの誤採用はありません。**

さらに、[driver test:215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/tests/test_b5_generator_contrast.py:215)と[:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2797-tier0/orchestrator/tests/test_b5_generator_contrast.py:381)は、このFalse／B=0を期待しています。恒真assertではありませんが、期待値が今回の計上契約と逆です。f4の緑では排除できません。

推奨修正は、duplicate分類でも確認済みsubmissionを保持し、系列停止・非certifiedは維持することです。投入証拠なし／ありを分け、後者のB保持をdriver→reportまで検査してください。

F7についてもう一点、裁定の「provenance例外ならdriverが分類不能」という説明は実コードと一致しません。D:631はrcに依存せずsidecarを分類するため、Tier0拒否sidecar公開後のprovenance失敗でもD:354から候補拒否になります。**M18で子のrc 3検査が落ちる見込みと、driverが系列停止することは別の主張**として扱う必要があります。

再照準M4（rr95）とM18、親の生死確認は未確認です。rr20の15node失敗を、rr95の単一理由性の証拠には数えません。

## 総括

**NO-GO — must-fix 1件（N1：投入済みduplicateのB消失）。**

F1〜F6はclosed、F7は実装確認済み・変異実測未確認です。f4の集計成功を、受入全走や実build生死確認の完了とは扱えません。