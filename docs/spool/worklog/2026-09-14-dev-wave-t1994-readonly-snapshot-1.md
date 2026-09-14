---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t1994-readonly-snapshot
seq: 1
title: [T-1994] build 中の source 差し替えを封じる sealed snapshot を実装した (コード + docs、branch worktree-dev-wave-t1994-readonly-snapshot)
---

## 本文

- 依頼は D1201 が正式受入の前提とした「実効的な不変 snapshot を計算ノードで実証する」の実装。
  設計択一 4 件は D1439 で裁定済みだった (依頼文の 4 件と一致)。
  **閉じたのは D966 の 4 経路のうち「build 中の source 差し替え (A→B→A)」だけである。**
  「汚染 cache binary の再利用」は閉じていない。
- **依頼文が指した一次資料の path は不在だった。** 実体は
  `output/insights/2026-09-01/t1994-readonly-snapshot-design/` で、日付が dir 階層になっていた。
- **DW-G01 の生死確認が、段 3 の 2 レンズがどちらも予測していなかった実在の欠陥を出した。**
  identity map した user namespace の中では `CAP_DAC_OVERRIDE` により `chmod` が効かない。
  そのままでは **D1755 が chmod で守る build 根が、守るべき相手である build 子から書けてしまう。**
  是正には capability 落としと `CLONE_NEWUSER` の seccomp 禁止が**両方**必要で、
  4 状態を分離した probe で実測した。詳細は {{F:userns-mode-bits-bypass}}、判断は {{D:userns-dual-guard}}。
- **段 2 のプランが未実証の機構を 2 つ持ち込んだため DW-G01 が再発火した。**
  本格実装の前に probe を 4 本走らせ、login node と計算ノードの両方で測った。
  不成立なら数百行を捨てることになっていた。
- **段 6 の敵対レビュー 2 レンズが real 8 件を出し、両方が承認不可と判定した。**
  最重要は (a) **seal していたのは source root だけで親・祖父は seal されておらず、
  子が親 dir を退避して symlink で B を読ませられた** (= D1201 が閉じていなかった)、
  (b) **worker の失敗経路が `os.kill(0, SIGKILL)` に到達し親 process ごと殺す**。
- **親が提案した設計が、別の攻撃を開き直した。** 兄弟 entry の列挙が成立しないと分かったとき
  (`/tmp` に 145,596 entry ある)、親は祖先を元の inode へ self-bind する構成を提案した。
  これは子の側からの rename は止めるが、**mount は dentry に付くため外側 namespace からの
  rename を防げない。** 攻撃テストが「保護なしなら B が見える」対照つきで実走して捕まえた。
  詳細は {{F:parent-proposal-reopened-attack}}、判断は {{D:sealed-private-spine}}。
- **失敗本文に path が無いと原因を特定できなかった場面が 2 度あった。**
  1 度目は親が `/tmp` の entry 数を独立に数えて初めて分かり、
  2 度目は子の stderr を出す変更を入れて初めて分かった。
- 焦点走は計算ノードで 9 回実走し、赤は 385 → 116 → 119 → 31 → 7 → 6 → 3 → 0 と推移した。
  **既存テスト関数は 12 file すべてで 1 つも削除していない** (local main の起点と AST 比較)。
  skip・xfail・期待値の反転・機構の stub は行っていない。
- **変異は本走で 10 件すべて KILLED、生存 0、期待 node と完全一致。baseline も PASSED。**
  M13 (外側からの rename が通る構成へ戻す) と M14 (capability 落としを外す) は
  **この wave が実際に踏んだ後退そのもの**で、再発検知として登録した。
  M15 は観測 node が 29 件あり**冗長 gate**なので、単独では単一理由の証拠に数えないと明記した。
  起草子が提案した両層同時変異は、probe の 4 状態分離が実機証拠になっているため追加しない
  ({{D:mutation-redundant-gate}})。
- **実 CMake の qualification は未完走である。** driver は実装したが、
  D1439(c) が求める一度きりの計算ノード artifact はまだ取れていない。
- 登録を見送った変異が 7 件ある。いずれも `DW-M01` の単一理由性を満たさず、
  無理に近い行を選ばなかった。理由は変異 spec の commit message に残した。
- Codex 子 24 本 (plan 1 / consult 3 / author 8 / review 3 / fix 9)。
  途中で 1 本を名前衝突のため停止させたが、**配下の `codex exec` が orphan として生き残り
  `buildcache.py` へ 223 行書き続けた。** 次の子はそれを「別 session が編集中」と見て
  正しく止まり、親が生死を実測してから継がせた ({{F:orphan-codex-after-producer-kill}})。
- 段 8 は `DW-C00` へ 1 行だけ収容した。**L1 の残りは 6 bytes しかなかったが、上限は上げていない。**
  独立レンズ 1 本が `DW-G01`〜`DW-G04` と 2 つの preamble に**意味等価な 67 bytes** を見つけ、
  義務を 1 つも落とさずに収まった (実測 10,621 / 10,625)。同レンズは親の
  「削減不能・独立 3 例成立・増枠必要」という主張を**三点とも反証**しており、親はそれを採った。
  `test_check_docs.py` は 574 passed / 3 skipped で pin も無傷。
- 成果物と生証拠 = `output/insights/2026-09-14/t1994-readonly-snapshot/`。

## 次の一手差分

### 更新

- [T-1994] **P1・実装は着地**: sealed snapshot を実装し、変異 10 件すべて KILLED・生存 0、
  焦点走と受入全走が緑になった。**残るのは実 CMake の qualification 1 本だけである**
  (D1439(c) が求める計算ノードでの一度きり artifact)。driver は実装済みで、
  既登録の generic dispatch で走る形にしてある。それを取るまで D1201 の正式受入完了とは書かない。
  base: 10ba244061b6f932252f9d65b4dd247c0e36f44846f796b435384854a3c01fbb

### 新規

- {{T:sealed-snapshot-qualification-run}} **P1・新規**: sealed snapshot の実 CMake
  qualification を計算ノードで一度きり走らせ、D1439(c) の artifact を取る。
  driver は実装済み (`orchestrator/manual_probes/t1994_readonly_snapshot_qualification.py`)。
