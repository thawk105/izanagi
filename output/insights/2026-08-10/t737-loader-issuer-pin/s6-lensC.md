結論は **NO-GO**。親の 83 passed は通常系の実測であり、以下の変異上の欠陥を解消しない。こちらでは pytest・変異とも未実走。

### C-01 — loader 2 node は量化点の semantic kill にならない（must-fix / real・静的確認）

- file: [test_env_contract_activation.py:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:82)、[test_env_contract_activation.py:1659](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:1659)、[env_contract.py:535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/campaign/env_contract.py:535)、[s4-adjudication.md:108](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s4-adjudication.md:108)
- G/P を `[:N]` へ縮退すると leaf validation は通るが、直後の `_verify_entry_calibration()` が `output/synthetic-activation/...` を検証する。この directory は現 worktree に存在せず、`current_activation_state()` は別の `EnvContractError` で引き続き拒否する。
- したがって loader G/P node が赤くなるのは `activation authority 検証失敗` 等の message assertion が変わるためであり、production-loader の受理集合は反転しない。DW-M03 上は KILL ではなく diagnostic sensitivity。
- spec A の G 4 node中 loader 2本、P 2 node中 loader 1本を KILLED と数える事前登録は成立しない。変異は未実走。
- 成果物影響: 有効な calibration を持つ不正 transition が loader を通る変異を未拘束のまま、変異台帳とレポートが「loader でも KILLED」と誤記し、certified 選択の contract 世代参照を過大保証する。
- 修正案: G用・P用に terminal generation だけ実在する grandfathered calibration ref を使う別 registry を作り、縮退後に `_load_authority_snapshot()` 全体が成功する fixture にする。代替は loader node を diagnostic sensitivity へ降格し、semantic kill を別 node で追加する。

### C-02 — issuer 変異時の赤理由が downstream handoff 例外へ逸れる（must-fix / real・静的、変異未実走）

- file: [test_env_contract_activation.py:2328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:2328)、[issue_env_contract_activation.py:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/tools/issue_env_contract_activation.py:143)
- 負例は `issuer.__file__` を実 repo のままにする。G/P 縮退後は validation が通り、tmp authority へ record を publish した後、`issued.relative_to(real_repo_root)` が `ValueError` になる。
- `finally` の実 authority 名検査は走るが、その後の `SystemExit.code`、stderr、`assert not published` は実行されない。これは実際に publish へ反転するため diagnostic-only kill ではないものの、赤理由と publish postcondition が単一に観測されない。
- 成果物影響: 変異台帳は `_activation_handoff` の `ValueError` を expected-node KILL として記録できてしまい、レポートの「issuer が publish を防いだ」という参照が未評価 assertion を指す。
- 修正案: `_write_create_only` を spy/wrapper 化し、負例では「呼ばれた」こと自体を副作用なしで失敗させる。併せて handoff を tmp repo 内で完結させ、writer 到達・対象 directory・publish 不在を `finally` で一意に観測する。

### C-03 — real-authority guard は名前集合しか守らない（realな検査範囲欠落、現行 exploit は未成立）

- file: [test_env_contract_activation.py:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:245)、[test_env_contract_activation.py:2349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:2349)
- `_entry_names()` は bytes・file type・別 checkout/path・authority 親の staging residueを見ない。既存 entry の同名置換や別 path への publish は集合比較を通る。
- 現 production の `_write_create_only` は no-replace なので、同名 bytes 改変は現 snapshot の通常経路では到達不能。`sys.modules` 欠落や guard 自身の例外は node を赤にするため、green bypass にはならない。
- 成果物影響（条件付き推測）: import/write 経路が drift した場合、別 authority の bytes または head chain が変わっても guard が緑となり、その checkout の certified report・台帳が未審査 activation を参照しうる。
- 修正案: writer の対象 path を呼出し前に強制し、実 authority は `{name, file type, sha256}` で前後比較する。負例は writer を実行させない。

静的に成立を確認できた点:

- `range(1, 4 if index == 64 else 3)` は最後だけ g1/g2/g3、他は g1/g2。ゼロ埋め tag、`sorted()`、`_chain()` の zip により `(2,)*64 + (3,)` は確実に `pin-env-064` へ対応する。
- `_use_authority` は cache clear 後に `current_activation_state()` → `_load_authority_snapshot()` → `load_activation_state()` → G/P へ到達し、終了時にも cache を捨てる。現順序での global/cache 漏れは見つからない。
- import-time registry は決定的で I/O を行わず、xdist worker 間では process 分離される。揮発する working-tree hash の焼き込みもない。
- plan v2 からの有意な実装逸脱はない。post guard を `finally` に置いた点は強化。C-01/C-02 は author の逸脱ではなく、plan v2 自体の見落とし。

## 総括

(a) must-fix はある。C-01 は loader の kill 主張を直接無効化し、C-02 は issuer の変異理由・publish 証拠を非一意にする。

(b) **NO-GO**。現状では「2層で量化点を semantic kill した」と記録して land できない。

(c) 親は calibration-valid loader fixture で G/P 変異を再走し、別拒否でなく state 受理へ反転すること、issuer は writer 到達/pathを明示観測することを確認すべき。`ident` 未被覆と loader正例が leaf止まりという裁定上の限定も維持すること。