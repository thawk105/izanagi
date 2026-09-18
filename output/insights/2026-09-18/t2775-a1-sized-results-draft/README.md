# A-1 sized attempt-0001 の results 稿と図9

これは既存測定の執筆材料と図を作る開発記録である。新しい性能測定、formal化、A-1要件充足の判定は行わない。
`formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only` を維持する。

## 成果物と一次資料

- 結果稿: `docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`。
- 図9: `docs/paper-story/figures/fig9_a1_balanced5_sized_attempt1.{png,pdf,provenance.json}`。
- 入力: `output/insights/2026-09-13/paper-story-a1-balanced5-sized/` の公開leafとpolicy v3。
- 値の出所・測定条件・限界は稿に、図のcaption・着地hashはfigures READMEのfig9節に記録する。
  稿をcaption_sourceとするので、図provenance hashを稿へ逆流させない。

## 回収と裁定

旧waveは未commitの稿・README・生成器・testを残し、独立焦点レビューがclosed10/partial1に加えて
F-MF1を検出していた。旧worklog下書きの「全closed」「閉じた」は実績でなく先書きだったため採用しない。
旧差分はrepo外job directoryのpatchとarchiveに保全し、指定impl tip `1c991c0cc`の3 commitを
着手時local main `b2037abfa`を第一親とするmergeで回収した。

旧親は生存していた。ユーザーの明示許可後、照合済PIDへのSIGTERM後に同一sessionが再出現したため、
Claudeの正規stopでsession `6f80faa7`を停止し、state=stoppedを確認した。

- F-MF1: 全欠落時のskipで着地closure全体が迂回された。隔離Codex authorがskipを除去し、
  実際の着地testを呼ぶ全欠落1ケース・部分欠落6集合を追加した。生成器と入力受理集合は不変。
- A-S1: READMEの系列規則にも、数値と転記元hashをresult.jsonから得る本稿の個別扱いを追記した。
- 独立焦点再レビュー: 既存11件closed、F-MF1は実装済み・実走待ち。全180標本・90対差・6armの値を
  独立に再計算し、稿・図・caption・hashの不一致はなかった。参照先未存在R-M1は本READMEで処置した。
- 追加gate・汎用化・次wave・自己改善実装は行わない。

## 元記録との相違

T-1505の記録insight §4は、balancedとread-heavyのverify commits数を入れ替えている。
WALとjob stdoutの値は、balancedがfixed5 466561 / no-backoff 483318、
read-heavyがfixed2 516607 / no-backoff 515988である。旧凍結記録は変更せず、稿§2.4へ正値と相違を記載した。
旧親の標本表の手打ち誤りは現物からの機械生成へ置換済みで、F1再発fragmentに経緯を保持する。

## 検証記録

稿の権威bytes・数値照合を回収前後に再実行し、ともにPROBLEMS 0。最終図生成rc=0、3成果物を生成し、
READMEの4 hash欄を実値化した。check_codex_agentsとcheck_docsはrc=0。
図9単独テストは正規run_tests経路の6379.nqsvで28 passed / skip 0 (pytest 7.47秒、job Elapse 13秒)。
最終bundle正例と全欠落・部分欠落負例を含む。変異・最終受入はこの記録時点で未完了であり、終端実績を追記してからlandする。
関連consumer・列挙設定の4 test fileは111 passed (110.50秒)。受入全走の代用ではない。
レビュー・裁定・検算の逐語は `verbatim/` に保全する。

逐語3 fileの末尾ASCII空白だけをgit diff検査のため可逆正規化した。原文SHA-256・byte数・行番号・除去suffixは
`verbatim/whitespace-normalization.json`にあり、各行のLF前へsuffixを戻して原文を復元できる。可視文字は変更していない。
