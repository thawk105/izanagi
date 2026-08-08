---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-t530-contract-hash-binding
seq: 3
---

## 新規

### {{F:dual-module-identity-across-test-and-production}}. 同じファイルが 2 つの module object として読まれ、exact 型検査を跨ぐ値が弾かれた [手順漏れ] [テスト代表性]

- 事象: fix 子が新設したテスト helper が `type(x) is not Y` の exact 型検査に落ち続けた。
  引数は正しい型の実体だが、test file が `orchestrator.campaign.build_admission` から、
  production が `campaign.build_admission` から同じクラスを取っていたため、クラスの実体が
  2 つあった。同じ原因が引数を変えて 2 巡連続で再現し、fix 2 巡ぶんを空費した。
- 根本原因: `orchestrator/` は `campaign.X` と `orchestrator.campaign.X` の両方で import できる。
  exact 型検査 (`is not`) を跨いで値を渡すテストは、production と同じ module 経路から
  オブジェクトを取らなければならないが、その規律がどこにも書かれていなかった。
  production 側 (`p3_autonomous_workload_trial.py` の import 直前コメント) は
  「同一 module identity 上に揃える」意図を明記していたのに、テスト側には伝わっていなかった。
- 恒久対応: `docs/dev-wave/workers.md` の `DW-S05-C` が実装子プロンプトへ入れる項目として、
  「exact 型検査を跨いで production へ渡す値は production module 自身の namespace
  (`A.env_contract` 等) から取る」を追加する。
- 再発検知: 同型は `type(...) is not ...` を持つ production 関数へテストが直接値を渡す箇所で
  起きる。fix 3 巡目で同型の全走査を子に要求し、取り残しゼロを静的に確認した。

### {{F:codex-auth-expiry-mid-wave}}. wave 途中で codex のサブスクリプションログインが失効し、実装面の続行が不能になった [観測] [手順漏れ]

- 事象: 段 6 の fix 5 巡目を投入した瞬間に codex が 401 Unauthorized を返し、
  出力ファイルを 1 byte も作らずに rc=1 で終了した。`codex login status` は `Not logged in`。
  実装面は Codex author 必須のため親は代行せず fail-closed で停止し、ユーザー手番へ返した。
- 根本原因: サブスクリプションログインの失効は wave の進行と無関係に起こるが、
  `DW-O01` は起動レシピと採用条件だけを持ち、**走行中の認証失効時にどう振る舞うか**を
  書いていない。`docs/ai-provenance.md` の D105 は Codex 不可用時の waiver 手順を定めるが、
  入口の条件 dispatch からは辿れない。
- 恒久対応: `docs/dev-wave/operations.md` の `DW-O01` へ、認証失効は fail-closed 停止とし、
  親が実装面を代行せず、再投入は新しい artifact 名で行う旨を追加する。
- 再発検知: 失効時は `-o` の出力ファイルが生成されないため、
  `tools/check_codex_output.py` が「対象を開けない」で必ず非 0 になる。
  この rc を採用条件として扱っていれば、無出力を成果と誤認する経路はない。
