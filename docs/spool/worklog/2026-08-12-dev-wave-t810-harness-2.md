---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t810-harness
seq: 2
title: 測定装置 slice 2 — §9.1 item 1 の 6 機構を実装したが production 正例経路は 1 本も通っていない (コード + docs、変異 16/17 期待どおり、branch worktree-dev-wave-t810-harness)
---

## 本文

[T-866] と [T-867] を単一 wave で実装した。**成果は「機構は在るが、端から端まで通る経路は
無い」である。**§9.1 item 1 は充足していない。この判断は焦点再レビューの NO-GO を親が
real と裁定した結果であり、取り繕っていない。

**実測が静的レビュー 4 本を超えて欠陥を出した。**実装子 5 本・レビュー子 4 本はいずれも
sandbox から計算ノードへ dispatch できず、全員が正直に「実装済み・未実走」と報告していた。
変異 matrix の**基準走が本 wave のテストの初回実走**となり、そこで coordinator の赤 4 件が
出た。根は `presence_valid` の意味が coordinator (slot 行列 + group-root) と schema
(document 内の行列だけ) で食い違い、root だけが不一致のとき必ず例外になっていたことである。
静的レビューは 4 本ともこれを見つけていない。fix 後の焦点走は 195 passed / rc=0。

段 4 の裁定は 29 所見すべてを real とし、start-permit 相の廃止 (protocol に無い発明だった)、
launch-intent を起点とする片方向 digest DAG、未承認値に依存する判定の全面 deny、
effect 入口ごとの認可検査、(d2) は検査型 + 限界宣言、を確定した。dormant seal は
validator が `run_authorized=True` を拒否するため effect gate には使えず、
`t810-launch-authorization/v1` witness を新設した (**発行経路は本 wave に作っていない**)。

fix は 5 巡を要した。うち fix-4 と fix-5 は**本 wave の fix 巡が自ら作り込んだ回帰**の修復で、
fix-1 の中断 (model call 上限で SIGTERM、2,106 行を書いて対応表ゼロ) を保全して次の子に
監査させたところ、実害ある抜け 3 件が見つかった。

未達は後続タスクへ送る ({{T:t810-e2e-wiring}})。**測定は 1 件も投入していない。**

- 設計判断の記録は {{D:t810-launch-authorization-witness}}。
- 実測が静的レビューを超えた事実は {{F:child-cannot-run-tests-defect-survives-review}}。

## 次の一手差分

### 更新

- [T-866] **P3・部分完了**: §9.1 item 1 の (a) N-job barrier・共有 release・取り消し marker・
  開始ばらつき測定・完了 verifier、(b) T-810 専用 PBS wrapper、(c) runner policy、
  (d2) 測定ノード上の repo 不在を実装した。機構は在るが
  **coordinator → script → wrapper → coordinator の production 正例経路は通っていない**。
  残余は {{T:t810-e2e-wiring}} へ分離した。
  正本 = `docs/pegasus-node-variance-protocol.md` §9.1 +
  `output/insights/2026-08-12_t810-harness-s2/`
  base: 5925e0b19c9231684d7eb96115a53e5b72147a3a104614e0062accacd058491e
- [T-867] **P3・部分完了**: (f) 並走ガードの機械化 (qstat -f の strict parser、未知状態の拒否、
  A 系優先、競合時の取り下げ) と (g) 予算残枠との突合による投入 admission を実装した。
  **T-139 の識別規約・qsub の project/queue/walltime・承認 host・予算数値はいずれも未承認**で、
  policy の status は `unratified`、依存する判定はすべて deny する。
  実効化には人間の ratification が要る ({{T:t810-ratify-admission-values}})。
  base: 2327ec78c67e3073fed70ebd8d496d941f4fed82afd38c0a49e1fec6bb3cdaeb

### 新規

- {{T:t810-e2e-wiring}} **P2・新規 ([T-866] 段 6 焦点再レビューの must-fix)**:
  測定装置の production 正例経路を 1 本通す。焦点再レビューが挙げた優先順は
  (1) qsub 前の静的 request と node 側 runtime identity の分離を完成させ
  coordinator → script → wrapper CLI を通す、(2) wrapper path/hash を凍結 package の実 bytes へ
  束縛する (現状は caller の自己申告)、(3) guard/budget producer を production へ結線し
  budget receipt の ledger-after を実 ledger bytes と照合する、(4) repository roots を
  caller config でなく effect 前に取得した live git common-dir へ束縛する
  (現状は偽 identity で外部性判定を迂回できる)、(5) executable hash/path を
  validator/build identity と intent/runner-policy 間で同一に束縛する、
  (6) coordinator から実 wrapper CLI を通る正例統合テストを足す。
  **これが閉じるまで §9.1 item 1 は充足しない。**
- {{T:t810-ratify-admission-values}} **P2・新規・ユーザー裁定待ち ([T-867])**:
  `tools/pegasus/policies/t810_admission_v1.json` の `status: unratified` を解消するために、
  (a) T-139 pilot / 本走の anchored `Job_Name` 規約と所有者、(b) qsub の project / queue /
  run kind 別 walltime、(c) 承認 hostname の権威、(d) 予算の総 node 秒・builder / 生死確認 /
  本走の見積り・ledger genesis を決める。§4.3 に既知値は臨界区間 451 node 秒と builder 上限
  1080 秒しかない。決まるまで投入経路は全面 deny のままである。
- {{T:t810-m6-attribution}} **P3・新規 ([T-866] 段 6 変異事前登録)**:
  事前登録 M6 (完了側の測定欠損を `terminal_reduced` と誤判定する変異) が単独帰属不能で
  spec から外れた。その入力を持つテストが無く、integrity 理由が完了数判定より先に
  `incomplete_after_start` へ倒すためである。実効 gate へ再照準して登録し直す。
- {{T:dev-wave-l15-budget-blocks-self-improvement}} **P2・新規・ユーザー裁定待ち
  ([T-866] 段 8)**: 本 wave の自己改善候補 4 件が **`docs/dev-wave/**` の L1.5 予算に阻まれて
  1 件も反映できない**。`DW-O01` へ 3 行 (約 200 bytes) 足すだけで
  `L1.5 unique footprint 9859 bytes > 予算 9566 bytes` になり、実測して撤回した。
  候補は (1) 再投入は新 artifact 名・旧 `.done` を消さない、(2) 中断子の部分成果物は素性を
  明記して保全し次の子に監査させる、(3) 編集量の大きい fix 巡は `--max-model-calls` を
  見積もって上げる、(4) `DW-S06-B` の「既存テスト」を「wave 開始前から tracked のもの」に
  限定する (**これは memory 既知型の再発**で、親が適用しそこねて fix 子 1 本を空費した)。
  規約どおり予算引き上げは自己改善に含めないため変更を止めた。実施するには L2 節の削除
  (ユーザー裁定が必要) で先に空けるか、予算値の独立審査が要る。
  **同じ理由での停止は [T-810] slice 1 の段 8 でも起きており、これで独立 2 例目である。**
- {{T:t810-m7-overdetection}} **P3・新規 ([T-866] 段 6 変異本走)**:
  M7 (retry 表の変異) が **MISMATCH = 超過検出**。変異は KILLED され、期待 node 1 件は
  実測 7 件の真部分集合だった。凍結表を共有する schema 側 6 node が同時に落ちる。
  事後に期待を書き換えず冗長 gate として単独変異の証拠から外した ({{F:m7-frozen-table-shared-coverage}})。
  単一理由へ再照準するか、冗長と確定するかを決める。
