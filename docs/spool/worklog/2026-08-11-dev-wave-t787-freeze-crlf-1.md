---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t787-freeze-crlf
seq: 1
title: 凍結発行・検証層へ証拠 path の CR/LF 検査を広げた — 裁定 (a) を実装、変異 14/14 KILLED (初回 1 件は期待側の誤りで MISMATCH、訂正後に一致) (コード + テスト、branch worktree-dev-wave-t787-freeze-crlf)
---

## 本文

- **裁定前提の実測 (段 1)。** `evidence_contract_sha256(CR 入り契約)` は拒否せず
  `00205cec988138cc…`、LF 版は `e7e1e5857c11e578…` を返した。同じ契約を `load_contract_bytes`
  へ渡すと `contract-path-control-char` で拒否される。穴は実在し、裁定の前提を覆す新事実は
  なかった。現行契約 38 path に CR / LF / NUL は 0 件で移行なし。
- **設計は {{D:freeze-crlf-single-call-scope}}。**段 2 起草が親案 (node 内で NUL を先に見る) を
  倒した — 文書順で先行する CR/LF が後続 NUL の理由語を横取りするためである。**親が独立に実測して
  裏取りした**: 前=CR 後=NUL の契約を変更前の実装は
  `[evidence-contract-path-nul] '/conditions/11/consumer_requirement/path'` で拒否していた。
  そこで CR/LF は最初の pointer だけ保留し、走査完了後に NUL が無い場合だけ拒否する形にした。
- **段 3 レンズ A が「NUL の全域優先は 1 契約内でしか成立しない」ことを示した。**履歴検証は祖先順に
  各契約を hash するので、祖先が CR/LF・後続が NUL の履歴では祖先側が理由語を決める。
  親は**不変条件の射程を単一 hash 呼出し内に限定する**裁定で閉じた (受理集合は 1 bit も変わらず、
  該当履歴は実測 0 件、二段検査は単一走査の設計を壊す)。履歴側の挙動はテストで固定した。
- **敵対レンズは段 3・段 6 とも 2 本ずつで、段 3 = 2 本 NO-GO、段 6 = A GO / B NO-GO。**
  段 6 で採った must-fix は 3 件 — (i) 発行 API (`prepare_revision`) の CR/LF テストが無く
  「tip だけ新検査・祖先や発行経路は旧経路」という弱実装が生存する、(ii)「CR/LF 以外の制御文字は
  通す」の正例が VT だけで TAB 等を過剰拒否する実装が生存する、(iii) 混在 CR/LF の文書順・
  root が list・深い入れ子が未固定。fix はテスト追加だけで閉じ、production を 1 行も変えていない。
- **同レンズが変異の分類も正した。**M4/M5/M6/M11/M12 は受理集合を変えず理由語・pointer・検査順
  だけを変えるので、kill でなく診断感度の pin として別枠に数えた (`DW-M08`)。
  「理由語の統一は revert 変異が包含する」という親の当初判断も誤りで、独立登録に改めた。
- **変異は 14/14 KILLED (受理集合の kill 8 + 診断感度 pin 6)。期待 node は手打ちせず、
  `--collect-only` の完全集合 (324 node) に対する述語で機械導出した。**置換 15 箇所はいずれも
  対象ファイルに exact 1 回だけ命中することを事前検査した。`M1` は wave 前の実コードの形そのもの、
  `M8`/`M9a`/`M9b` は承認外の過剰拒否を検出する正例である。
- **初回 run で MISMATCH 1 件。原因は実装ではなく親の期待集合の誤りだった (erratum)。**
  `M13-detail-carries-node` の期待に `test_activation_report_marks_legacy_crlf_bound_freeze_invalid`
  の 2 node を入れていたが、`ActivationReport` は `exc.reason` だけを載せて detail を持たないため、
  detail を汚す変異は構造的にこの 2 node へ届かない。期待を 110 node へ訂正して同じ anchor で
  再走し完全一致になった。**初回台帳は消さず insights に残した。**
- **本 wave が変えるのは受理集合の 1 点だけである。**parse と canonical 化の両方に成功する入力の
  うち、key が exact `path` で値が `str`、CR または LF を含むものだけが新たに拒否される。
  `path` 以外の field の CR/LF、非 str の `path`、TAB・BS・FF・VT・U+0001・U+0085・U+2028・U+2029、
  文字どおりの `\r` `\n`、NUL を含まない schema 違反は従来どおり通る。NUL 入り入力の理由語・
  pointer・優先順位は 1 つも変わらない。現行契約 hash
  `c4f3740202de302c9dafc9cecac39165bc2213ebf425d2da8cf7ede91b264471` と既発行 g1 の
  `protected_sha256` `853e6c44442780f180997b86819efaa8cbf245ae15d1a37a83e5b9a4ee99286e` は不変。
- **[T-739] の凍結成果物は 1 byte も触っていない** (両レンズが 17 file の blob hash 一致を確認)。
  同 wave の変異 `M5-nul-to-cr` は当時 CR 受理テストを期待 node に含んでいたが、それは当時の仕様に
  対する記録であって本 wave 後は再現しない。台帳を live code へ突き合わせるテストは存在しない。
- **実装子と fix 子はいずれも sandbox から pytest を起動できなかった** (Pegasus の dispatch
  preflight)。テストを弱める迂回をせず「実装済み・未実走」と報告したので、親が計算ノードで実走した
  (実装後 349 passed、fix 後 365 passed、いずれも rc=0)。
- **セッション事象:** 段 6 のレビュー 2 本を `--lane` 付きで投入して rc=2 で起動前に弾かれた
  (`--lane` は `--stage consult` 専用)。成果物ゼロで再投入して回復した。

## 次の一手差分

### 完了

- [T-787] 凍結発行・履歴検証の層へ CR/LF 検査を広げる裁定 (a) を実装した。単一 choke point
  (`evidence_contract_sha256`) で NUL を即時・CR/LF を保留付きで拒否し、契約の全 path 位置
  38 箇所 × CR/LF・中間位置・root・root list・深い交互入れ子・malformed shape・非 str `path` 配下・
  文書順 pointer・NUL との優先順位・発行 API・複数世代履歴・activation report をテストで固定した。
  設計は {{D:freeze-crlf-single-call-scope}}。変異 14/14 KILLED (受理集合 kill 8 + 診断感度 pin 6)。
  remaining: none
  base: cebd3a8738c2c283ee531a9589e88dfacbe9534a765a4c3f8bc82621b0e0dac0
