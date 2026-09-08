---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2437-record-issuer
seq: 1
---

## 新規

### {{F:mutation-blocked-by-source-closure}}. enforcement source closure に載る file は変異検査で帰属できない [テスト代表性]

- 事象: [T-2437] の変異 probe で、`loop.py` と `pipeline.py` へ入れた 8 変異がいずれも
  8〜10 node を落とした。落ちた node は狙った負例ではなく、campaign を構築する test の全体だった。
  同じ probe で `reflux_result_evidence.py` へ入れた 6 変異は 0〜4 node だけを精密に落とした。
- 根本原因: `campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` (exact 63 path の enforcement
  source closure) に `loop.py` / `pipeline.py` / `ident.py` / `wal.py` などが含まれる。
  変異 harness は固定 commit の worktree へ一時変異を注入するため、disk bytes が HEAD blob と
  乖離し `contract-loader-drift` が**狙った関門より先に発火する。**
  DW-M01 (F820) が禁じる「同じ入力を拒否する層が前後にある」状態であり、KILLED になっても
  その関門の実効性を示さない。期待 node に drift 由来の赤を含めれば形式上は完全一致するが、
  それは**偽の KILLED を台帳へ残す**ことになる。
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M01` に従い、閉包内 file への変異は**登録しない。**
  当該 file に置いた関門の実効性は変異ではなく負例そのもの (拒否 node 群) が担保する、と
  insight の限界節へ明記する。判定手順は「変異先 file が
  `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` に含まれるか」を段 4 の事前登録前に確認する。
- 再発検知: probe 走で 1 変異が 5 node 以上を落としたら、まず落ちた node の assertion 本文に
  `contract-loader-drift` が含まれるかを見る。含まれるなら帰属不能として登録から外す。

### {{F:early-return-does-not-guard-argument-evaluation}}. helper 内の早期 return は呼び出し側の引数評価を防げない [恒真ゲート]

- 事象: [T-2437] で `_issue_campaign_result_evidence(...)` の helper 冒頭に
  `if context is None: return` を置き、「発行 context が無い既定経路では何もしない」と設計した。
  しかし Python は呼び出しの前に引数を評価するため、既定経路でも
  `authorized_contract.contract_sha256` と `r.build_attempt_id` を読み、
  代用 object を渡す既存 3 node が `AttributeError` で落ちた。
  子の自走検査ではこの 3 node に到達できず (別の既知赤で停止)、親が commit 後の焦点走で初めて検出した。
- 根本原因: 「使わないときは何もしない」を helper の内側だけで書いた。
  無効化の意図は helper の本体にあるが、副作用 (属性アクセス) は call site の引数式にある。
- 恒久対応: 既定経路の不変を守る guard は **call site を囲む**。
  helper 内の早期 return は残してよいが、それだけでは防護にならないことを code comment に書く。
  再発を落とす負例として、属性アクセスで例外を投げる番人 object を既定経路へ渡す node を置く
  (`orchestrator/tests/test_reflux_campaign_issuer.py` の
  `test_originless_campaign_does_not_evaluate_issuer_only_attributes`)。
- 再発検知: 上記の番人 node。guard を外すと確実に落ちる (段 6 の焦点再レビューが確認)。

### {{F:gate-checks-presence-not-authenticity}}. 関門が「あるか」だけを見て「本物か」を見ない [恒真ゲート]

- 事象: [T-2437] で「execution receipt が無ければ発行を拒否する」という関門を置いたが、
  実装は `type(x) is dict` と `contract_sha256` の一致しか見ておらず、**条件に合う任意の dict が通った。**
  repo には権威検証器 `execution_guard.receipt_matches_contract()` が既にあったのに、
  発行側からの参照が 0 件だった。中心正例も、本番では作られない受領証を合成してこの穴を通り緑になっていた。
  さらにこれを直した後も、**検証の分岐を呼び手が自己申告できた** —
  required 契約から作った v1 receipt に `attestation_mode="none"` の札を付けると検証が `True` を返す
  (焦点再レビューが述語を実際に評価して確認)。
- 根本原因: 関門の入力を、呼び手が渡す自己申告の値から取っていた。
  存在検査と真正性検査を区別せず、権威ある検証器が既にあることを調べなかった。
- 恒久対応: 発行側は**解決済みの契約実体**を必須入力として受け取り、
  検証器へ渡す `env_tag` / `attestation_mode` / digest を契約から読む。
  関門を新設する前に、同じ性質を検査する既存の権威関数が repo にあるかを検索する
  (CLAUDE.md 規律 3。設計判断は {{D:result-evidence-production-issuer}})。
- 再発検知: 変異 m7 / m7b / m7c (`mutation/mutation-final-spec.json`) が 3 層それぞれを単独で pin する。
  本走で KILLED 3 / 3、期待 node 完全一致。
