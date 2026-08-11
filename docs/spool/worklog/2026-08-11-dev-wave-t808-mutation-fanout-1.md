---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t808-mutation-fanout
seq: 1
title: T-808 変異本走の N-job fan-out を実装した — 敵対 4 本が queue 待ちの TIMEOUT 化と pairwise path 検査の誤りを摘出、変異 6/6 が期待一致 (被覆の穴 3 件を実証、コード + docs、branch worktree-dev-wave-t808-mutation-fanout)
---

## 本文

- **[T-808] を実装した。**D289 決定 (3) の 5 設計点をすべて解いた。設計判断は
  {{D:mutation-fanout-contract}}、逐語と変異台帳は
  `output/insights/2026-08-11_t808-mutation-fanout/`。
- **独立 2 系統が全 18 欄で一致した。** 親が独立導出した併合欄分類 (`merge-field-table.md`) と
  段 2 codex プランが、`executable_path` を MATCH とする訂正まで含めて独立に同じ結論へ達した。
  親の初稿は `executable_path` を DIFFER 側に置いており、`shutil.which` 解決を見落としていた。
- **段 3 の敵対 2 本が、両系統が揃って誤っていた点を摘出した。**
  「path は shard 間で pairwise に異ならねばならない」は誤りで、同一 scratch root を**逐次**
  再利用すれば一致しうる。DIFFER 必須にすると内容上正しい shard を誤拒否する。
  **独立導出 2 系統が同じ誤りをしており、敵対レビューでしか出なかった。**
- **最重要の発見は queue 待ちの `TIMEOUT` 化である** ({{D:mutation-fanout-contract}} 決定 3)。
  変異の timeout は dispatch subprocess 全体に掛かるため、`QUE` のまま超過した変異が
  **一度も走っていないのに terminal として記録され、`registered == recorded` が成立する。**
  本 wave が守ろうとしていた不変条件そのものが、走っていない変異で満たされうる経路だった。
  **fan-out が作った欠陥ではなく現行の逐次経路に既にある。**根治は
  {{T:mutation-timeout-semantics}} へ回し、fan-out 側は併合器が TIMEOUT record を拒否して閉じた。
- **親の実測 2 件を wave 中に撤回した。** (i) shard あたり RSS 372 MiB を N 倍する admission は
  判定量が誤り (runbook §7.0 は user slice の `memory.current`)、かつ予備 2 GiB を引くと
  「N=4 は余裕」という結論自体も誤りだった。(ii) `--plan-only` の成功を「fan-out 成立」と
  書いていたが、pytest / qsub / receipt / teardown を通らないので**分離機構の確認**でしかない。
  どちらも段 3 のレンズが指摘し、brief と decision 草案へ訂正ブロックを入れた。
- **fix 1 巡で赤 3 件が消え、焦点 41 件緑・既存 90 件緑。**焦点再レビューは
  closed 2 / partial 7 / regressed 0 を返した。**fix 2 巡目は行わなかった** — 残る partial は
  (a) 同一 user による偽造耐性、(b) legacy 単発経路、(c) 変異帰属 (spec 側で解く) に尽き、
  **scope 内でコードで閉じるべき残件が無い**ためである (`DW-O16`)。
- **偽造耐性は本 wave では閉じないと裁定した。** 敵対レビューは偽 scope を立てて kernel peak を
  合わせる等の具体手順を構成しており real である。ただし信頼境界が operator 自身の account で
  あることと、ユーザー確定裁定「研究最優先・プロトタイプ基準」に従い見送った。
  **代わりに「偶発欠落への fail-closed であって偽造への改竄検知ではない」と明記する義務**を
  {{D:mutation-fanout-contract}} 決定 6 に置いた。実装は {{T:fanout-tamper-evidence}} へ。
- **変異が被覆の穴を 3 件実証した。** M04 / M06 は「生存する」と事前登録して当てた。
  M02 は KILLED を期待して生存し、**私が『shard 間の一致検査』を撃ったつもりで
  実際には『shard 内の自己整合検査』を撃っていた**ことが判明した。初回結果を消さず erratum とし、
  実効 gate へ再照準した M05 は期待どおり KILLED した (`DW-M02`)。
- **待ち手で 1 度誤検知した。** 変異再走の待ち手へ渡した pid が呼び出し元シェルのもので、
  それが先に終了したため「生産者死亡」で返った。**成果物の実在で照合して誤りと判明**し、
  正しい pid で張り直した。走行そのものは正常だった。

## 次の一手差分

### 完了

- [T-808] 変異本走の N-job fan-out を分割器・併合器・driver として実装した。設計 5 点は
  {{D:mutation-fanout-contract}} に確定。変異 6 ベクトルは全件期待一致 (KILLED 3 / SURVIVED 3)。
  remaining: none
  base: d2d0eaf05c2a0fd51306f50e4563387be263d83f7dc8190623a19178c915b918

### 新規

- {{T:mutation-timeout-semantics}} **P1・新規**: 変異 `TIMEOUT` の意味を
  「RUN 開始を receipt で確認した後の計算ノード実行 timeout」に限定し、queue timeout を
  別 status にする。現行は dispatch subprocess 全体に timeout が掛かるため、**一度も走っていない
  変異が terminal として `registered == recorded` を満たす。**逐次経路にも存在する既存欠陥で、
  D130 決定 (3) 条件 4 の `total_deadline` と同族。既存台帳の再解釈が要る。
- {{T:fanout-tamper-evidence}} **P3・新規**: fan-out の merge index へ偽造耐性を入れるか決める。
  同一 Unix user が偽 scope・複写 identity・同一 root 内の親 hash 差し替えで
  正規 index を作れることを敵対レビューが構成した。プロトタイプ基準で本 wave は見送ったが、
  index が proof chain 材料である以上、位置付けの明文化だけで足りるかは別途判断する。
- {{T:fanout-uncovered-gates}} **P3・新規**: 変異が実証した被覆の穴 3 件を埋めるか決める。
  shard 内 collection 自己整合、`nonterminal_history` の TIMEOUT 拒否、
  collection への expected node 包含検査。いずれも gate は存在するが**赤くなる負例が無い**。
  根拠は `output/insights/2026-08-11_t808-mutation-fanout/README.md`。
- {{T:fanout-exact-n-run}} **P2・新規**: fan-out の採用可否を決める exact-N の本走を 1 回行う。
  `--plan-only` は pytest / qsub / receipt / evidence relocation / teardown を通らないため
  本走の代替にならない。**変異集合を増やさず既存 A/B で**行い、cgroup `memory.current` 3 反復・
  Git admin burst・`df -Pi`・全 request 対応・fair-share・最終 `git worktree list` を採る。
- {{T:legacy-mutation-reservation}} **P3・新規**: legacy 単発経路
  (`tools/mutation_worktree.py`) が reservation を取らずに harness を起動する点を塞ぐか決める。
  fan-out 本体は CLI 全体を単一 scope へ再 exec して全子孫へ上限を適用するが、legacy は迂回する。
  段 4 で「既存逐次経路を変えない」と裁定したため本 wave では partial のまま残した。
