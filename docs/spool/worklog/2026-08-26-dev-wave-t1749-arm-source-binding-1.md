---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1749-arm-source-binding
seq: 1
title: [T-1749] 宣言 arm を build・bench された CCBench source へ因果束縛した (コード + テスト、branch worktree-dev-wave-t1749-arm-source-binding、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **段 3 の 2 レンズが独立に同じ穴を指摘し、段 2 plan の芯が不足だと分かった。** plan は
  proposal 全 bytes の SHA で source artifact の path を決めれば proposal→source を閉じたと
  したが、これは命名規則であって内容の因果束縛ではない。宣言 A の述語と別 source B の
  preimage を同じ名前で保存すれば、plan の全述語を通る。レンズ A は具体的な payload / WAL /
  provenance の組を構成し、レンズ B は同じ反例を別の言い方で示した。
- **レンズ B の修正案は実測されていなかった。親の probe が決着させた。** B は
  「preimage 内の代入が proposal 由来の述語と exact 一致することを検査せよ」と提案したが、
  根拠の byte 数は素の checkout の値で、素の木では preimage 中に gate 変数が 1 件も現れない。
  親が template patch を実適用 + 即時復元する probe を回し、materialize 後は代入行が
  逐語で残る (2 マクロ文脈 x 3 出現) ことを確かめて採用した。逐語は
  `output/insights/2026-08-26_t1749-arm-source-binding/README.md`。
- **段 2 plan の編集面を不採用にした。** `campaign_lock.py` の強制ソース閉包は exact 25 path で、
  plan が書き込み経路を足そうとした 2 file がその中にある。閉包 file を 1 byte 変えると
  記録済み blob map と現在の map が食い違い、既存 campaign が全部 `E1-stale` で
  certified 受入から外れる。閉包の外だけで同じ保証を作る設計へ寄せた
  ({{D:acceptance-gates-stay-outside-the-enforcement-closure}})。
- **閉じない部分を閉じたと書かない方針を裁定した。** 関連付け検査は「宣言した文字列が実体に
  在る」ことまでしか示せず、非到達化や別変数による実効分岐は受入時点に checkout も compiler も
  無いため consumer 単独では閉じない。証明の種別を届いた範囲そのもので命名し、
  実行到達性は主張しない ({{D:proof-kind-names-the-actual-reach}})。
- **述語が空振りする 3 経路を実測して塞いだ。** 正式受入は呼び手が差し込んだ driver を
  拒否しておらず (親の grep で受入側に該当文字列 0 件)、その driver では producer の
  artifact 契約が発火しない。materialized なのに build-and-bench がゼロの束、
  trigger 以外の軸の混入も同様。3 件とも受理集合を狭める方向として実装した。
- **子の成果物を 2 本失った。** 段 3 レンズ A 1 本目は既知 2 原因 (web 検索の重複キー・
  非 NFC) を実測で否定した F540 の型で、別 job-id での再投入で解決した。
  段 5 実装子は非 NFC で、発火源は**親が裁定文書へ書いた代替表記**だった
  ({{F:parent-placeholder-invites-non-nfc}})。どちらも保全して読んだが単独根拠にしていない。
- **待ち手が完了を偽る事象を 6 回踏んだ** (F518 再発)。うち 1 回は害が出て、親が
  「投入ラッパーが落ちた」と誤診してユーザーへ報告した。実際には全走が継続中で、
  後に完走したため訂正した。終盤は `.done` の現物確認と harness process の直接照合へ
  切り替えた。**あわせて、親が測っていない時刻を報告へ書いた**ので、以後は実測した時刻だけを
  書くよう改めた。
- **親の編集が変異走行を止めた。** 待機中に台帳の下書きを repo 内へ置いたため、harness が
  走行前に untracked 検出で fail-closed した。壊れたものはない。下書きを repo 外へ退避し、
  同時に両層同時変異を最終巡へ統合して走行を 1 本節約した。
- 変異 probe 巡で 1 件が SURVIVED した。E1 の mask 等式で、digest が mask の純関数である以上
  digest 等式が mask 等式を含意する冗長 gate だった。両層同時変異へ再照準して KILLED を確認した。
- 全走の赤は 48 → 18 → 0 と減った。48 のうち 12 件は非帰属で、`output/` ツリーの前後
  スナップショット一致を要求するテストが並行走行中の書き込みで落ちたものである
  (単独走でそれぞれ 455 / 41 件すべて緑を実測)。最終の全走は 16,580 passed / 0 failed。
- 子の工数: codex 8 本 (plan 1・consult 3 (うち 1 本不採用)・author 1・review 3 (うち 1 本は
  親の必読指定ミスで即停止)・fix 2)。model は全段 `gpt-5.6-sol`、reasoning は `xhigh`。
- 段 8 の自己改善候補は {{F:parent-placeholder-invites-non-nfc}} の恒久対応として
  `DW-O02` へ「非 ASCII は `chr(...)` 表記で渡す」を足せるかを検討したが、
  `docs/dev-wave/**` の byte 予算が満杯のため入らなかった。裁定へ回す。

## 次の一手差分

### 完了

- [T-1749] 宣言 arm から build・bench された CCBench source への因果束縛を実装した。
  D863 第 2 条件のうち、宣言と実体の**文字列としての同一性**は閉じた。実行到達性は
  閉じておらず、下記の新規項目として分離した。
  remaining: none
  base: 1d75be48914340562345f5e148f3daf200d15d35c549a43c4c9b981839c3fff9

### 新規

- {{T:acceptance-proves-execution-reach}} **P1・ユーザー裁定待ち**: 宣言した述語が実際に
  **実行される**ことを正式受入が証明できるようにするか。現状は文字列としての実体化までで、
  非到達化・別変数による実効分岐・build 中の source 差し替え (A→B→A)・汚染 cache binary を
  排除できない。immutable snapshot からの build か compiler input manifest が要る。
  D863 第 2 条件を文字どおり閉じるならこれが残件である。
- {{T:prereg-contract-fieldpaths-need-freeze-reissue}} **P1・ユーザー裁定待ち**: 事前登録契約の
  C10 `field_paths` を本 wave の新 field まで広げるか。契約 JSON は条件凍結の保護 hash 対象で、
  評価器は強制ソース閉包の中にある。広げるには凍結の再発行と判定器版の bump が要り、
  既存 campaign が全部 `E1-stale` になる。現状は契約の記述が実装より弱い。
- {{T:cross-binding-leaf-receipt-durability}} **P2・新規**: cross-binding 受領証の本体を
  永続化し、後段 verifier が再検証できるようにする。現在は outer receipt に SHA だけが残り、
  後段は leaf を再実行も再読もしない。certification を有効にする前に閉じる必要がある。
- {{T:acceptance-gate-enforcement-closure-membership}} **P2・新規**: 受入 gate 本体
  (照合器・登録器・受領証) を強制ソース閉包へ入れるか裁定する。現在 closure の外にあるため、
  gate を「certified acceptance の強制ソース」とみなすなら scope 不足である。
- {{T:dev-wave-nonascii-in-parent-documents}} **P3・新規**: 親が子へ渡す文書で非 ASCII を
  `chr(...)` 表記に固定する規律を `docs/dev-wave/` の該当節へ入れる。byte 予算が満杯のため
  本 wave では入らなかった。予算の扱いと併せて裁定する。
