# 段 1 brief — R5 resume / accounting closure

- 継承: 前 wave は `DW-O16` 3 巡上限で停止し、R5 の 2 consumer を real / scope 内 / must-fix と
  裁定した (`s6-focused-review-3.md`)。本 wave はこの 2 consumer だけを scope にする。
- ユーザー裁定 (逐語): 「codex はレートリミットが近いので claude で代替してください」。
  → 子 worker は Codex subprocess でなく Claude subagent を使う (D95 の author 要件の今回限りの置換)。
  凍結境界の他項 (親は実装面を直接編集しない / 実装子は docs・commit をしない / push しない) は不変。
- 前提実測 (静的、file:line で追認):
  - C1 = `tools/pegasus/test_dispatch.py:6555-6566` — resume の submit-receipt 分岐は matched
    `scheduler-lookup-result` を `job_id_normalized` だけで選び、同 WAL candidate の
    `group_name` / `user_name` / `request_name` / `queue` / `account` を再検証しない。
    非対称の対照は同ファイル `:4741` (WAL 復元側は policy へ全項照合済み)。
  - C2 = 同 `:3195 validate_nqsv_accounting` — footer の `Group Name:` を非空 `\S+` としか検査せず、
    `policy.account` と exact 比較しない。呼出は `:4404` (final 再検証) と `:5255` (monitor)。
  - `submit-receipt.json` (`izanagi-test-submit-v2`, `:2348`) は group を持たない。よって
    「receipt だけがあり matched WAL が無い」resume では group 情報がゼロである。
- 既存被覆と純増検出力: wrong-group は fresh lookup (`:3021`) と per-job qstat (`:2998`) で既に拒否
  され、`test_pegasus_test_dispatch.py:1070` / `:1717` が被覆する。resume 分岐と accounting footer の
  2 vector は未被覆であり、本 wave の純増検出力はこの 2 つだけである。
- O08/O09/O10: 対象 3 file を pin する `FROZEN_MANIFEST` / generator hash pin は無い
  (`grep -rn --include=*.py`)。v2 active generation も official floor 受理集合も空のままで、
  凍結 bytes の再発行対象は無い。proof chain・oracle gate の入力形式は変更しない。
- O13 (gate 入力の実在): `Group Name` は実 probe `874129.nqsv` の accounting footer と qstat -f 出力に
  実在し、fixture (`test_pegasus_test_dispatch.py:400-`) はその形を写している。`policy.account` は
  `tools/pegasus/test_dispatch_policy.json` の `"account": "SFC"` に実在する。同名識別子の二義化なし。
- 不変条件: 受理集合の縮小は wrong-group 経路だけとし、same-group の正常 dispatch / resume /
  accounting は現行どおり受理する。frozen bytes、trace 分離、proof chain、非 Pegasus 挙動、
  push 境界、既に closed の R1〜R4・R6〜R9 の挙動を変えない。
- 成果物影響 (DW-G05): 未実装なら wrong-group の既知 job が resume で受理集合へ入り monitor/qdel の
  対象になり、wrong-group accounting を含む dispatch receipt が `CHILD_RESULT` として封印される。
  実装後はどちらも fail-closed で拒否され、receipt に拒否理由が残る。
- 成果物の形: `test_dispatch.py` の 2 経路の exact 比較 + `test_pegasus_test_dispatch.py` の
  expected-red 2 件と same-group positive control 2 件。docs は親が書く。
- (P1) C1 は「WAL candidate を policy へ全項照合する」で閉じる。receipt しか無く group 証拠が
  ゼロの resume は、monitor/qdel の前に per-job qstat の group 検証を要求して fail-closed にする。
- (P2) C2 は `validate_nqsv_accounting` に `expected_group` を必須引数で足し、両呼出へ
  `policy.account` を通す。`validate_final_receipt_object` は既定値なしで expected_group を受け取る。
- (P3) 既定値・後方互換の省略引数は作らない (省略が wrong-group 受理に戻る穴になるため)。
  P1〜P3 は親の provisional 裁定であり段 3 の攻撃対象。
- 分割: C1 と C2 は同一 file (`test_dispatch.py` と同一 test file) を編集するため所有が素集合に
  ならない。単一実装単位 U5 とする (DW-S06-B の単一化理由)。
- 受入・実測環境: Pegasus gen_S 計算ノード (`qsub`)。ログインノード `pegasus02` では pytest / build /
  qsub 実体を走らせない (D103)。所在の正本は worklog。
