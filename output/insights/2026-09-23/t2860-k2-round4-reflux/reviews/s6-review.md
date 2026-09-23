以下、`I` = `output/insights/2026-09-23/t2860-k2-round4-reflux`、`R` = `docs/paper-story/results/2026-09-23-k2-manual-loop-four-rounds.md`、`J` = 指定の job root。

## must-fix

- **real — critic のWAL読取範囲を過大に記録している。**
  **箇所:** `I/README.md:62`、`R:115`。
  transcript の実行済みコマンドは `jq -c '.' … | cut -c1-1800`。10 record を表示対象にしたが、候補・stockそれぞれの `build_start` / `build_done`、計4 record は途中で切れている。先行する Python 読取りは hook に拒否されている。「全10行を読んだ」は「10 record の先頭最大1,800文字を表示、4 record は末尾未表示」へ限定する必要がある。根拠は `J/critic-4-transcript.jsonl:17`・`:20`。
  **成果物影響:** critic が確認した証拠範囲を過大評価する。verify・bench・commit の数値照合には影響しない。

## should

- **real — critic の時刻を「07:5x／保存なし」とする記述が不正確。**
  **箇所:** `R:146`、`R:165`。
  transcript の初回依頼は **2026-09-23 07:49:53.481 JST**、最終応答は **07:53:19.164 JST**。差は **205.683秒**で「約206秒」と一致する。プロセス起動時刻そのものと区別し、この保存済み時刻を記載できる。根拠は `J/critic-4-transcript.jsonl:1`・`:45`。
  **成果物影響:** 時系列表の時刻と、一次資料の欠落範囲が誤っている。

## nit

- **real — 「bytes のまま抽出」は末尾改行の追加を省略している。**
  **箇所:** `I/README.md:54`、`R:114`、`docs/spool/worklog/2026-09-23-dev-wave-t2860-k2-round4-reflux-1.md:15`。
  `SubagentHandback.message` のUTF-8表現は **11,114 B／sha256 `25745b5f…`**。保存物は末尾LFを追加した **11,115 B／`bb9e3277…`**。「本文を抽出し末尾LFを補った」が正確。
  **成果物影響:** 診断内容・保存物の掲載ハッシュ・AO取込みは正しいが、byte同一性の説明だけが過剰。

## 照合した数値 (一致)

`R:58`以降の表について、巡1は `job.stdout`、巡2・3はレポートの events、巡4はWALと照合した。

| 対象 | 一致した主要値 |
|---|---|
| 巡1 | commits / aborts / anomalies = 469,618 / 83,034 / 0、表示median 719,324、CV 1.70% |
| 巡2 | 445,394 / 71,877 / 0、median 687,508.5、反復692,403 / 682,614、CV 1.007%、abort_rate 0.0740 |
| 巡3 | 523,120 / 122,211 / 0、median 815,983、反復815,067 / 816,899、CV 0.159%、abort_rate 0.09065 |
| 巡4候補 | 566,368 / 161,015 / 0、median 884,922.5、反復892,103 / 877,742、CV 1.148%、abort_rate 0.10105 |
| 巡4 stock | 281,132 / 8,715 / 0、median 354,948、反復358,000 / 351,896、CV 1.216%、abort_rate 0.01835 |

- 比は **2.4931046 / 2.3660941**、候補差 **+7.199663%**、stock差 **+1.738405%**。掲載の丸め値と一致。
- trace abort率は巡4 **22.136206% / 3.006759%**、pair **18.879858% / 3.108481%**。巡4のcommit/abortはstock **32.258405**、候補 **3.517486**。
- 入力 **6,436 B**、prompt **7,083 B**、保存診断 **11,115 B**、AO **32,549 B**、最終レポート **65,158 B**。掲載SHA-256と一致。開示14項、AO3件、仮説1件、artifact_refs 7件、source_refs **14 = 10 + 1 + 3**も一致。
- WAL canonical ref **10/10**、AO canonical ref **3/3**を再計算して一致。レポートのevents・AOは写しの実物と一致し、provenanceの絶対pathも記述どおり。
- job ID・host、pairのElapse **100秒**、巡4の **107秒**、Created / Started / Ended、WAL時刻も一致。

次の疑義は **refuted**。

- **原本変更・保護ファイル不一致** — `I/README.md:91`。6 fileは原本・写し・既存byte複製・MANIFESTで一致。保護5 fileの前後ログも一致し、原本 `runs/` はWALだけ。**成果物影響:** 同一性の記述を維持できる。
- **層3の別項目変更・未開示の書込み** — `I/README.md:45`・`:63`。2回のJSON差分は `noise_floor` のみ。Bash8呼出しに書込みはなく、受領証・lock本文の未読も確認。**成果物影響:** これらの限定は妥当。
- **性能一般化・B-6充足への昇格** — `R:24`・`:154`。stock=`BACK_OFF=1`、別job比較禁止、原本消失、写しへの取込み、legacy critic非適格、K2必須経路外の限定がある。**成果物影響:** criticの帰属を本稿の実証へ昇格していない。
- **凍結物変更・fragment不備・禁止成果物の追加** — `docs/paper-story/README.md:95`・`:219`、fragment`:20`。凍結版・3巡稿は差分なし。staleは4項で、項3が評価成立、項4が還流の追加を扱う。fragmentのH2・完了・更新・両base digestは適合。禁止されたcampaignファイルの追加なし。**成果物影響:** 文書構造上の阻害なし。

## 総括

**NO-GO — criticのWAL読取範囲の記述修正が必要。**
主要数値・識別子・AO取込み・原本保全は照合範囲で一致。
書込み・テスト実測は行っていない。