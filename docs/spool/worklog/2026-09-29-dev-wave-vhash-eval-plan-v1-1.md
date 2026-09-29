---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-eval-plan-v1
seq: 1
title: [T-2893] VHash の評価計画の草稿を v1 に改め、md_21 (前進先の方策) と md_23 (hot 配置) の結果の読み方と確認段の述語を、それらの結果が main に着地する前に書いた。発効はしない (docs のみ、VHash 並行 wave md_25、branch worktree-dev-wave-vhash-eval-plan-v1)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_25.txt` (+ `common.txt`)。成果物は `docs/vhash-evaluation-preregistration-draft.md` の同じ path での改訂 (草稿 §0 の更新契約) と `docs/README.md` の地図の 1 行。設計判断は {{D:vhash-eval-plan-v1}}。
- **着地前に書いたことの証跡:** 着手時 (22:1x JST) と段 4 の前 (22:48 JST) に、local main `8fe87f852` の `output/insights/2026-09-29/` に md_19・md_20・md_21・md_23 の一次資料の dir が無いことを確かめた。codex 子の prompt でもそれらの path を読まないよう指示した。草稿 §14 に記録。
- 段 2 plan 1 本・段 3 相談 2 本 (A: 正しさ・統計、B: 実効性・過剰。どちらも NO-GO、must-fix 計 13 件) を段 4 で裁定し、B の 1 件 (確認段に R0 が無い) だけ refuted (R の 3 cell は R0 を含む)、他は real として反映した。段 2 プランの「H4 方策を bytes で判定」は不採用。
- 段 6 レビュー 2 本 (① 正しさ・統計、② 過剰・実効性。どちらも NO-GO、must-fix 計 10 件、うち「対が作れないときの規則が少ないほど良い指標で逆向き」は 2 本が独立に指摘) をすべて real と裁定して直した。段 4 裁定に書いた S3 の走行数 (308、段 2 プランの行列) は草稿の行列と食い違っていたので、段 6 の裁定で草稿の行列 (H6 の GC 4 点) に改めた。
- 焦点再レビュー 3 巡 (DW-O16 の上限): 1 巡目は元の must-fix 9 件 (重複除く) のうち 8 closed・1 partial と新規 must-fix 3、2 巡目は新規 must-fix 2、3 巡目は新規 must-fix 3 で、
  どれも修正が持ち込んだ p* の分岐まわりの 1 文単位の食い違いだった。3 巡目の 3 件は 4 巡目を回さず親が直し、「108・96・532・448・該当なし」の全出現を照合して閉じた。派生値 (走行数・node 時間) は 2・3 巡目とも子の再計算と一致。
- codex 子は計 8 本 (plan 1・consult 2・review 2・focus 3、すべて gpt-6-sol・medium、read-only)。実装子は無し。
- 変異 matrix は実装面の差分ゼロのため免除 (DW-S04)。
- 起動: EnterWorktree の name 形が「Could not read the repository git config to neutralize filter drivers」で失敗し、記憶どおり `git worktree add --no-checkout` + lock + `reset --hard` (1 回目で rc=0、約 16 分) → path 形で入った。

## 次の一手差分

### 更新

- [T-2893] **P2・草稿 v1 (未発効)**: VHash 論文の評価計画 (`docs/vhash-evaluation-preregistration-draft.md`、草稿 v1) を発効させる。
  v1 は md_21・md_23 の結果の読み方 (§5.5) を着地前に書き、確認段の族を m = 19 にした ({{D:vhash-eval-plan-v1}})。発効の前提は草稿 §11 の P1′〜P10:
  A の最良設定の正しさの門 (md_20)、throughput の D145 の意味の floor (Cicada は D1373 の関門で未取得、取れなければ発効の wave が §8.3 の 2 案をユーザーに諮る)、
  他の指標の揺れ (S0)、構成 B・C_p・E_hb(p*)・E_sp(p*) の inert patch と門、新しい経路の壊した variant、性能用 build での ro 指定率の制御と L-snap の生成器、
  A と C に同じ計器 (H2a)、md_19 の修正、pin、探索結果への §5.5 の適用。揃ってから 1 タスクの job 合計ごとに実測単価で node 時間を計算し直し、
  2 node 時間以上のタスクはユーザーの確認を得て、日付付きの決定で発効させる。発効までは本計画の計測・計算投入をしない。設計の根拠は D2286 と {{D:vhash-eval-plan-v1}}。
  base: e1ca1a7ba60d62ba92dc3805f667162d597fc31826718fd8b2458636256dc0eb

### 新規

- {{T:vhash-eval-read-explore}} **P2・新規**: md_21 (`vhash-forwarding-target-policy`) と md_23 (`vhash-hot-block-cicada`) の一次資料が着地したら、評価計画の草稿 v1 §5.5 の規則をそのまま当てて、方策・K・cell ごとの予備的な判定語と、確認段へ持ち込む p*・K* を決める (草稿 §11 の P10)。規則を変えたくなったら草稿 §0 の「結果を見た後の変更」として扱い、変更前の規則による読みも併記する。md_20 が未着地なら A を対照にした比較は判定不能 (比較相手未検証) とする。docs のみ、計測なし。
- {{T:vhash-cicada-floor}} **P3・新規**: Cicada の throughput の between-run floor (D145 の意味、時間窓 cluster を複数持ち動作点署名ごと) を得る道を決める。既存の floor 生成は D1373 の関門で Cicada を拒否する (trace hook の証拠が patch にしか無い、D2291)。評価計画の草稿 v1 §8.3・§11 の P2 の前提で、取れなければ発効の wave が「D19 の下限 0.030 だけで δ_T = ln 1.03 とする」か「取れるまで発効しない」かをユーザーに諮る。
