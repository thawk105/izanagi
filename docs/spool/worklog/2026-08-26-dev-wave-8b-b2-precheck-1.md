---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-8b-b2-precheck
seq: 1
title: 論文 §8 の B-2 は現 main では投入できないと実測で確定した — 実装差分ゼロの precheck (docs のみ、branch worktree-dev-wave-8b-b2-precheck)
---

## 本文

- 依頼は「B-2 (descriptor を条件にした合成の因果証拠) の実験を今投入できるかを実測で確定し、
  着手可能なら最小 canary セル 1 本まで進め、着手不能なら実装差分ゼロで閉塞を構造化して返す」。
  **結論は投入不能。canary も取れない。** 裁定パッケージ =
  `output/insights/2026-08-26_8b-b2-precheck-package.md`。設計判断は {{D:b2-precheck-blockers}}。
- **B-2 の器は段 8c 正式系列である。** 8b 設計 §7 段階 2 の generation/search 実験に対応し、
  段階 1 の selector 実験とは独立だと 8c 事前登録 §2 が明記する。依頼が守れと言った
  「selector 実験は B-2 の証拠に数えない」は、8c 側でも維持されている。
- **最上流の閉塞は、充足を返す終端が設計上存在しないことである。**
  `s8c_preregistration_evidence.py` は `SATISFIABLE_CONDITION_IDS = frozenset()` を持ち、
  条件評価器が仮に充足を返しても id がこの集合に無ければ ERROR へ倒す。充足を返す site は
  同 module に 1 つも無い。**これは実装漏れではない** — 理想的な合成入力に対しても終端が
  `completion-proof-not-machine-checkable` であることを、既存テストが期待値として固定している。
  違反の検出側は空ではなく、10 条件分の評価器が実在する。欠けているのは完了を証明する層だけである。
- **親の provisional 裁定 4 件のうち 2 件が段 3 の敵対相談で覆り、親の再実測で確定した。**
  (P2)「arm 実行は正式発効系列にしか存在しない」は誤りで、`registered-formal-non-certifying`
  という発効判定を呼ばない登録モードが実在する。(P3)「selector に一切従属しない」も誤りで、
  認証経路の build は共有 8b ratified freeze の active 化を要求し、現在それは
  `no-active (v2 未発効)` である。結論 (投入不能・canary 不可) は両方とも維持されたが、
  **理由が入れ替わった。**
- **canary が取れない理由は arm の構造ではなく artifact の不在だった。** 非認証経路も manifest を
  必須とし、その loader は**ちょうど 6 試行**と**世代数 = 整数 2 固定**を要求する。
  段 3 の一方が提案した「1 セル・G=1 の軽い canary」は loader が受け付けない。親が
  loader を直接読んで反証した。
- **段 3 の所見のうち 3 件を不採用にした。** (i) test registry 注入と live module 差し替えで
  発効を偽造できる (real だが production entrypoint から到達せず、repo のコードを書き換えられる
  権限を前提とするため gate を新設しない)。(ii) C04 に旧 no-restart policy が残っている
  (**refuted** — C04 の評価器自身が `forbid_trial_restart` の到達可能性を要求しており、
  残骸ではなく契約である)。(iii) 1 セル canary (上記のとおり loader が拒否)。
- **判定器の CLI 欠陥を 1 件見つけた ({{F:cli-double-module-diagnostics}})。**
  `s8c_preregistration.py` を CLI として起動すると 12 条件すべてが `evaluator-exception` になり、
  package として import して同じ引数で `main()` を呼ぶと本当の内訳が出る。**正しさゲートは
  緩んでいない** — `effective=false` は両形式で一致し、ERROR を無害として受理を広げる consumer は
  段 3 の探索でも見つからなかった。壊れているのは診断経路だけである。正しい診断入口は現存する
  (`python3 -m orchestrator.campaign.s8c_gate_report`)。
- **8c 事前登録 §6 の「現在地」記述が現物より遅れている条件が複数ある** (条件 1 の 100k/4
  hard-code、条件 5・6 の machine-checkable 件数など)。本 wave では直さない — 同文書の
  §1〜§4・§6・§7 の本文全体が条件契約の保護 hash 対象であり、**記述の 1 行修正が発効判定の
  入力を動かす**ためである。条件契約の世代更新を伴う別 wave の仕事とした。
- 段 2 のプラン起草は起こしていない (実装が無いため)。段 3 の敵対相談 2 本 (sol / luna) は
  いずれも `--reasoning high` の read-only で、13 分ほどで返った。段 5・6 は
  「実装しない」裁定により飛ばした。実装差分ゼロのため変異 matrix は免除、受入全走は実施した。

## 次の一手差分

### 新規

- {{T:b2-completion-proof-ruling}} **P1・ユーザー裁定待ち**: 8c 事前登録の完了証明層を
  どう設計するか。(i) 10 件ある machine-checkable 条件のどれから充足証明を実装するか、
  (ii) `SATISFIABLE_CONDITION_IDS` へ条件 id を追加する手続き (誰が承認し、どの record に残すか)、
  (iii) 各条件の充足証明に対する negative control の要求水準。**B-2 の全経路がここに従属する。**
  これはコードの問題である前に「どうなったら充足と認めるか」を人間が決める問題であり、
  8c §6 条件 2 が「充足を返す経路は無い」と書いたのは意図的な fail-closed だからである。
  なお共有 8b ratified freeze の v2 active 化 (現在 `no-active`) は本項と独立に進められる
  別線で、認証経路の build 実走の前提になる ([T-088] の official guard 解禁と射程が重なる
  可能性があるため、着手時に重複を確認する)。
- {{T:prereg-cli-diagnostics-defect}} **P2・新規**: `s8c_preregistration.py` の CLI 起動時に
  12 条件すべてが `evaluator-exception` になる欠陥を直す。あわせて
  `s8c_gate_report.py` がファイルパス直接起動で ImportError になる点も直す。
  受理集合は変わらない (両方とも非発効で rc=1) が、「何が塞いでいるか」を問う経路が壊れている。
  再発防止は、CLI を実プロセスとして起動する検査を足すこと — 現行テストは
  imported module の `main()` を呼ぶため、この経路を一度も通らない。
- {{T:prereg-section6-currentstate-refresh}} **P2・新規**: 8c 事前登録 §6 の「現在地」記述の
  陳腐化を更新する。条件 1 の 100k/4 hard-code、条件 5・6 の machine-checkable 件数など、
  現物が先行している箇所が複数ある。**§6 本文は条件契約の保護 hash 対象**であり、
  更新には条件契約の世代更新と判定器版の扱いの裁定が要る。陳腐化した現在地は、
  precheck を悲観にも楽観にも歪める。
