---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t425-premise-refuted
seq: 1
title: [T-425] 裁定の前提を着手前実測が覆したので再裁定へ戻す (docs のみ、branch worktree-dev-wave-t425-premise-refuted)
---

## 本文

- D1264 の実装 wave として起動し、ユーザーが指定した着手前実測の停止条件が成立したため実装せずに
  終えた。コード・テストの差分はなく、Codex 実装子も起動していない。
- **親の初回報告のうち 2 点が誤りで、Codex 相談 2 レンズが独立に反証した。** (1)「A4 の現物は
  揃っている」は誤りで、A4 は readiness index が書くとおり `unmet` である。serial 2 が発行前に
  不在なのは正常だが、それは正常な未充足であって充足ではない。(2)「凍結側を g2 まで進める必要が
  ある」は誤りで、環境世代と凍結世代は別番号であり、正式 launch は
  `orchestrator/campaign/s8b_ratified_freeze.py` の `certificate-generation-scope` が
  `generation_number == 1` 専用に限定している。組む相手は凍結 g1 である。g2 まで進めると
  かえって拒否される。
- 実測で確定した事実。`output/s8b-freeze` 配下の v2 世代 file・approvals・active pointer・
  candidates はいずれも 0 件で、`git check-ignore` 非該当。`floor_protocol.json` は pegasus g1 契約に
  束ねられたまま。承認 record と有効 pointer の導入 commit は `AI-Agent: none` 逐語・非 merge を
  要求するため、A6 は AI だけでは完了できず最後に人間の commit が要る。
  `env_contract.py` と `env_contract_activation.py` から凍結側検証への import・呼出しは 0 件で、
  A6 は activation 経路へ機械的に結線されていない。
- **D1264 の決定部分は保てるが、理由が実測で覆った。** 同 D は「A5 / A7 が H1 / H2 を無期限に
  止めている本体」を理由とするが、A6 にも現物が無く人間承認も要る以上、A5 / A7 だけを置換しても
  律速が A6 へ移るだけで activation は進まない。D444 の床値 protocol 張替えだけで A6 を閉じるのは
  凍結側の承認を経ない近道であり、絶対規律 2 に触れるため採らない。再裁定はユーザーの手番であり、
  本 wave では decisions を改訂しない。
- 実効性レンズは D1265 (rr80 / rr20 の production projection を環境世代切替なしで着地) を
  当面の前進経路として挙げた。本 wave の依頼対象外のため着手していない。
- エージェント工数: Codex 相談子 2 本 (`consult` / `read-only` / `xhigh`、レンズは正しさ境界と
  実効性・整合)。いずれも rc=0 で `tools/check_codex_output.py` も rc=0。実装子・レビュー子は
  起動していない。

## 次の一手差分

### 更新

- [T-425] **P1・裁定の前提が実測で覆った → ユーザー再裁定待ち**: D1264 の決定部分 (A4 / A6 は
  必要条件として維持し、A5 / A7 の完成待ちだけを置換または非認証化する) は保てるが、理由の
  「A5 / A7 が律速の本体」は着手前実測で覆った。A4 と A6 の双方が `unmet` で、A6 は現物が皆無・
  activation 経路へ未結線・完了に人間 commit が必須である。再裁定で確定すべきは、A6 の proof を
  何と定義するか (凍結 g1 の承認済み successor で足りるか)、A4 / A6 / A7 の `unassigned` な
  remediation owner を工程別にどう割り当てるか、A5 / A7 を非認証化する際に「認証されていない」と
  明示する列と文言をどう固定するかの 3 点である。実装は再裁定後に再開する。
  base: 47b101c72eab6d9724afe470c54a973997481bd9605b78755bebddc7303ff0ca

### 新規

- {{T:freeze-g1-successor-prep}} **P2・新規**: 凍結側の下位実装を上位権限束設計の exact 正本へ
  適合させ (現行は approval と pointer を同一 commit に要求しており、設計が求める別 commit 構成と
  食い違う)、legacy v1 → 凍結 g1 の承認可能な successor を人間承認の直前まで用意する。AI が
  到達できるのはそこまでで、承認 record と有効 pointer の commit は人間の手番である。着手は
  [T-425] の再裁定で A6 の proof 定義が確定してからとする。確定前に始めると、作る対象が
  外れる可能性がある。
