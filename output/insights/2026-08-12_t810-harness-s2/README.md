# [T-866] + [T-867] 測定装置 slice 2 — insights package

protocol §9.1 item 1 の (a) N-job barrier 系、(b) T-810 専用 PBS wrapper、(c) runner policy、
(d2) 測定ノード上の repo 不在、(f) 並走ガードの機械化、(g) 予算 admission を実装した wave。

**キューへ T-810 の測定を 1 件も投入していない。**

## この package が主張しないこと (最初に読む)

- **§9.1 item 1 の充足。**6 機構は実装したが、
  **coordinator → PBS script → wrapper → coordinator の production 正例経路は 1 本も通っていない。**
  焦点再レビューは NO-GO で、親はその所見をすべて real と裁定した。残余は worklog の
  新規項へ分離した。
- **投入可能性。**admission policy の `qsub` / `approved_hostnames` / `budget` と
  並走ガードの A 系識別はすべて `unratified` / `unresolved` であり、依存する判定は全面 deny する。
  人間の ratification と承認 ID なしでは 1 件も投入できない。
- **起動認可の権威性。**`t810-launch-authorization/v1` witness に署名も trust root も無い。
  `approval_receipt_trust_root_absent` として機械可読に宣言してある。
- **repo 非流入の完全性。**共有 mount 上の repo 到達性は node 側の検査で消えない。
  `shared_mount_repository_reachability_not_eliminated` と
  `repository_absence_not_proven_from_node` として宣言してある。

## 構成

| file | 内容 |
|---|---|
| `brief.md` | 段 1 brief。scope・不変条件・親の provisional 裁定 (P1)〜(P4) |
| `s4-adjudication.md` | 段 4 裁定。段 3 の 29 所見を real 裁定、plan v2 差分 7 点、変異 18 件の事前登録 |
| `s4-addendum-1.md` | 追補 1。休眠封印と effect gate が両立しないため起動認可 witness を新設 |
| `s4-addendum-2.md` | 追補 2。schema の残存限界・第 2 走査・reason code。親起因の綴り不統一の自己是正 |
| `s4-addendum-3.md` | 追補 3。fix 子のテスト編集範囲 (親の広すぎる禁止で 1 巡空振りしたことへの是正) |
| `s4-addendum-4.md` | 追補 4。焦点再レビューの裁定と、回帰修復のみに絞った fix-4 の scope |
| `s6-fix-adjudication.md` | 段 6 fix 裁定。共通 interface 契約 C-1〜C-7 と 3 巡への分割 |
| `verbatim/s2-plan.md` | 段 2 起草プラン |
| `verbatim/s3-lensA.md` | 段 3 敵対レンズ A (fail-closed 性・非流入) — NO-GO |
| `verbatim/s3-lensB.md` | 段 3 敵対レンズ B (入力の実在・実効性) — NO-GO |
| `verbatim/s6-revA.md` | 段 6 敵対レビュー A (正しさ境界) — NO-GO、blocker 8 |
| `verbatim/s6-revB.md` | 段 6 敵対レビュー B (契約整合・限界の誠実さ) — NO-GO、blocker 7 |
| `verbatim/s6-focus.md` | 段 6 焦点再レビュー — NO-GO、must-fix 7 件 |
| `mutation/mutation-spec.json` | 変異 17 件の事前登録 (結果に合わせて書き直していない) |
| `mutation/mutation-ledger.json` | 変異本走の台帳 |

## 成果物

| path | 役割 |
|---|---|
| `tools/pegasus/t810_harness_schema.py` | 全 artifact の exact schema、canonical digest、起動認可 witness、限界 ID の閉じた集合、(境界, reason) の凍結状態表 |
| `tools/pegasus/t810_coordinator.py` | launch-intent → manifest → submission receipt の create-only DAG、raw evidence から再計算する ready barrier、release/cancel、coordinator 単一時計の開始ばらつき、N 件 exact の完了 verifier |
| `tools/pegasus/t810_pbs_wrapper.py` | canonical qsub argv、単独性と静穏を 1 schema に束ねた node-side preflight、binary の 3 点 hash、測定直前の第 2 走査と cancel 再確認、(d2) の検査 |
| `tools/pegasus/t810_runner_policy.py` | 測定実行の単一 mediation 点。argv は凍結事前登録の projection のみ |
| `tools/pegasus/t810_guard.py` | qstat -f の strict parser、未知状態の拒否、2 相ガード、identity 一致時のみの取り下げ |
| `tools/pegasus/t810_budget.py` | append-only ledger、genesis 束縛、flock 内の予約、精算の遷移表と typed witness |
| `tools/pegasus/policies/t810_admission_v1.json` | 並走ガードと予算の policy。**全 status が unratified** |

## 実測値

| 対象 | 結果 |
|---|---|
| 焦点走 (本 wave の 6 file、計算ノード) | **195 passed / rc=0** |
| 変異 matrix | **17 件中 16 件が期待どおり** (KILLED 15 + 正例 SURVIVED 1)、基準走 PASSED |
| 変異 MISMATCH | M7 の 1 件のみ。**超過検出** (KILLED、期待 1 node は実測 7 node の真部分集合) |
| provenance 全史監査 | rc=0 |

## 実測が静的レビューを超えた事実

実装子 5 本とレビュー子 4 本のすべてが計算ノードへ dispatch できず (`qstat -Q` preflight rc=1)、
全員が正直に「実装済み・未実走」と報告した。**変異 matrix の基準走が本 wave のテストの初回実走**
となり、そこで coordinator の 4 node が落ちた。

欠陥は `presence_valid` の意味が coordinator (slot 行列 + group-root) と schema (document 内の
行列だけ) で食い違い、root だけが不一致のとき必ず例外になるというものだった。
**どちらのファイルも単独では正しく読める**ため、file:line 単位で読む静的レビュー 5 本
(段 3 の 2 本、段 6 の 2 本、焦点 1 本) をすべて素通りした。

基準走が赤だと変異は 1 件も走らない (17 件登録・0 件実行)。fail-closed は正しく働いたが、
検知位置が遅く走行枠を 1 つ失った。

## 変異 matrix の注記

- **M6 は spec から外した。**完了側の測定欠損を `terminal_reduced` と誤判定する変異を単独帰属
  させる入力が現行テストに無く、integrity 理由が完了数判定より先に `incomplete_after_start` へ
  倒すためである。事前登録どおりに無理やり入れず、除外理由を残して裁定へ回した。
- **M7 は超過検出。**凍結された (境界, reason) 表を schema 側のテストも参照するため、
  表を変異させると読み手すべてが落ちる。`DW-M03` に従い冗長 gate として単独変異の証拠から外した。
  期待 node を実測へ合わせて書き換えていない。

## fix の経過 (5 巡)

| 巡 | 内容 |
|---|---|
| fix-1 | model call 上限で SIGTERM。2,106 行を書いて対応表ゼロ。素性を明記した WIP commit で保全 |
| fix-1b | 保全分を監査して完成。**前の子の実害ある抜け 3 件**を発見・修正 |
| fix-2 | 実装せず正しく停止。親 prompt の「既存テストの期待値を変更しない」が広すぎた (追補 3 で是正) |
| fix-2b | argv を凍結正本由来へ、再検査全通過後のみ ack、証明不能な肯定を false 固定 + 限界宣言 |
| fix-3 | 限界 ID 統一、effect の型強制、台帳外部性、精算 witness の内容照合 |
| fix-4 | **fix 巡が自ら作った内部矛盾 2 件**の回帰修復 |
| fix-5 | **実測で出た赤 4 件**の修復 (presence_valid の意味の統一) |
