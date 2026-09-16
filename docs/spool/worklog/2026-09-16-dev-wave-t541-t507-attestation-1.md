---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t541-t507-attestation
seq: 1
title: [T-541][T-507] 資格判定 driver の attestation 成功経路を実データで到達させた (コード + docs、branch worktree-dev-wave-t541-t507-attestation、変異 matrix = baseline PASSED・4/5 KILLED + 1 SURVIVED (事前登録どおり)・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「[T-541] と [T-507] を 1 wave で閉じる。裁定は両者とも択 (a)。『成功経路が一度も
  到達不能』は恒真な保証の最も重い形なので、直したあとに**実データで 1 回通る**ところまでを完了条件に
  する。本題の 2 層修正と記録版上げだけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **完了条件を満たした。** 計算ノード bnode005 で `_attest` が `status: accepted` の payload を
  1 件返し、comparisons 21 行すべてが `pass` になった (Request 861.nqsv、実行 7 秒、
  commit `dcace0db9`、較正 `calibration-753f535a8d024727.json`)。逐語は
  `output/insights/2026-09-16_t541-t507-attestation-reach/attest-861.stdout.json`。
- **一次裁定の一部を scope 外に置いた。** 2026-08-25 の裁定行は両者を「読み込み側の自己整合 gate
  (D155) と同じ wave で扱う」としていたが、本 wave の起動引数がその条項を引用したうえで scope を
  2 層修正と記録版上げに限定した。`DW-C00` の「command 引数は worklog 候補より優先する」に従い、
  [T-506] の loader self-pass gate は実装せず carry に残した。**過去裁定も同じ scope だったかのように
  記録しない。**
- **段 3 の 2 レンズが親 brief の誤りを 4 件正した。** (1) `attestation_records` list が未使用である
  ことから「payload の載る先がない」と一般化したのは誤りで、evidence_manifest が bytes 参照を収録する。
  (2) 完了条件に「attempt の evidence として書かれる」まで含めたのは scope を超えていた。
  (3) 不一致を「比較到達」で完了扱いにする退避案は、不一致では payload が返らないため成立しない。
  (4) 「計算ノードなら一致する見込み」という一般化は、CPU 構成が関係する 3 field 以外を未測定のまま
  導いていた。いずれも段 4 で撤回・訂正した。
- **段 6 のレビュー A が変異事前登録の誤りを見つけた。** 記録値の由来を literal 固定に置き換える
  変異 (M4) は、driver が生成文書の版を v2 に固定している以上**同値変異**で、検出できない。
  `positive` / `SURVIVED` 期待へ登録し直し、harness の SURVIVED 検出能力の正例として使った。
  **したがって「記録値の由来への感度」は本 wave の検証範囲外である** — 実装は parser の戻り値から
  取る形を維持しているが、それが保護されているとは主張しない ({{D:attestation-reach-two-layer}})。
- **段 6 のレビュー B が実測手順の 2 件を正した。** 不一致時に field 別の内容が残らない点は、
  恒久 API を変えず実測 script 側の観測 wrapper で解いた。HEAD 記録だけでは実行コードを復元できない
  点は、実測前に実装を commit して解いた。
- **テスト入力の不整合を実測で確定した。** 共有 fixture `test_schema_v2._valid_document()` の
  `effective_clock.tolerance_pct` は 5.0 で、現行 policy の 2.0 と一致しない。比較実装は両者の一致を
  要求するため、**この不一致だけで必ず落ち、帯判定に到達していなかった**。入力を policy 定数へ揃えた
  (literal は焼き込まない)。policy 外 tolerance を拒否する保護は `test_env_attestation.py` の既存
  テストが引き続き固定しており、失われていない。
- **エージェント工数。** codex 子 7 本 (plan 1・consult 2・author 1・fix 2・review 2)。
  段 5 の実装子は最終メッセージが断片で `check_codex_output.py` 未受理 (`f43_fragment`) となり、
  実装報告は worktree 内の `s5-author.md` から回収した。
- 受入全走は `verdict = child-green`、赤ゼロ (tested main `1afe51f54`)。
  焦点走は計算ノードで 8 passed / 5.74s。provenance full 監査は 10,346 件で新規違反なし。

## 次の一手差分

### 完了

- [T-541] 2 層とも直し、計算ノードで `status: accepted` を 1 件得た。
  remaining: none
  base: aabd59af669ec21d9e472a4e2f618d130af67df43a88d02b1650f160135c51a8

- [T-507] 比較を直し、envelope を `t126-qualification-attestation/v2` へ上げ、
  `observed_profile_projection_schema` を parser の戻り値から記録するようにした。
  remaining: none
  base: 78f7b477816b21cd2bc8f72eda3de6c24125dda393a84a3e4ad95a3d6d261f3f

### 新規

- {{T:attestation-mismatch-rows-not-persisted}} **P2・新規 (段 6 レビュー A の real 所見)**:
  attestation が不一致で終わるとき、**どの field がどの値で食い違ったのかが成果物に残らない**。
  `compare_profiles` は field / expected / observed / verdict を返すが、driver は比較行を捨てて
  固定文言の例外にし、子プロセスの失敗は終了コードだけに畳まれ、台帳へ渡るのは stage / type /
  message の 3 つである。本 wave はこれを**既存の欠落**と裁定して scope 外に置いた (新たな握り潰しは
  作っていない)。今回の実測 script は観測 wrapper で非 pass 行を出せるようにしたが、これは実測限定で
  恒久経路ではない。規律 3 の射程に入るかの判断を含めて裁定したい。

- {{T:attestation-projection-schema-provenance-unverified}} **P3・新規 (段 6 レビュー A の real 所見)**:
  `observed_profile_projection_schema` を parser の戻り値から導くか literal で書くかは、
  **現在のテストでは区別できない** (M4 が同値変異)。driver が生成文書の版を固定している限り
  出力が変わらないためである。由来への感度を検査したいなら、v1 文書を通す経路か、版を変えて
  往復させる検査が要る。**受理集合は変わらないので優先度は低い。**
