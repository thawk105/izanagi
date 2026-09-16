---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t1232-rootless-failure-report
seq: 1
title: [T-1232] failure-only の診断 report を root 引数なしで独立検証できるようにした (コード + docs、branch worktree-dev-wave-t1232-rootless-failure-report、変異 matrix = baseline PASSED・8/8 KILLED・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「failure-only の build report を root 引数なしで独立検証できるようにする。
  root を省いてよい根拠を明確にし、束縛検査の一律撤去には広げない (規律 2)。本題の契約整合だけ。
  仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。一次資料は
  `output/insights/2026-09-16/t1232-rootless-failure-report/README.md`。
- **起票文の前提は着手時点で一部閉じていた。** root 要求には免除が 2 つあり、campaign 生成前に落ちた
  6 key の fallback cell は既に root なしで通っていた。後者の免除は 2026-08-18 の T-1348 配線が
  副次的に入れたもので、T-1232 を閉じる意図ではなかった。
- **生きていた穴は起票文より深かった。** campaign identity を宣言した admission 失敗 cell は
  **root を与えても** cross-binding が落とす。producer は publish 前に cross-binding を呼ばないので、
  producer が出せて独立検証器が原理的に受けられない report があった。
- **親の段 1 brief の中心前提を段 2 plan が倒した。** 「root を省くと失われるのは path identity 束縛だけ」は
  誤りだった。さらに brief が producer 実出力の例に挙げたテストは、検証機構 4 つを monkeypatch で無効化しており
  証人にならなかった。**段 3 の 2 レンズも同じ 2 点を独立に指摘し、親が現物で裏取りして段 4 で訂正した。**
- **段 4 の中心裁定: 非 certifying の診断検証として成功集合を増やすことを認めた。** 受理を 1 つも増やさない案では
  依頼を満たせないためである。依頼の歯止めは「束縛検査の**一律撤去**」であり、閉じた厳密述語 + 明示 opt-in +
  既定経路無改変はそれに当たらない。ただし段 3 レンズ A の条件どおり、opt-in と `certifying=false` を
  受理集合不変の証拠にせず、**成功集合が増えることを明示して記録した。** 判断は {{D:failure-only-diagnostic-verification}}。
- **段 2 plan の設計の核を段 3 レンズ B が倒し、親が却下した。** 既存の role / provider 束縛検査の流用は、
  救済対象の report が provider 成果物も raw 参照も持たないことがあるため、救済対象自身を落とす。
  差し替えた要求は「欠けている束縛は飛ばすのでなく、不在を report 側の事実と突き合わせて証明する」。
- **段 6 レビュー A が裁定 (D) 違反を 1 件見つけた。** 提案が宣言されているだけで producer 状態の確認を
  飛ばしていた。fix で拒否へ狭めた。
- **段 6 レビュー B が変異 2 本の生存を事前に示した。** M4 は先行 accounting 検査に覆われ、M7 は
  `status != partial` と件数検査に遮られる。M4 は raw bytes 検証へ再照準し、M7 は fix 子が
  単一理由の入力を構成不能と確定したので登録から外した。**実走前に登録を直したので、変異 matrix は
  1 回目 (probe) から全件が観測 node を出し、2 回目 (final) で 8/8 が完全一致した。**
- **`EnterWorktree` はこの repo で両形とも使えなかった。** name 形は `Could not read the repository git config`、
  path 形は内部の `git worktree list --porcelain` が 10 秒上限を超えた (実測 17.6 秒 / 19.7 秒、worktree 113 本)。
  手動 `git worktree add` と絶対 path で進めた。add は 1 本あたり約 18 分かかった。
- **受入全走の 1 回目は 1 failed / 24109 passed で、赤は本 wave に帰属した。** 実装子が足した test helper が
  coder build authority の低レベル発行 helper を直接呼んでおり、その呼び出し箇所を repo 全体の AST で
  数えて許可台帳との完全一致を要求する検査に当たった。**pin の key が path でも wave の symbol でもなく
  「新たに呼ぶ callee の名前」で走査範囲が全域**だったため、段 1 の pin 閉包・段 6 の焦点走・レビュー 2 本の
  いずれも拾えなかった。F30 の再発として記録した。許可台帳へ行を足さず、既に台帳に載っている helper の
  流用へ置き換えて直し (test file の +2 / -4 行)、変異 matrix を取り直した (8/8 KILLED・完全一致)。
- **受入前の main 取り込みで所要台帳の `nodeid_count` が衝突した。** 台帳は実装面なので Codex 子に解決させた。
  その子の報告が 477 byte で出力検査の下限 500 byte に届かず不受理になったため、別の子に変更させずに
  独立監査させて受理した。**作業が小さいほど報告が短くなり下限に掛かる**という型である。
- 工数: codex 子 10 本 (plan 379 秒 / 9 call、consult 175 秒 / 6 call と 203 秒 / 9 call、
  author 1243 秒 / 55 call、review 226 秒 / 8 call と 148 秒 / 7 call、fix 646 秒 / 38 call、
  台帳衝突の解決 32 秒 / 2 call (不受理) と監査 1 本、authority 修正 1 本)。
  変異走 3 回 (job 所要の和: probe 787 秒、final 340 秒、final2 は insight の ledger)。受入全走 2 回。

## 次の一手差分

### 完了

- [T-1232] 明示 opt-in の非 certifying 診断検証経路 (`verify_autonomous_trial_files(..., failure_only_diagnostic=True)`、
  CLI `--failure-only-diagnostic`) を足し、producer が publish する identity 付き failure-only report を
  root 引数なしで独立検証できるようにした。既定経路は無改変。
  remaining: none
  base: a48145ceac6d283e8b17767605f01776d04bdc1ef1ac2f644e415d458e09b293

### 新規

- {{T:formal-failure-report-unpublishable}} **P2・新規**:
  正式 registered 系列で campaign identity を持つ admission 失敗は、publish 前に
  `autonomous_trial_completeness.py` の digest 検査 (現行 1137 行付近) で拒否されるため、
  **診断 report が 1 件も残らない。** 探索走は本 wave の診断経路で独立検証できるようになったが、
  正式系列の失敗は回復していない。回復させるなら producer と digest 契約の一体改訂になる。
- {{T:producer-cross-binding-asymmetry}} **P2・新規**:
  producer は publish 前に `verify_s8c_cross_binding` を呼ばず、standalone verifier と受入だけが呼ぶ。
  この非対称が「producer が出せて検証器が受けられない report」を生む根である。
  producer 側で呼ぶか、verifier 側で受けられる形を増やすかは設計択一で、本 wave は後者を
  探索走の閉じた形についてだけ採った。
- {{T:admitted-prefix-failure-unverifiable}} **P3・新規**:
  複数 workload のうち先行 cell が admitted で最後の cell だけ identity 付き admission 失敗の混在 report は、
  campaign output root を与えても cross-binding の build population 要件と failure chain の条件が両立せず
  受理できない。本 wave の診断経路は cells 長さ 1 に限るので救済しない。
