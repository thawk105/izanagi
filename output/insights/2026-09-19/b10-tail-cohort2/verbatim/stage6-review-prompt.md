単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2

必読事項の射影:
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2/docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md — レビュー対象の results 稿 (第 2 cohort、未 commit)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2/output/insights/2026-09-19/b10-tail-cohort2/verbatim/extract-cohort2.md — 集団報告 JSON / DAT / -complete.json / job root から機械的に転記した抽出 (稿の数値の照合元)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2/docs/b10-backoff-static-tail-preregistration.md — 事前登録。§4.5、§4.6、§4.9、§7、末尾の「2026-09-19 追記」を読む。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2/docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md — cohort 1 (主結果) の稿。同型の先例であり、稿が転記している cohort 1 の欄の出所。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2/output/insights/2026-09-19/b10-tail-cohort2/README.md — 本 wave の記録 insight (未 commit)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/78abb492/tmp/wave/readme-row.diff — `docs/paper-story/README.md` の results 系列表へ足した 1 行の diff。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/78abb492/tmp/wave/D2050-verbatim.md — 裁定 D2050 の逐語。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-tail-cohort2/docs/paper-story/README.md — 「results 系列」節の規則 (append-only、1 file = 1 結果、数値の出所は一次資料だけ、protocol status を研究の成否へ拡張しない)。読めなければ即停止。
- 可能なら (読めなければその旨を書き、上の抽出だけで照合する): /work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260919-cohort2/t2500-backoff-static-tail-formal.json、同 dir の `.dat` と `-complete.json`、job root `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/b10-backoff-grid-20260919T131526Z-2235286-write-heavy/` の `completion.json` / `reservation.json` / `qstat-f.stdout`、失敗 attempt の `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/b10-backoff-grid-20260919T131120Z-2159341-write-heavy.failure.json`。

## 役割

あなたは read-only の独立敵対レビュー子である。書込可能な tmp は無いので pytest の実走は要求しない。静的検査でよい。
テストの実測は親が行う。予算が尽きそうなら、途中までの結論を下の出力形式どおりに書いて終われ (無出力が最悪)。

## 状況

ユーザー決定 (2026-09-19): 「第 2 cohort は独立再現。cohort 1 (group b10-backoff-grid-20260915T061814Z-545445、verdict not-observed-in-any-workload) の verdict を主として保持し、cohort 2 の verdict は再現欄に併記する。合成はしない」。親はこの地位を事前登録の末尾追記として commit `8737cacb4` に固定してから第 2 cohort を投入し、完走・集団判定 (`not-observed-in-any-workload`) を得て、results 稿を書いた。これは一次資料から事実を再抽出する docs-only の稿なので、独立レビュー 1 本を必須とする。

## 攻撃レンズ

1. **数値・識別子の転記誤り。** 稿の表 (§1.1、§1.3、§2.1〜§2.5、§2.6、§4.1) の値を抽出と突き合わせよ。SHA-256、job id、campaign id、ホスト、所要、開始時刻 (JST 換算)、平均、変動係数、区間推定、生標本。cohort 1 の欄 (§2.6) は cohort 1 の稿 §1.1・§2.1・§4.1 と突き合わせよ。
2. **言い方の固定 (事前登録 §4.5、2026-09-19 追記の項 7)。** 「飽和しない」「飽和点が存在しない」「再現されたので飽和しない」に相当する表現、あるいは 2 cohort の一致を強さの根拠にする表現が 1 箇所でも紛れていないか。README 行と insight も対象。
3. **合成の禁止 (追記の項 3)。** 統合 verdict・プール推定・またぐ有意水準・「再現精度」評価に読める文が無いか。§2.6 の表と本文の言い分けが十分か。
4. **cohort 1 の稿・図を改めていないか。** 稿・README 行・insight が cohort 1 について新しい主張をしていないか。ただし insight §5 は cohort 1 稿の限定 5 が不完全 (reservation.json に commit がある) と書く — これは「新しい事実の記録」であって稿の改変ではないか、それとも越権か。判定せよ。
5. **限定の抜け。** cohort 1 稿の限定 15 件に対し本稿は 16 件。落ちた限定・弱まった限定・新たに要る限定 (例: 失敗 attempt、別 blob 束縛、T-548 による job body の差、探索走 campaign の固定) を挙げよ。
6. **results 系列の規則違反。** append-only、1 file = 1 結果、数値の出所は一次資料だけ (cohort 1 稿からの転記は §4.2 に明記されているか)、protocol status を研究の成否へ拡張していないか、placeholder・値なし前方参照・自己 hash が無いか (F36: 稿自身の SHA-256 を稿に書いていないか、insight の SHA-256 を書かない理由が妥当か)。
7. **過剰・削除。** 稿・insight・README 行に、依頼 (独立再現の投入と結果稿、fig8 再現欄の材料) を越える主張・提案・一般化が無いか。あれば削るべきか裁定パッケージへ送るべきかを分けよ。

## 出力形式 (この順・この見出しで)

### 所見
番号付き。各所見に must-fix / should / nit の格付け、根拠 (file と節名または行)、放置時に成果物 (稿・README・insight・fig8 の材料) がどう変わるかを 1 行。

### 修正案
must-fix と should について、該当箇所への具体的な置換文 (前後がわかる引用で)。

### 照合した範囲
何を何と突き合わせたか (表ごとに件数)。読めなかった資料があれば列挙。

## 総括
3〜6 行。commit してよいか (yes / yes-with-fixes / no) を最初の行に書く。
