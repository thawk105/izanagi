## 所見

対象の「稿」は [2026-09-18-t1998-balanced-stock-inline-accepted.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2674-recovery-codex/docs/paper-story/results/2026-09-18-t1998-balanced-stock-inline-accepted.md)、「insight」は同waveの [README.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2674-recovery-codex/output/insights/2026-09-18/t2674-t1998-results-doc/README.md)を指す。

**新規 must-fix 0、should-fix 2、nit 0。旧must-fix 8件は閉鎖を確認した。**

1. **should-fix／real — 稿:30、insight:67：投入回数の記録から不存在保証へ広げている。**
   「2本目の試行は存在しない」の根拠として挙げた事前登録§7は、投入回数の**規則**である。指定receiptは1 job、9月13日の実行記録は投入1回、9月15日の記録は再投入なしを支持するが、他の試行の不存在を網羅的に証明しない。焦点再レビュー自身もこの限界を記録している。
   **影響:** 報告対象が1試行であることに、資料が保証していない網羅性を付け足す。性能値・consumer判定の不一致ではない。
   **最小是正:** 凍結稿は保持し、results入口の追補で「指定receiptと両waveの記録から確認した1試行を指し、他の投入の不存在を保証しない」と限定する。追加の全保存先監査は不要。

2. **should-fix／real — insight:78：B-5の無限定な不存在断定が周辺記録に残存。**
   「再解析の判定JSONが保全されていない」は、同README:27のjob dir内の探索、および稿:181・355の「参照した保存先では確認できない」より強い。`ef74d66c6`は稿本文を直したが、この行は直していない。
   **影響:** 未発見を未保全と転記する、旧B-5と同じ量化の問題。
   **最小是正:** insightへ保存先限定の訂正を追記する。旧レビュー逐語や凍結稿の書換えは不要。

3. **既知must-fix／real — worklog fragment:18・48、insight:73：旧受入を完了の根拠にしない。**
   親が訂正予定と明示した既知事項として、新規件数には含めない。指定JUnitの該当2 testcaseはいずれも`error`で、module fixtureの`git ls-files --others --exclude-standard -z`が30秒でtimeoutしている。assertion不一致ではないが、**旧rc70は受入成功ではない**。

**以下の疑いはrefuted。**

- **主要値・hashのF1型転写不一致:** 原WAL全40 recordから8点の標本・median・CVを再計算し一致。登録対は `4330570 / 3893509 = 1.1122537536191646`、改善率 `11.225375361916456`で、producer・consumer・稿・README追加行が一致する。
- **identityの取り違え:** 掲載された原典fileのSHA-256、測定commitの事前登録・job body・投入器・pipeline・loop等のblob、gitlinkを照合し一致。source digest・tracked diff・binary digest・receipt IDも原WALと一致する。
- **判定の昇格・混同:** consumer `accepted`とproducer `complete`、legacy正しさ検査と性能判定、median比とA-1対差平均を区別している。A-2/A-6とのプール、B-7充足、有意差・区間推定への昇格はない。consumer是正による受理集合拡大と残る非保証も明記されている。

## 対応表

行番号は現在の稿。旧findingの番号を維持する。

| 旧finding | 判定 | 原典との確認 |
|---|---|---|
| A-1 must-fix | closed | 稿:371。first-parent境界は`b1a3d45d…`、前親`e0b1c336…`は是正commitを含まない。日時も一致 |
| A-2 must-fix | closed | 稿:268・460。終了時刻・712Sはstderr、投入時刻はqstat／group ID |
| A-3 must-fix | closed | 稿:451。`genome`は`build_start.payload` |
| A-4 must-fix | closed | 稿:108。lockの`ycsb_*`キーと文字列値が一致 |
| A-5 must-fix | closed | 稿:198。resultの値は配列`["not_required"]` |
| A-6 must-fix | closed | 稿:84・462。逐語引用と要約の区別が正しい |
| A-7 must-fix | closed | 稿:231。resultは23 key、`correctness`なし |
| A-8 should-fix | closed | 稿:166。共有identity fieldsの一致に限定 |
| A-9 should-fix | closed | 稿:229・302。検査件数はD1993理由節に根拠あり |
| B-1 must-fix | closed | 稿:296。温度ドリフトの排除ではなく未評価と記述 |
| B-2 should-fix | closed | 稿:132・361。source一致とpatch／diff対応未照合を区別 |
| B-3 should-fix | closed | 稿:222。測定時blobの呼出し経路・既定値と一致。実行argvとは区別 |
| B-4 should-fix | partial | 稿:233。8点表は存置、比較文は削除。編集判断として非阻害 |
| B-5 should-fix | partial | `ef74d66c6`による稿:181の修正は確認。ただしinsight:78に残存 |
| B-6 nit | closed | `ef74d66c6`で稿§5.5の指摘された経緯重複を削除 |

**回収対象全体ではclosed 13／partial 2／regressed 0。** 稿本文に限ればB-5もclosed。

## 親briefへの異議

- **HANDOFF:31の「docs差分に到達しない」から完全な非帰属までは導けない。** 変更対象は13 fileで実装差分0、t1259のtest・probeにも旧tipとの変更なし。これは支持できる。一方、fixtureは実作業木を走査するため、作業木状態・I/O・負荷の影響は静的検査では切り分けられない。最新mainで単独走が通っても、旧timeout原因の確定とは別である。
- **「残partialを訂正済み」は稿本文について正しいが、周辺記録までの閉鎖ではない。** insight:78が残る。
- 旧briefの全8点掲載は要件ではなく編集判断。ただし現稿は登録外点から結論を導いておらず、表の削除を着地条件にする必要はない。

## 総括

**内容監査による新たな着地阻害はない。** 旧must-fix 8件の閉鎖、`ef74d66c6`の本文修正、回収差分13 file・実装差分0を確認した。既知の受入完了記述は訂正が必要で、旧rc70を成功として回収してはならない。

静的検査のみ実施した。pytest・consumer再実行は行っていない。9月15日の判定JSON、全保存先での不存在、patchとtracked diffの再現対応、環境digestのpre-image、実際のland時刻、旧timeoutの根因は未検証。これらを新たな保証へ昇格させず、当時の測定・判定は保持する。
