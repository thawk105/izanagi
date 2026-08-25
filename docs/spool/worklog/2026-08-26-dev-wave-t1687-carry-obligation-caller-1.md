---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1687-carry-obligation-caller
seq: 1
title: [T-1687] 繰越義務述語を段 6 候補提出の前提関門 adapter へ結線する (コード + docs)
---

## 本文

- 段 0 から繰り越した fixture 義務の解消述語 `require_stage0_fixture_obligations_discharged()` は、
  production から一度も呼ばれていなかった。設計正本は「将来の段 6 実装が呼ばなければならない」と
  記すだけで、呼び手は 0 件だった。ユーザー裁定 (2026-08-25 /rulings 全件、暫定) の
  「呼ばれない義務は無いのと同じである」に従って結線した。
- **成果物は呼び手不在の adapter である。** `require_stage6_candidate_submission_ready()` を
  production 側に置き、そこから義務述語を呼ぶ。終端は 2 つで、義務未解消の拒否と、
  義務通過後の段 6 policy 未解決の拒否を別型・別 reason code に分けた。
  adapter を呼ぶ operational caller は 0 件のままである。記録では常に
  「production adapter 1 件・operational caller 0 件」を並べて書き、前提条件表は `unmet` に保った。
- **上流の呼び手は本 wave では作れない。** 段 6 の候補提出経路は段 5 の policy 裁定
  (`CFAB-STAGE6-POLICY-PREDICATE` = `unresolved`、owner = user) に依存し、X の発効自体が
  D437 の lockstep と人間 seal の手番である。親がこの 2 つを飛び越えない判断は {{D:stage6-adapter-vs-operational-caller}}。
- **両レンズの敵対相談と敵対レビューが、同じ核心所見へ独立に収束した** — 「入口を作っても
  呼び手がゼロなら D580 の型 (問題を API 呼び出しの一段手前へ移すだけ) に当たる」。
  親はこれを real と裁定し、実装は行うが記録を格下げした。段 3 で 12 件、段 6 で 10 件の所見。
- **段 6 レビューが、親が書いた設計正本の文言に迂回経路を見つけた** — {{F:authority-doc-prescribed-gate-bypass}}。
  親は「段 6 の候補提出前に義務述語を呼ぶ」と書いたが、それでは将来の実装が義務述語を直接呼んで
  adapter の policy 終端を迂回できる。3 箇所とも「呼び手は adapter を呼び、adapter が義務述語を
  呼ぶ」へ書き換えた。
- **呼び手の件数そのものを機械検査にした。** 実 working tree の Python を走査し、義務述語を呼ぶ
  module 集合と adapter を呼ぶ module 集合を AST で数え、前提条件表の 6 cell と設計正本
  §10.2 / §12.3 の逐語へ exact に束縛する。将来 operational caller を 1 件足すと、
  台帳の該当行を同じ変更で直さない限り検査が赤になる。
- 段 6 レビューの実測で、素朴な部分文字列による事前絞り込みは全角で書かれた同名呼出しを
  取りこぼすことが分かった。Python は識別子を NFKC 正規化するため AST の葉名は ASCII になる。
  親が反例を実走で確認し、判定を NFKC 正規化後に対して行う形にした。走査所要は 6.1 秒から
  0.2 秒へ下がった。
- 段 1 の実測: 義務述語の合格終端は述語自身の引数経路では到達不能である。gate の
  `(gate_id, owner, status)` 三つ組が contract module の literal と entries hash に二重固定されており、
  どんな fixture root を渡しても `deferred_gate_ids` を空にできない。合格側の対照は
  `validate_repository` の差し替えでのみ構成できる。
- 親の実測 2 件の訂正: (a) `orchestrator/campaign/` 配下から `orchestrator.tests` を import する
  既存 module は 0 件である (`tools/hold_inventory.py` は運用 tool であり先例ではない)。
  (b) 呼び手 0 件・編集面の重複 0 件は観測集合での 0 であり、ignored untracked・stash・
  remote-only ref・別 clone を含まない。
- 非帰属の赤: `test_calibration_freeze_authority_contract.py` の単体実行は変更前から 3 件赤
  (`monkeypatch` 引数を取るテストを自走 harness が扱えない)。
  `test_real_repo_serialization.py` の単体実行も 5 件赤 (4 件は同じ fixture 未供給、
  1 件は `cache-path-unavailable`)。いずれも main の blob と照合して差分外を確認した。
  別変更単位で解消する。
- 工数: Codex 子 7 本 (plan 1、consult 2、review 2、author 1、fix 1)。全件 `gpt-5.6-sol` / xhigh /
  accepted。

## 次の一手差分

### 更新

- [T-1687] **P1・ユーザー裁定待ち**: 繰越義務述語を段 6 候補提出の前提関門 adapter へ結線し、
  呼び手の件数を機械検査にした ({{D:stage6-adapter-vs-operational-caller}})。残件は
  **adapter を呼ぶ operational caller が 0 件**であること。実段 6 submitter の所有 module と
  canonical な呼出し位置、および「提出 writer を関門の内側へ閉じ、外から呼べる下位 writer を
  公開しない」要求を裁定してほしい。段 6 policy gate が `unresolved` である限り submitter は
  完成しないため、先に所有と呼出し位置だけを決める形も選べる。
  base: 4369b77c6697a7e1a486b67b29b388acff4cc59ed38beda49afa9779a7e67ee4

### 新規

- {{T:stage6-contract-module-layer}} **P2・新規**: 契約 module と authority data を
  production / shared 層へ移すか、tests / docs を production の runtime 依存として認めるかを
  裁定する。現状は `orchestrator/campaign/` から `orchestrator/tests/` を import する逆向きで、
  同配下に先例が無い。
- {{T:plain-runner-fixture-support}} **P3・新規**: 自走 harness が `monkeypatch` / `tmp_path` を
  取るテストを実行できず、`test_calibration_freeze_authority_contract.py` で 3 件、
  `test_real_repo_serialization.py` で 4 件が単体実行時に赤になる。pytest では緑であり
  受入には影響しないが、単体走の緑が意味を持たなくなっている。
