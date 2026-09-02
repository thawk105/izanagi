---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t2159-c05-schedule-authority
seq: 1
title: [T-2159] C05 の schedule 正本は実装せず裁定へ返した — 権威のない仕様 4 件と、D1448 の前提の欠落 (docs のみ、branch worktree-dev-wave-t2159-c05-schedule-authority、実装面の差分 0)
---

## 本文

- **裁定 D1448 の実装に着手したが、実装しないと裁定した。** 段 3 の 2 レンズが別々の主題
  (受理集合と恒真化 / 権威の出所と順序裁定との抵触) から独立に同じ結論へ達し、親が一次資料と
  実測で裏を取った。一次資料は `output/insights/2026-09-02_t2159-c05-schedule-authority/`。
- **理由 1: 権威のない仕様を 4 件その場で決めることになる。** schedule authority 18 field の
  `whiteboard` 受理規則・`leakproof_context` の包み方・`descriptor_binding` の表形式、および
  事前登録 §5 の予算欄へ足す cell ごとの予約値。schedule の hash はこの形から決まるので、
  実装が決めた形を実装が検証する構図になる。18 field の名と型対応が D530 の裁定範囲外で
  実装著者の選択だったことは、先行 wave が記録に残している。
- **理由 2: D1448 の前提が不完全である。** `registered-effective` の admission は発効済み事前登録を
  要求し、発効は 12 述語すべての充足を要求する。`_evaluate_c05` は全条件を満たしても終端が
  `EVIDENCE_UNDEFINED` で、`SATISFIABLE_CONDITION_IDS` が C10 以外の SATISFIED を ERROR へ倒す。
  **本件を実装しても正式起動は 1 ビットも近づかない。** 共有 8b ratified freeze も未発効のまま。
  D959 が同じ経路を「上流に従属する下流症状であり順序を入れ替えて先に解除してはならない」と
  定めているが、**D1448 の裁定文にも 1184 の該当行にもその言及がない。** DW-S04 に従い
  不採用にせず、新事実を添えてユーザー再裁定へ返す。
- **先行 wave が「3 矛盾」と記録した点は、実測では 1 件だけだった。** `leakproof_context` は
  射影で解け、`descriptor_binding` は型としては通る。production 実値で `validate_authority` を
  落とすのは `whiteboard` の空配列 1 件だけである。**この 1 点が実装の前提を閉じている。**
- **runbook の stale 記述を訂正した。** 「12 述語の SATISFIED が 0 件」は誤りで、実測は
  C10=SATISFIED、C03=UNSATISFIED、残り 10 件=EVIDENCE_UNDEFINED である。
- **棄却した所見:** (a)「D549 と D992 が本 wave を禁じる」— D549 が保留したのは artifact と §5 の
  同時発行で本 wave は触れない。D992 の主文は凍結 spec の producer/lifecycle に限る。効いているのは
  D959 の順序規定だけである。(b)「プランの現行値が親実測と矛盾する」— 一方は artifact を注入した
  反実仮想で、別の状態の値であり矛盾しない。
- **親の誤り 1 件を訂正した。** 段 1 brief の実アンカー表で
  `test_p3_autonomous_workload_trial.py:9053` を「現状の raise を固定する test」と書いたが、
  実際は loader を成功 lambda へ差し替える monkeypatch で、無条件 raise を pin するテストは無い。
  段 3 レンズ A が指摘し、親が現物で確認した。裁定の向きは変わらない。
- **セッション異常:** worktree を作った直後の HEAD が local main でなく別稼働 wave の branch tip
  だった。開始 gate が「332 commit 遅れ」で捕まえ、local main へ据え直して rc=0。
  `tools/dev_wave_submodule_init.py` の初回呼び出しも checkout 競合で rc=1 になり、再実行で rc=0。
- **エージェント工数:** 段 2 プラン 1 本、段 3 敵対相談 2 本 (並列)。実装子は起動していない。
- **段 8 の候補 1 件は収容できず「実施しない」へ落ちた。** 受入 tool は `--receipt-file` と
  `--log-file` が必須だがどちらも DW-O27 に書かれておらず、tool 自身も `--help` を出さないため、
  初回投入が `cli-usage` rc=2 で落ちた (実測)。DW-O27 へ 1 行足すと単節予算 1000 bytes を
  111 bytes 超過する。D782 が指す D730 の手順を適用したが、意味を弱めない削減で作れる余地は
  約 30 bytes、独立 3 例の例外収容も 1 例目のため未達、上限引き上げは 1 件では不相応と判断した。
  **同じ欠落を次に踏んだ wave がこれを 2 例目として数えられるよう、事象だけ記録する。**
- 実装面の差分が 0 なので変異 matrix は免除 (DW-S04)。受入全走は免除せず親が実走した。

## 次の一手差分

### 更新

- [T-2159] **P2・裁定済み → 実装前にユーザー裁定が要る 5 件へ差し戻し**: C05 の schedule 正本は、
  次が決まるまで実装しない。(1) 順序 — D959 の「上流を先に解く」を D1448 が明示的に上書きするか
  (親の推奨: 上流の許可リスト側を先に片付ける)。(2) `whiteboard` の扱い — authority から外す /
  空を表現できる版付き schema へ改訂する / 呼び手供給のまま据え置く (親の推奨: 2 番目)。
  (3) cell ごとの予約値の置き場所 — 事前登録 §5 の予算欄か 6 cell manifest か
  (親の推奨: manifest。あわせて規範が要求する arm 上限の対称性と holdout 上限の和の一致を
  予算 consumer へ入れる)。(4) 予算台帳の正本 path。(5) schedule 行 hash の正本形。
  根拠と実測は `output/insights/2026-09-02_t2159-c05-schedule-authority/`。
  base: 0c4ba519e15573a23dcb3d9e0225e080ad2c5d425c4a040af88dc6efa0235d29

### 新規

- {{T:schedule-row-hash-binding}} **P2・新規・実装待ち**: 試行 slot の `schedule_row_sha256` を
  C05 の schedule と結線する。現行の検査は slot 自身が記録した値を読み返すだけで、schedule
  artifact から当該 hash を導く producer が存在しない。preimage の正本形を定めて genesis producer と
  同じ digest で照合する。着手は [T-2159] の択一 5 のあと。
- {{T:zero-reservation-vacuity}} **P2・新規・実装待ち**: 全 cell の予約値 0 が `held` として受理され、
  予算保証が恒真化する。`_check_limit_state` は「予約の和 ≤ 上限」しか見ない。事前登録の規範が
  要求する arm 上限の対称性と holdout 上限の和の一致も検査されていない。実測は
  `output/insights/2026-09-02_t2159-c05-schedule-authority/` の §5。
- {{T:schedule-budget-verify-order}} **P3・新規・実装待ち**: schedule と予算の検証位置が、
  attempt slot の予約・分類・lifecycle 開始より後にある。「実走前に固定・検証」の失敗境界に
  なっていない。前倒しは起動順を変えるので、着手は [T-2159] の択一が片付いたあと。
