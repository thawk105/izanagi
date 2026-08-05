---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t139-alt-x-probe
seq: 1
title: [T-139] 代替 X の生死確認が両 workload で成立した — 4 stripe・cache line 分離・固定回数 stripe 計算、ただし J=1 の engineering screen (コード + docs、branch worktree-dev-wave-t139-alt-x-probe、probe = Pegasus gen_S request 892042、変異 matrix = 対象外)
---

## 本文

- **着手条件は既に成立していた (F35 の照合)。** worklog の [T-139] 項は (134) 以来 pointer で
  持ち越され「[T-338] の Q1〜Q5 の裁定の後」と書かれていたが、**[T-338] は (142) で Q1〜Q11 が
  全件裁定完了**しており、項が stale だった。段 1 の前提実測でこれを検出して繰り上げた。
- **段 1 の前提実測で blocker を 1 件発見した。** probe が依存する gflags / glog の実体
  (`/home/SFC/tanab/github/`) がディレクトリごと消えており、`verify-deps` が rc=1 だった。
  これは probe だけでなく rung1 系の再現全体に掛かる。共有 policy のパスは書き換えられない
  (凍結済み証拠がその sha256 を pin していることを親が実測確認した) ため、pin 固定・clean で
  `/work` 配下へ復旧し、probe 側の env seam で供給した。**一般経路は未復旧のままである。**
- **親 brief の欠陥を 3 件認めた。** (a) stripe 混合要件「先頭・末尾・長さ」は不十分で、
  共通 prefix + suffix・同一長の key 族では 100% 退化することを親が実測した (中央窓が必須)。
  (b) stripe 数 2 の理由「stock に近づきすぎる」は定量的に支持されない。(c) 権威境界の参照が
  D126 のままで D162 を引いていなかった。逐語と訂正は
  `output/insights/2026-08-05_t139-alt-x-probe/README.md` §5。
- **敵対検証が投入前に blocker を 19 件止めた。** 段 3 が 10 件、段 6 (レビュー 2 本 + 焦点再レビュー
  2 巡) が 9 件。うち 1 件は「`compile_commands.json` の該当 entry が 4 件あるため exact-one 要求が
  最初の arm で停止し、job が何も生成せずに終わる」型で、1 時間の allocation を丸ごと失うところだった。
  ほかに、queue 待ち中に HEAD が進むと別 bytes を実行しうる点、事前登録 path の恒真拒否、
  内部 timeout の直列総和が予算超過 (3817 > 3300 秒)、不変 snapshot を書込み不能のまま
  consumer へ渡す点などを投入前に閉じた。
- **fix は 3 巡 + 実走由来 1 巡。** 4 巡目は計算ノードでの実走が見つけた `set -u` の実行時停止で、
  レビュー所見の積み増しではない ({{F:local-single-statement-dependency}})。
- **投入は 3 submission を要し、全 ID を結果閲覧前から台帳化した。** `892032` は shell の
  実行時バグで 5 秒停止、`892039` は前 job の scheduler 出力が repo root に残り clean-tree 検査が
  正しく発火して 6 秒停止 ({{F:probe-clean-tree-scheduler-droppings}})、`892042` が本結果である。
  **いずれも性能値を 1 つも見ないまま判断した。**
- **実装と事前登録を実走前に commit した。** job は投入時に渡した期待 commit と job 開始時の
  HEAD の exact 一致を要求し、その commit の blob だけを展開する。
- **子の非実走を緑と数えていない。** 実装子と fix 子は PBS を実走できず、親も機械防壁により
  ログインノードで probe を実行できないため、build・compile receipt・liveness・性能の緑は
  すべて計算ノードの実走 (`892042`) が唯一の根拠である。親の `bash -n` は guard_bash が拒否したので
  迂回せず、構文の証拠は子の sandbox 内実走と実走そのものに委ねた。
- **変異 matrix は対象外**である。izanagi の gate・schema・pytest を 1 つも新設せず受理集合を
  変えないため。代わりに `DW-S04` の「通る正例を 1 つ添える」を probe 内の self-check fixture
  (verdict / row 構造 / liveness / compile argv の各拒否に正例と負例) で満たした。
- 段 8 の自己改善候補は {{F:probe-clean-tree-scheduler-droppings}} と F132 再発として routing した。

## 次の一手差分

### 更新

- [T-139] **P1・生死確認は成立 → RF 統計設計に準拠した本走の設計へ**: 代替 X (4 stripe・
  `alignas(64)` の cache line 分離・先頭/中央/末尾窓 + 長さ + storage の固定回数 mixer) が
  **両 workload で全標本分離を達成**した (W1 2.01x / 回復率 13.5%、W2 2.33x / 回復率 14.4%、
  request `892042`)。前候補は W2 で 0.85x と逆転していた。**ただしこれは J=1・未較正の
  engineering screen であり、正例 artifact ではない** — 適格性の権威は独立 validator だけが持ち
  (D162)、validator と consumer は未実装 (0/9) である。次は [T-338] が裁定した RF 統計設計
  (推定量 / 最小識別幅 / 同時信頼領域 / 独立単位 / 二段階設計) に準拠した本走の事前登録を書くこと。
  機序の帰属は本 study では不可能 (3 変更を同時に入れた) なので ablation は別 study。
  正本 = `output/insights/2026-08-05_t139-alt-x-probe/README.md`、
  設計判断 = {{D:t139-alt-x-partial-recovery}}
  base: cc1de274413537993b167632b1b51498e2469b3bbe7d20d08ae4ba02bed138e4

### 新規

- {{T:pegasus-dependency-general-procurement}} **P2・新規**: gflags / glog の一般調達を復旧する。
  `/home/SFC/tanab/github/` の消失で `fetch_third_party.py verify-deps` と rung1 系の再現経路は
  **rc=1 のままである**。本 wave が直したのは probe 経路だけ。択一 = (a) 共有 policy の locator を
  正式に rebind する (凍結証拠の再 binding を伴う)、(b) versioned な共通調達経路を新設する、
  (c) 現状維持で probe ごとに env seam を持つ
- {{T:probe-exclusivity-witness}} **P3・新規**: Pegasus の全 probe で共通の単独性 witness
  (process / cgroup / PSI) を設けるか裁定する。現行の `load1` + `pgrep` は限定 screen にすぎず、
  本 wave も「単独性の成立」を主張していない
- {{T:disposable-probe-scale-cap}} **P2・新規**: 使い捨て probe の規模上限を族として制度化するか
  裁定する。F132 と本 wave で**独立 2 例**が揃った (`DW-G03` の条件成立)。あわせて D184
  (使い捨て probe の生死主張を最小 pytest node で裏取りする) も、本 wave が 2 例目にあたるため
  族への制度化を判断できる。本 wave は self-check fixture で代替し pytest node を作っていない
- {{T:t139-mechanism-ablation}} **P3・新規**: 代替 X の回復がどの変更に由来するかを分離する
  ablation を事前登録する。本 wave は cache line 分離・stripe 計算の固定回数化・stripe 数 4 の
  3 つを同時に変えたため、機序の帰属ができない
