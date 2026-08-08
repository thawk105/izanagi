---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t648-fallback-ledger
seq: 1
title: [T-648] 受入免除判定の証拠記録義務を fallback (台帳 + memory) で発効させた — 契約本文は 1 byte も変えず、本文昇格は再訪条件付きで見送り台帳へ (docs のみ、実装差分なし、受入 7504 passed / 1 failed = F57 再発・単独再走 1 passed / 20 skipped、変異は免除、branch worktree-dev-wave-t648-fallback-ledger)
---

## 本文

- **ユーザー裁定 2 件に基づく fallback 実施 wave。** (1) 2026-08-08 /rulings: [T-648] = (b) +
  遡及なし — 「実 repo を読むテストがあるか」の判定証拠 (該当 nodeid か「不存在」の判定手順) の
  worklog 記録を dev-wave 契約へ 1 文足す。**予算内に収まらなければ [T-641] (c) と同型に台帳記録へ
  落とす** (rulings branch `worktree-rulings-20260806-a` の fragment seq 25、本 wave 時点で未 land)。
  (2) 2026-08-09 本セッション、ユーザー逐語「(B') 再訪条件付き fallback で進めて」。
- **発効させた義務 (正本 = 本エントリ + memory `record-acceptance-exemption-evidence`):**
  docs-only / 実装差分ゼロの wave が受入全走の要否を判定するときは、「実 repo を読むテストが
  あるか」の判定証拠 — 該当テストの nodeid、無ければ「不存在」と判定した検索手順 — を
  worklog (fragment) へ記録する。
- **契約本文は変えていない。** `docs/dev-wave/**` の aggregate は 25,199 / 25,200 bytes
  (空き 1 byte)、dispatcher は 9,457 / 9,500 bytes (空き 43 bytes) を本 wave で実測し、
  裁定 (b) の 1 文はどこにも入らない。[T-664] は未 land のうえ branch 側の結論が
  「依頼 2 経路で解放 0 bytes」のため、予算待ちをやめ fallback 条項を発動した。
  memory への固定は repo 予算を使わない (t664 wave 段 8 の memory 固定と同型)。
- **canonical decisions の旧射程記載 (D72 ほか) は遡及改変していない** (裁定どおり
  前向き supersession のみ)。
- **義務の初回適用は本 wave 自身。** 実 repo を読むテストは存在する — 判定証拠 =
  `orchestrator/tests/test_check_docs.py` / `orchestrator/tests/test_spool_fold.py`
  (いずれも実 checkout の docs/ と spool を読む) — したがって docs-only だが受入全走を実施した。
  **7504 passed / 1 failed / 20 skipped** (tip `5bcf6382`、request `896541`、1260 秒)。
  赤 1 件は F57 の再発 (`test_ruleops.py` の real_repo node が `ruleops: git-timeout` で rc=2)。
  単独再走は 1 passed / 75.55 秒で再現せず、`DW-O18` により実装差分へ帰属しない。詳細は F57 の再発追記。
- **受入 lease が 2 時間 15 分取得できなかった。** 60 秒周期の待ち手が 90 分空振りし、30 秒周期へ
  詰めて取得した。その間 holder は 5 回交替しており、並行 wave の輻輳が実測値として残った
  (この観測は F57 の再発追記でも独立の裏付けとして使った)。lease に fairness は無く、
  待ち周期が短い側が有利になる — 短い wave が長時間待たされる構造は残っている。
- **peer wave 由来の provenance 赤を 1 件検出したが、本 wave では直していない。** main の祖先
  `2c192953` ([T-659] wave が 2026-08-09 01:34 に land) が
  `output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.py` を
  含みながら Codex `role=author` trailer を持たない (trailer は manager + researcher 2 本)。
  他セッションの履歴は書き換えない。`tools/dev_wave_land.py` の provenance 使用は fold message の
  preflight だけで全史監査ではないため、本 wave の land は塞がれない。**所見として起票する。**
- **段 8 の改善候補は 2 件、いずれも本文編集なしで記録のみとした。** (1) 受入 lease の待ち周期は
  30 秒にする — 60 秒 90 回 (本 wave) と 120 秒 40 回 (同日の別 wave) がいずれも全空振りし、
  30 秒の 2 本目が取得した。**独立 2 例が揃い `DW-G03` の族一般化条件は満たす**が、
  `docs/dev-wave/**` の空き 1 byte では本文へ入らないため memory
  (`acceptance-lease-poll-30s`) を正本とする ([T-641] (c) と同型、本 wave の [T-648] 処理と同じ形)。
  (2) worktree 隔離セッションで複合 shell (export + `$()` + heredoc) が harness の guard に
  拒否される件は、[T-594] が既に所有しており本 wave では起票しない (worklog 319 と同じ扱い)。
- 実装差分ゼロのため変異 matrix は免除 (`DW-S04` の免除条項)。子エージェントは起動していない
  (docs-only は子ゼロ、`DW-C00`)。

## 次の一手差分

### 新規

- {{T:t659-probe-missing-codex-author}} **P2・新規**: land 済み commit `2c192953` ([T-659] wave)
  が実装面ファイル (`output/insights/2026-08-09_t659-activation-deploy-window/verbatim/probe_split_window.py`)
  を Codex `role=author` trailer なしで含み、全史 provenance 監査が新規違反 1 件を返す。
  履歴改変を避ける処置 (forward-correction commit か known-violation 登録か waiver) を
  [T-659] wave 所有者が選ぶ。本 wave は検出のみで直していない

### 見送り

#### プロセス文書系

- [T-648] 受入免除判定の証拠記録義務の契約本文への明文化 — 理由: 義務は fallback
  (本エントリ + memory) で発効済みで、契約 1 文の追加は dev-wave docs 予算 (空き 1 byte) に
  入らない ([T-641] (c) 同型)。再訪 = [T-313] 実装などで `docs/dev-wave/**` 予算に空きが
  出たとき、本文 1 文への昇格を再検討する (2026-08-09 ユーザー裁定 (B') による再訪条件)。
  base: 054c83f5793e127d0adfaedab4d5b321d5fde9c1af920ce433a1f37c46a1c8ee
