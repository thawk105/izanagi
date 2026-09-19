**静的レビューはGO。最終採用はNO-GO（最終file単独走・変異・受入が未完）。** `7975385b55… → eda92f107` を照合しました。実装の新規阻害所見はありません。

| 所見 | 状態 | 照合結果・成果物への影響 |
|---|---|---|
| B must：同node排他を失う候補を出荷しない | **closed** | 共通job bodyは基準とbyte一致。候補専用test/harnessも除去。最終3codefileはfix `3e2a8327` とbyte一致。 |
| B should：両rank・会計・failureを照合する | **closed** | 両rankがcomplete、failureファイルなし。4caseの個別JSONと集約結果が一致し、会計に両jobの出力境界を確認。片側doneだけの旧wait receiptには依存していない。 |
| README：schedulerのrequest消滅を確認済み | **partial** | rawの `qstat-after-review.txt:7` は **Post-running**。07:39の不在は親HANDOFFに記録されるが、指定raw内に消滅確認の一次出力はない。この一文の独立追跡性が不足する。 |
| policy・pin・fixture保持 | **closed（静的）** | policy変更はnodes 1→5のみ。literal SHA一致、protocol対象不変。4 sibling、nodefile、qsub引数が整合し、単一node契約・既存負例も保持。 |

実反例はrawで確認できました。同じbnode082でcandidate保持PID3123610に対しdefault挑戦PID3123612が取得成功し、逆方向もPID3123616／3123618で取得成功しています。候補撤回はこの排他喪失を最終成果物から除いています。

READMEの会計6秒とStarted→Endedの2秒は別fieldとして正しく区別されています。同nodeのPID3123598／3123600のdevice/inode一致も確認しました。node間の同じinode数値を共有の証拠とせず、独立予約・全bencher排他・性能改善へ一般化していません。

保存監査では、**正規化9ファイルすべて**について復元byte数・SHA・原文一致を確認。probe原文2本は記載SHAと一致する非実行 `.md`、環境・結果JSONと会計もrawと一致しました。差分は3codefile、phase記録、証跡資料に限定され、新gate/framework・他launcher・凍結artifactへの変更はありません。

`442 passed / 1 skipped、65.90秒` は `focus1.log` と一致し、skipは既存growth holdです。既往のnode秒+16%も掲載会計値から16.23%と再計算できますが、過去attemptの一次資料までの再監査は今回行っていません。

## 総括

候補撤回とnodes=5閉包の静的確認はGOです。request消滅の記述は、一次出力を添えるか親観測として明示すると追跡可能になります。最終file単独走・変異・受入は緑としません。本レビューでは書込み・pytest・性能実行を行っていません。