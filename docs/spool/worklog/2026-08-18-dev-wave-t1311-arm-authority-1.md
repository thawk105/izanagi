---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t1311-arm-authority
seq: 1
title: arm が選ぶ入力から二層 digest を導き 7 sink へ消費させた — 「6 sink」は 7 面で、provider へ実際に送った bytes が抜けていた (コード + テスト + 凍結 artifact、branch worktree-dev-wave-t1311-arm-authority、変異 matrix = baseline PASSED・10/10 KILLED・MISMATCH 0)
---

## 本文

- **依頼が名指しした「6 sink」は実際には 7 面だった。** 段 6 の敵対レビューが、
  provider へ**実際に送った** payload / envelope bytes が未検査であることを見つけた。
  6 sink だけを塞いだ状態では「台帳は off、実 stdin は on」の入力が通る。
  台帳の数字を実面数と読み替えずに数え直したのは本 wave の主要な訂正である。
- **[T-1310] を先行必須とした段 2 プランを親が反証した。** H1/H2 の完全定義
  (rratio 80/20・skew 0.9・rmw 0・1,000,000 records・48 threads) と derangement は
  `s8b_holdout_freeze.py` に凍結済みで、`descriptor_for_holdout` という既存 API も在る。
  さらに凍結済み selector payload の hash が交差しており
  (`payload_rr80_on` = `payload_rr20_swapped`)、on/swapped の descriptor 同一性は
  既に凍結 bytes として実現されていた。[T-1310] が要るのは実 benchmark の production profile だけである。
- **`off` の中立入力を手書き literal で作る案を却下した。** 段 3 レンズ A が
  「`source="human_declared"` は一 field で off を識別でき、対照実験の blind 性が壊れる」と指摘した。
  既存 projector を通す形へ変え、`source` が `campaign_search_config_projection` になって
  on/swapped と区別できないようにした。値の非恣意性は凍結端点の中点と
  同 module の `rr50-positive-control` 定数の 2 本で支える。詳細は {{D:arm-execution-digest}}。
- **親自身の実測誤りを 1 件撤回した。** 段 1 brief で「`output/` に `p3-t178` の hit は 0 件」と
  書いたが、狭い path しか grep しておらず、実際は tracked 29 file にある (全て historical)。
  結論 (凍結 bytes の巻き添えなし) は変わらないが根拠が違う。段 4 で訂正した。
- **fix が 2 度、既存の設計テストを反転させる方向へ進み、親が差し戻した。** 1 度目は
  digest chain の検査を completeness へ重複新設して既存診断を奪う形、2 度目は fixture を
  exploratory 化して `[launch-admission]` の別枝へ落とす形。どちらも「新しい要求を足すときに
  既存の診断優先順位を奪ってはならない」に反する。最終形は chain の**呼び出し位置**を
  acceptance の後段へ移すことで解いた。{{F:new-check-preempts-existing-diagnostic}}
- **段 3・段 6 とも 2 レンズが独立に NO-GO / hold を返した。** 段 6 の must-fix 5 件のうち 2 件
  (chain 呼び出しの消失、`enforcement_arm` の削除) は両レンズが独立に指摘した。
  親が refuted と裁定したのは 1 件 — 全 artifact を再生成する label 交換攻撃は、
  事前登録 commit 束縛と append-only registry の履歴走査が担当する既存機構の射程である。
- **codex 子は本 wave でも pytest を 1 件も実走できなかった** (全巡 `qstat -Q rc=1` / child rc=16)。
  測定は親が毎巡引き受けた。親からの `qstat -Q` は rc=0 で、子の sandbox 制約である。
- **エージェント工数**: codex 子 15 本 (plan 1・consult 2・author 3・fix 7・review 2)、
  いずれも `gpt-5.6-sol`。段 5 単位 A は 134 model call / 1530 秒。
  段 6 の must-fix 収束に fix 4 本を要した。
- 変異は 7 sink それぞれについて「producer がその sink へ digest を流さない」形とし、
  pairwise 非同一検査の無効化と **wave 前の実コードの形**
  (`{workload}.g{generation}.{role}` の digest なし invocation ID) を含めた。
  期待 node は probe 走行 (全件 SURVIVED 期待) で観測集合を集めてから完全集合として再登録した。
- 正本 = `output/insights/2026-08-18_t1311-arm-execution-authority/README.md`

## 次の一手差分

### 完了

- [T-1311] arm が選ぶ実入力 bytes から content digest と domain 分離した arm binding digest を導き、
  descriptor・campaign identity・proposal bytes/path・invocation namespace・run-start・
  terminal report・**provider payload/envelope** の 7 sink すべてに消費させた。
  `off` の中立入力は canonical 281 bytes として実体化し
  (sha256 `8ecce69906410c451aa20a242634ba8ce82525636ed912493af6d12487340e89`)、
  同一 holdout の 3 arm が相異なる content digest を持つことを launch 前に要求する。
  検証側は producer helper の呼び出しを撤去し persisted lock/config を独立に読む。
  焦点走 733 passed / 0 failed、変異 matrix baseline PASSED・KILLED 10/10・MISMATCH 0。
  remaining: none
  base: ec2cec4e03c4f787006506408f6fbb15b5be58cc83869e5d021b080a2983f2d2

### 更新

- [T-822] **P2・(ii) の前提が解けた → (ii) は着手可、(i) は [T-1310] 待ちのまま**:
  (ii) 宣言 arm の実走認証を止めていた 2 つの欠落 (実走 arm を示す field の不在、
  `off` 中立入力の canonical bytes の不在) は [T-1311] で解消した。arm は実行を変え、
  7 sink が同じ digest を消費し、変異 10/10 が KILLED である。
  **ただし receipt は引き続き `certifying=false` かつ `c02-arm-binding-unproven` を必須理由として
  保持する** — 証拠契約 C02 は `machine_checkable: false` で評価器 table にも無く、
  充足には receipt v2 と `accept_trial` 実名の整備 (問 3 側) が要る。
  (i) は正式 holdout の producer profile が要るため [T-1310] 待ちのまま。
  base: 2e7d26964fa12941d4a0510b0104991bec4b80626483198f87aab29547374ff3

### 新規

- {{T:role-payload-workload-token-leak}} **P2・新規 (段 6 レンズ A の real 所見、本 wave で scope 外と裁定)**:
  role payload の closed key set が `"workload"` を含み、`_common_payload` が真の workload 名を
  role へ渡す。`off` arm では descriptor が中立でも role は `workload="rr80"` を見るため、
  descriptor ablation を迂回しうる。修正は role payload 契約 (事前登録の凍結範囲に接する) の変更であり、
  digest authority とは別の設計択一である。これが残る限り、6 cell の on/off 差と swapped 追従を
  descriptor 効果として解釈できない。正本 =
  `output/insights/2026-08-18_t1311-arm-execution-authority/README.md`
- {{T:dev-wave-waiter-and-lane-doc-gaps}} **P3・新規 (段 8 自己改善、docs 予算のため未実装 → ユーザー裁定)**:
  本 wave で実測した dev-wave の作法の穴 2 件。(a) 待ち手を producer script の pid file 作成**前**に
  張ると、子が生きていても待ち手が即座に戻る。`DW-O01` は pid file を producer 自身が書くと
  定めるが、**張る前に実在を確認せよ**とは書いていない。(b) `--lane` は `--stage consult` 専用で、
  他段に渡すと rc=2 で起動前に落ちる。`DW-O01` の起動形は `[--lane <lane>]` を段の別なく併記している。
  どちらも 1 行で是正できるが、`DW-O01` は L2 上限を超える大きさで `DW-O20` の余裕も 4 bytes しかなく、
  自己改善契約の「予算に収まらなければ止めてユーザー裁定へ返す」に該当する。
  **諮る点 = どちらの節を削って空きを作るか、別 L2 節へ収容するか、見送るか。**
  なお背景 Bash の完了通知が実体より先に返る事象も観測したが、これは
  `DW-O01` の「通知は先行しうる。完了は `.done` と exit code だけで判定」が既に覆っており、
  実際その規律で誤進行を防いだので候補から外した。
- {{T:holdout-profile-single-source}} **P2・新規 ([T-1310] への申し送り)**:
  [T-1311] の arm resolver は `s8b_holdout_freeze.HOLDOUTS` を descriptor の権威として読む。
  [T-1310] が producer へ入れる rr80 / rr20 の production profile が**同一 bytes を指すことを
  [T-1310] 側が assert する**必要がある。二重管理になると、descriptor と実 benchmark が
  食い違ったまま両方緑になりうる。
