---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t2049-b4-report-generator
seq: 1
title: [T-2049] B-4 の材料レポート生成器と正規コマンドを実装した — 分析は floor 未発効に起因する protocol_violation にしかならないと自ら宣言する (コード + テスト + insight、branch worktree-dev-wave-t2049-b4-report-generator、変異 KILLED 20 / SURVIVED 7 / MISMATCH 0・27 件すべて期待一致)
---

## 本文

- 一次資料は `output/insights/2026-09-01_t2049-b4-material-report/`。段 1〜6 の逐語と、
  変異 3 巡の spec / report を置いた。
- `p3_b4_analysis_path.py` の docstring が scope 外と宣言する 5 語のうち、
  **report generator と sanctioned command の 2 語**を埋めた。producer と durable writer は
  2026-08-29 の wave が埋めている。**残るのは certified-selection connection の 1 語だけである。**
- **親の provisional 裁定が 1 件、実測で覆った。** 段 1 brief は `floor` を CLI 必須引数にする案を
  provisional 裁定にしていたが、段 3 の敵対相談 2 レーンが独立に自己矛盾を指摘した。
  brief 自身が「判断値を caller から受け取らない」と書いており、事前登録も floor の出所を
  §5 の凍結 artifact に限定している。親は裁定を撤回し、floor を渡さない形にした
  ({{D:b4-material-report-evidence-only}})。
- **親の一般化も 1 件狭めた。** 段 1 の「46 passed = producer から分析判定までの経路が生きている」は
  広すぎた。fixture は 1 block の real seed と 200 block の複製で、evaluator には test caller が
  `floor=0` を注入している。正規経路の `floor=None` とは別物である。
- 段 6 の敵対レビュー 2 レーンが独立に一致した最重要欠陥は、**共有 fixture が producer の
  再導出を通らず、正常経路を通る test node が 0 件だった**ことである。19 件の緑は拒否経路だけを
  見ていた ({{F:fixture-path-patch-rederivation}})。
- 完全射影の検査が**自己 oracle で恒真**だったことも独立に指摘された
  ({{F:self-oracle-completeness-check}})。期待側と観測側が同じ導出関数を使っており、
  外部入力では発火しなかった。登録変異の 1 件も候補集合に含意されて恒真だった。
- 出力先 guard が **campaign root を `runs/` と誤認**していた。WAL は
  `<campaign-root>/runs/wal.jsonl` にあるため、`<campaign-root>/任意の名前` が
  三方向検査を素通りしていた。親が `layout.py:203-208` で独立に確認した
  ({{D:b4-material-report-output-disjointness}})。
- **変異走が 2 回、変異の内容とは無関係な理由で停止した。**
  1 回目は kill が共有 fixture の setup で起き `FAILED ` 行として現れなかったため
  ({{F:setup-phase-kill-evades-node-extraction}})、2 回目は並列実行の group 名が
  失敗行の nodeid にだけ付き collection 側に付かないためである。前者は fixture の責務を分けて、
  後者は runner を直列化して解消した。**変異の内容は 2 回とも変えていない。**
- **SURVIVED 7 件は穴ではなく冗長である。**ただし**親が最初に書いた因果の説明は誤っており、
  段 6 の焦点再レビューが指摘して訂正した。**親は「隣接層に mask されている」と仮説を立てて
  両層同時変異 4 件を事前登録し、うち 2 件が検出されたことを「仮説の実証」と書いた。
  実際にはその 2 件の赤は配下方向の gate を外したことが一次原因で、一致方向と字面比較の
  変異は落ちていない。**両層変異は mask 仮説を実証していない。**
  結論 (単独 gate の証拠から外す) 自体は静的根拠で支持される — 完全射影の oracle は
  重なり合う 5 つの不変条件を持つ過剰決定の検査であり、出力先 guard の一致・配下・祖先も
  互いを包含する。`DW-M03` に従い冗長 gate と明記した。訂正の詳細は insight に残した。
- 子は codex-cli 0.151.0 の `gpt-5.6-sol` / xhigh を plan 1、consult 2、author 1、review 2、
  fix 2、focus 1 の計 9 本。全件 `accepted`。
- 実装子と fix 子は 3 回とも `qstat` の一過性障害 (`rc=16`) でテストを実走できなかった。
  実測はすべて親が行った。**子の未実走を緑と記録していない。**
- 正式 B-4 実走、qsub、性能測定、build は行っていない。

## 次の一手差分

### 完了

- [T-2049] B-4 の raw 試行記録を書く権威 producer は 2026-08-29 に着地済みで、本 wave が
  report generator と sanctioned command を埋めた。5 語のうち残るのは
  certified-selection connection だけであり、下記の新規項目へ引き継ぐ。
  remaining: none
  base: 22c8d28951ce2ab7a2ab36cbd59276924c87c85c7a5577be8b4faa2adb59cd13

### 新規

- {{T:b4-certified-selection-connection}} **P1・新規**: B-4 の材料レポートと certified 選択を
  つなぐ接続を実装する。`p3_b4_analysis_path.py` の docstring が scope 外と宣言する 5 語のうち
  最後の 1 語である。
- {{T:b4-floor-artifact-activation}} **P1・新規**: B-4 事前登録 §5 の `floor` 欄を発効させる
  手続きを人間の手番で決める。発効するまで材料レポートの分析 verdict は
  `protocol_violation` にしかならず、§7.1 の 4 分類は実効化できない。
- {{T:b4-durable-rejection-ledger}} **P2・新規**: raw 試行記録 producer の rejection を耐久化する。
  現状 publication root だけを入力とする consumer は過去の rejection を完全には復元できず、
  file-drawer を機械的に閉じきれない。
