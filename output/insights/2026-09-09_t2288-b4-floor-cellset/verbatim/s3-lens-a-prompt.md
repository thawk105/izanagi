単独段 dispatch: stage=consult; lane=sol; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib

## 必読事項の射影

次を読め。読めなければ即停止し、その旨だけを報告せよ。

- `/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/brief.md` — 親の段 1 brief v2 (逐語)。
- `/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/s2b-plan.md` — 段 2 の plan (逐語)。
- `/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/verbatim-rulings.md` — D1641 全文と事前登録 §5 floor 欄・§5.1 floor 解除条件の逐語。
- `/home/SFC/tanab/.claude/jobs/9ece0216/tmp/t2288/handoff.md` — 親が実測した現在地の表。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/floor_pair_driver.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/calibration_verify.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/orchestrator/campaign/p3_b4_floor_artifact_issuer.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2288-b4-floor-cell-calib/output/env/pegasus/b10-backoff-shape/24d80d9a35122de1/reports/final/b10_backoff_shape_provenance.json`

repo の path は上記 worktree のものだけを使う。親 checkout の path を使ってはならない。
`docs/decisions.md` の D15 / D19 / D1060 / D1377 / D1530 / D1641 / D1696 / D1759 は同 worktree の
`docs/decisions.md` を `grep -n "^## D1759\."` の形で索引して該当節だけ読め。
絶対規律は同 worktree の `CLAUDE.md` を読め (とくに規律 2 と規律 4)。

## 段の宣言

これは段 3 (敵対相談) のレンズ A である。sandbox は read-only で、書込可能な tmp は無い。
**pytest を実走して緑にすることは求めない。静的検査と読解だけでよい。** 実測は親が段 6 で行う。
実走していない検査を「通した」と書いてはならない。
コードを編集してはならない。commit してはならない。plan を守る立場に立ってはならない。

予算が尽きそうなら、その時点の途中結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

出力に結合文字 U+0300〜U+036F を使うな。

## あなたのレンズ — 正しさ境界。受理集合を広げる判断そのものを攻撃せよ

**plan と親 brief の両方が検査対象である。**

段 2 の plan は 3 案のうち **(γ): calibration と cell の workload 一致要求だけを外す** を選び、
`SPEC_SCHEMA` を v4 へ上げる形にした。これは**受理集合を広げる変更**である。
あなたの仕事は、この広げ方が正しさの観点で許されるかを敵対的に判定することである。

1. **(γ) の正当化が成り立つか。** plan の論拠は「calibration が保証するのは
   この環境・threads で working set / L3 下限を満たす record 数であり、read/write 混合の同一性ではない」
   である。次を一次資料で確かめ、論拠が成り立つか判定せよ。
   - calibration artifact の `saturation` (`saturated`、`lower_bound_selected`、`working_set_ratio`、
     `notes`、`series`) が実際に何を根拠に `records` を選んだか。
   - その根拠量 (maxrss / working set) が **workload 混合に依存するか**。
     依存するなら (γ) は誤りである。依存しないなら (γ) は成り立つ。
   - `noise_floor` (`kind: "within-run"`、`cv`) は workload 依存か。
     driver が測る量は **between-run floor** であり、calibration の within-run noise floor とは
     別の量である (D1639)。この区別が (γ) の判断に影響するかを述べよ。
   - 絶対規律 4 (レコード数は小さすぎると many-core の cache 競合が再現されず測定が楽観的に歪む) に
     照らして、balanced で選んだ records を read-heavy / write-heavy の cell に使うことが
     規律 4 に反しないか。
2. **より狭い案が存在するか。** (γ) は「calibration の workload と cell の workload が
   まったく無関係でも受理する」形である。次の中間案が成り立つか、成り立つならなぜ plan が
   それを採らなかったのが誤りなのかを述べよ。
   - (γ') `calibration.workload` が **cell workload 集合のいずれかと一致すること**を要求する
     (b10 の先例は balanced calibration + balanced cell を含むのでこれを満たす)。
   - (γ'') calibration の workload と cell の workload のうち、**records に効く key だけ**
     (例えば `ycsb_zipf_skew` は working set に効かないが `ycsb_rratio` も効かない、など) の
     一致を要求する。どの key が working set に効くかを CCBench 側の実装まで辿って判定せよ。
   **中間案が実在するなら、最も狭い案を採らないことは受理集合の不必要な拡大である。**
3. **受理集合が意図より広がる経路。** plan が書いた拡張集合の記述が実際の拡張と一致するか。
   plan が見落とした拡張を具体的に構成せよ。とくに
   - `records` 一致だけが残ることで、`threads` は一致するが workload が別で
     **records も偶然一致する** calibration を使い回せる形。
   - 単一 cell の spec で、その cell の workload が calibration と無関係になる形。
   - 2 時間窓・2 campaign の間で calibration を差し替える形が塞がっているか。
4. **fail-closed が fail-open になる経路。** plan の binder に例外の飲み込み、部分失敗の非 sticky 化、
   到達不能になる拒否がないか。plan が「行数を動かさないよう 2 行の説明へ置換する」と言っている点が、
   拒否を落としたまま形だけ残す型 (D1374 の「検査していないことを検査したと読ませる」) に
   なっていないかを見よ。
5. **既裁定との不整合。** D1641 (校正済み `PerfConfig` は calibrator の出力を採る)、
   D1060 (既存値を根拠にしない)、D1377、D1696、D1530、事前登録 §5.1 の floor と
   校正済み `PerfConfig` の解除条件。**緩めている項目があれば名指しせよ。**
   とくに「§5 の校正済み `PerfConfig` 欄が単数だから 1 calibration でよい」という plan の推論が、
   §5.1 の同欄の解除条件 (calibrator が決めた値へ差し替えるまで記入しない) と整合するかを見よ。
6. **規律 2 の向き。** この変更は「到達可能性のために検査を緩める」向きである。
   規律 2 は「性能や利便性のために正しさゲートを緩めない」と定める。
   **この緩めが規律 2 違反にあたるか、あたらないならその境界を 2 文で示せ。**
   禁止は署名で書き、通る正例を 1 つ添えよ。
7. **親の実測値とその一般化。** 親は次を実測と称している。各々が主張を支えるか検証せよ。
   - 「b10 は 3 workload すべてに同一 calibration を束縛し、束縛 field に workload を含まない」
     (根拠: provenance JSON の `calibration` object の key 集合)。**provenance が記録していないことは
     「束縛していない」ことを意味するか。** b10 の実際の admission 経路まで辿って判定せよ。
   - 「accepted calibration は rr50 / t48 の 2 件だけ」(根拠: tracked な `calibration/v2` 27 file の列挙)。
   - 「配線は済んでおり、§5 が `未記入` のときだけ fail-closed で None」
     (根拠: issuer 1216-1250 の resolver)。

## 禁止

- plan を弁護してはならない。同意する場合も同意の根拠 file:line を自分で挙げよ。
- 一般化した framework・汎用 gate の新設を提案してはならない。
- 事前登録 §5 を埋める案、事前登録本文を書き換える案を出してはならない。
- 権威 floor の発行そのもの、calibrator の実行、Pegasus への測定投入を提案してはならない。
- 仮想リスク向けの新しい gate・検査・台帳を足す提案をしてはならない。実在する構成可能な穴だけを挙げよ。

## 出力形式

以下の H2 見出しをこの順で使え。各所見には `real 候補` / `refuted 候補` の自己判定と、
根拠の file:line、そして「放置すると成果物 (certified 選択・レポート・台帳) の値・受理集合・参照が
どう変わるか」を 1 行で付けよ。

## (γ) の正当化の判定
## より狭い案の有無
## 受理集合が意図より広がる経路
## fail-open 経路
## 既裁定との不整合
## 規律 2 の境界
## 親の実測値の検証
## 総括
