---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-10-01
wave: dev-wave-p5-s3-prereg
seq: 2
---

## 新規

### {{F:contrast-history-fields-unfilled}}. 登録が書く coder 入力の履歴の欄を対照の経路が埋めておらず、後続の登録草稿が schema だけを見てそれを前提にしかけた [説明と実装の食い違い] [誤前提]

- 事象: T-2867 登録 §4.1 は「driver の自系列の履歴は本文・結果の分類・拒否の分類・verifier の digest を載せ」と書き、coder 入力を組む `make_policy_coder_input` の schema も
  `verifier_digest`・`reject_subtype`・`reject_rule_id` を持つ。しかし対照の経路は、初期点と評価の結果を `run_contrast_unit` の中で結果の分類だけ書き (verifier の digest を渡さない)、
  coder 出力の schema の拒否と auditor の出力の形式・digest の不一致による拒否は round tool の台帳にだけ残して履歴に入れない (検疫・構文・compile と auditor の通常の判定による拒否は分類つきで入る)。T-2852 の P5 S3 版の改版 wave は、段 1 で schema だけを見て「構造化された失敗理由は履歴で
  critic と独立に届くので critic なしの cell でも規律 3 を保てる」と置き、草稿に書いた。段 6 の read-only レビューが producer の経路を追って指摘し、親が本走の coder 入力 249 件の
  履歴の欄 (延べ 1,638 行で `verifier_digest` を持つ行 0) とコードで裏取りした。T-2867 本走は critic が常にあり (評価の結果の構造は critic 診断を通して届く経路があった)、確認した coder 入力の履歴に現れた評価の結果は全部 certified だった。
  規律 3 の破れと結果への影響は観測していないが、本走全体の失敗の有無はこの集計では確かめていない。land 前に草稿を直したので P5 への実害は無い。
- 根本原因: consumer の入力の schema (欄の存在) を、producer が実際にその欄を埋めることの証拠と取り違えた。登録の文も同じ schema から書かれており、対照の経路を足した実装で
  欄を埋める呼び出しが落ちたことを、登録・草稿のどちらも実データで確かめていなかった。
- 恒久対応: P5 の草稿 `docs/workload-description-critic-intervention-preregistration.md` §3.2・§13 の 2 が、対照の経路で履歴の欄を埋めることを critic なしの cell の発効の前提にした。
  T-2867 側の開示と修復は worklog の {{T:t2867-llm-input-disclosure}}。memory `consumer-schema-is-not-producer-evidence` (入力の欄を前提にする設計は、producer の経路を追うか実データの欄の埋まり方を数えてから書く)。
- 再発検知: 段 6 の事実照合レンズに「schema にある欄が実際の producer の経路で埋まるか」を入れる。P5 の発効の確認で、critic なしの cell の生死確認の coder 入力に、
  失敗した評価の `verifier_digest` が載ることを確かめる。
