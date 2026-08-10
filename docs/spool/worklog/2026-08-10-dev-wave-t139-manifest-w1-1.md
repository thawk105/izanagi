---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t139-manifest-w1
seq: 1
title: 第 2 erratum を起草・機械化し、Q-D の同一 land が manifest の構造要件と両立しないことを示した — 承認 manifest・受領証 schema・予約台帳・producer 本体は実装しない裁定 (コード + docs、受入 7994 passed / 20 skipped / rc=0 / 516.74 秒、変異 7/7 KILLED・SURVIVED 0、land しない、branch worktree-dev-wave-t139-manifest-w1)
---

## 本文

- **依頼は §58 裁定の (i)〜(v) 全部だったが、段 3 の敵対レンズ 2 本と段 6 のレビュー 2 本が
  すべて NO-GO を返し、親は独立所見 19 件を全件 real と裁定した (refuted 0 件)。**
  これで親の一般化が段 3 で覆るのは 8 wave 連続である。
  実装したのは第 2 erratum の機械化 1 単位だけで、承認 manifest・受領証 JSON Schema・
  `a13` / `b03` 予約台帳・producer 本体は**実装しないと裁定した**。
- **最重要の棄却理由 — Q-D の「同一 land」は manifest の構造要件と両立しない。**
  Q-A は record-items へ「承認済み修正」を求めるが、現行 record-items は D262 が
  承認済み blob として digest 固定している。`F_e` (D262 の fold commit
  `dce4ae4fed6f4fb33747165c5b92c16d01822850`) より後に生まれた blob を `F_e` は承認できない。
  承認には新しい fold が要り、manifest は自分の fold SHA を literal に持てない
  (D262 自身がこの理由で 2 段構成を採った)。**fold 2 回 = land 2 回が構造的に要る。**
  選択肢を裁定パッケージ R1 で返した。親の推奨は「文書承認の fold だけを先に land する 2 段 land」。
- **Q-B の「承認まで pilot を機械的に止める」は既に成立していた。**
  T-139 の投入 API は 1 つも実装されておらず、D264 の非 export 検査が機械固定している。
  ここへ停止 gate を新設すると D264 が名指しで却下した恒真 deny の stub になる。
  作るべきは gate ではなく「gate を作るとき第 2 erratum の承認を受理条件に含める」という要件の
  記録だったので、そう記録した。**親は当初これを「gate を実装する」と読み違えており、段 4 で撤回した。**
- **段 6 レビュー A が親の起草文書の欠陥を実証した。** 起草した第 2 erratum の検査は
  「置換後も 1 行」しか要求しておらず、**任意の 1 行に置換できた**。レビュアの probe では
  `事前 simulation で cluster level の型 I 誤りを較正済みである。` が通過した — これは
  erratum が除去しようとしていた強い主張そのものである。承認予定 `new_text` の
  exact digest (117 bytes) 固定で塞ぎ、変異 M7 が実際に kill することで裏を取った。
- **Q-A 第三分岐には閉じられない残余がある (裁定パッケージ R2)。** 6 条件で拘束したが、
  レビュー A が「6 条件をすべて満たしながら実際には性能 run を実行済み」の attempt を
  構成してみせた。producer 権限内の証拠だけでは原理的に閉じない。
  certified 値は上がらないが**試行台帳の「実行しなかった」が偽造可能**になる。
  裁定済み項目なので親は止めず、非保証として明記したうえでユーザーへ注記した。
- **D263 に事実誤りを見つけた。** 「同じ core に対する第 2 の erratum が既に承認済みである」と
  書くが、その文書は存在しない (Q-B が本 wave に起草させた)。承認されていたのは §47 R2 (a) の
  **方向**であって文書ではない。{{D:erratum-registry-membership-is-not-approval}} で
  当該事実文だけを前向きに失効させ、決定本文は残した。
- **段 1 の後に追補 B が land し、U5 の scope が過小だったことが判明した。**
  `b03` は primary とは別の「個別公表系列台帳」を要求する (台帳 2 本)。
  さらに受入投入の直前に追補 B の承認保留裁定 (B8 (a)) が land し、追補 B は段階 1 に
  留め置かれ、公表手続きの正本は新 core を起こす別 study で凍結することになった。
  **同裁定は「Q-A〜Q-E の裁定は不変」と明記しており本 wave の前提は覆っていない**ので
  巻き戻さず、`b03` の扱いを「新 core 側の確定後に再評価」と正確化して取り込んだ。
- **`verify_receipt` は既に別概念で実在する** (`orchestrator/campaign/t080_freeze_migration.py`、
  s8b freeze receipt 用)。D75 の同名二義化にあたるので裁定パッケージ R5 で返した。
- 受入は 1 走 (`7994 passed / 20 skipped / rc=0`、516.74 秒、計算ノード)。測った tip は
  `50b9c8de86685eaf7d828de1b61d87e07f8ef41e`。lease は取得・release とも rc=0。
- **本 wave は Q-D により local main へ land しない。** 次 wave は main からではなく
  本 wave の tip から worktree を作る。spool fragment は本 branch に置いたままとし、
  採番と canonical 追記は最終 land の lock 内で一度だけ行う。
- 実測の空振り 1 件 — 変異 harness は spec を検査対象 checkout の**外**に置くことを要求する。
  repo 内 path を渡して `rc=2` で 1 走を無駄にした。記録として repo へ commit しつつ、
  実行時は repo 外の写しを渡すのが正しい形である。

## 次の一手差分

### carry

- [T-316]
- [T-657]

### 更新

- [T-139] **P1・第 1 波は完了、ただし land していない (Q-D)。次はユーザー裁定 R1 待ち**:
  第 1 波 (branch `worktree-dev-wave-t139-manifest-w1`、tip
  `50b9c8de86685eaf7d828de1b61d87e07f8ef41e`) は第 2 erratum の起草と機械化、
  record-items 再発行版 (Q-A 第三分岐 + 未閉包 nested object 7 種の exact key 閉包)、
  D263 事実文の失効だけを作った。
  **承認 manifest・受領証 JSON Schema・`a13`/`b03` 予約台帳・
  `resolve_effective_preregistration` / `PreregBinding` / `verify_receipt` は未実装。**
  **pilot は投入不可のまま** (投入 API 不在 + D264 非 export の機械固定による)。
  裁定 5 問 = (R1) **Q-D の同一 land が manifest の構造要件と両立しない** — 新しい承認済み blob は
  それを承認する fold の後でなければ manifest に pin できず、manifest は自分の fold SHA を
  literal に持てない。**fold 2 回 = land 2 回が構造的に要る。**親の推奨は文書承認の fold を
  先に land する 2 段 land /
  (R2) Q-A 第三分岐は「実行しなかった」を証明できず、試行台帳の偽造余地を残す。
  producer 権限外の collector が要る /
  (R3) `a13` 台帳の保証境界 (land lock は Git common dir 内。独立 clone は防げない) と
  `b03` による 2 本目の台帳 /
  (R4) gate が効くために必要な未実装層 (intent / PBS / driver / collector / receipt writer /
  correctness verifier / certified consumer) /
  (R5) `verify_receipt` の同名衝突。
  逐語 = `output/insights/2026-08-10_t139-manifest-w1/`
  base: 484c40b7c83a6473c946edeeaf20d1086fc654cc0d03ae22e1a911f627e1ee29
