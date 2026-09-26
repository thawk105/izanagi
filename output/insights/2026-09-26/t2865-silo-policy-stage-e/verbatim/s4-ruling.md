# 段 4 裁定 — [T-2865] 段階 E (2026-09-26 19:4x JST、親)

入力: brief.md、codex/s2-plan.md、codex/s3-consult-{A,B,C}.md (3 本とも adopt_with_conditions)。裁定 inbox 再走査: 第 36 回 (D2249) は T-2865 の E を変えない (`.claude/agents/` の具体差分は提示の段でユーザー確認、を再確認)。local main は docs のみ 2 commit 前進 (265cce13c)。

## 所見の裁定

| 所見 | 判定 | 採否 |
|---|---|---|
| 共有 `quarantine()` への追加が C/D 診断経路を壊す・二重化する (A1・B1・C1) | real | 採用。**P1 を撤回**: `p3_s4_loop.quarantine()` は変えない。driver 側の方策専用 gate が `L.quarantine(..., marker_id=axis.MARKER_ID, write=False)` (構造 + effect) → `silo_policy_compile.check_policy_body` (構文 → 単独 TU) を順に呼ぶ。`silo_policy_coverage.prepare_policy` と段階 C/D の経路は不変 |
| `prior_critic_reverse` の自己申告 (A3・B3・C4) | real | 採用。proposal から除く。停止は予算 (iteration・walltime) だけ。reverse は E で接続しない |
| JSON 重複 key と scalar 型 (B2・C3) | real | 採用。proposal file を読む最外層で `object_pairs_hook` により全階層の重複 key を拒否。全 scalar を exact 型 (bool は int と区別)・値域で検査 |
| auditor 型上限の全域拡張 (C2) | real | 採用。`auditor_gate` の上限を呼出し側の引数にし、既定は 21 のまま。policy driver だけ 26 を渡す |
| 自系列の境界・入力 path (A2・B4・C5) | real | 採用 (縮小形)。形 (C++ / IR) を search_config に焼き、形ごと・系列ごとに別 campaign。coder 入力は driver の 1 関数が固定 path の projection.json と当該 campaign layout 内の履歴 file だけから組む。path を引数で受けない。禁止 path の open 監視や他 file 改変時の bytes 比較は足さない |
| build admission の実経路固定 (A4) | real | 採用 (最小)。driver が review / generator receipt を渡さず、CLI opt-in 無しで LLM 候補の build が拒否されることを test で固定 |
| preview・auditor・書込・build の byte 束縛 (A5) | real | 採用。preview と run が同じ render + gate 関数を使い、全 gate と auditor digest 照合の後にだけ書き、書いた本文から digest を再照合してから `run_campaign` へ |
| M-E4 は kill でない (A6・B5・C7) | real | 採用。subtype の変異は diagnostic sensitivity pin に分ける |
| auditor 免除の限定 (A7) | real | 採用。型 17〜21 の免除を「sort IR と、この軸の機械生成 IR 候補」に限り、LLM×C++・LLM×IR は監査すると本文とチェックリストの両方に書く |
| IR codec の往復 (B7) と serializer の要否 (C) | 一部 real | parser だけ新設 (`parse_policy_ir`)。serializer は用途が無いので作らない。各 node / hook の exact key 集合と、全 node 種の正例・負例を test で固定 |
| live 確認 (P8) — 手書き 2 形の計算ノード実走と job body (B6・C6) | C6 を採用、P8 を撤回 | E の完了条件から外す。新 driver 用の計算ノード job body も E では作らない。F の前提 (AI 側の carry) として insight と次の一手に書く |

## plan v2 (所有は素集合)

- **単位 A** — `orchestrator/campaign/silo_policy_ir.py` に `parse_policy_ir(document: object) -> PolicyIR` を追加 (tagged object、exact key、exact 型、未知 kind・範囲外は `ValueError`、最後に `validate_ir`)。`orchestrator/tests/test_silo_policy_ir.py` に全 node 種の正例・負例。既存の dataclass・`validate_ir`・`render_policy`・列挙は変えない。test fixture に偵察の点 ID・因子は使わない。
- **単位 B** — `orchestrator/campaign/auditor_gate.py` の violation type 上限を keyword 引数化 (既定 21、挙動不変)。`orchestrator/campaign/projection_guard.py` に planner なしの契約 `policy-cpp` / `policy-ir` を追加 (top required `{coder, auditor}`、optional なし、`planner`・`value`・`prior_critic_reverse`・`strategy_summary` は未知 key として拒否。既存契約の集合は不変)。`orchestrator/campaign/diff_quarantine.py` の subtype に `policy-grammar` / `policy-compile` を追加 (既存 subtype 不変)。対応 test (`test_auditor_gate.py`・`test_projection_guard.py`・`test_diff_quarantine*.py` の該当箇所に追加。既存期待値は変えない)。
- **単位 C** — `orchestrator/campaign/p3_s4_loop_policy.py` 新設と `orchestrator/tests/test_p3_s4_loop_policy.py`。
  - 軸定数は `axis_silo_function_policy` から import。PIN = `axis.PIN`。worktree 隔離は既定 ON。
  - `default_cfg`: `VERIFY_LEGACY_PLUS_PERFORMANCE`、性能構成は `p3_s4_loop` の較正 write-heavy 動作点 (plan の `calibrated_perf("write-heavy")`)、search_config に形 (`cpp` / `ir`) を焼く。
  - 方策 gate: C++ 本文 (IR 形は parse → `validate_ir` → `render_policy` の後の本文) を `L.quarantine(write=False)` → `check_policy_body` → auditor verdict の digest 照合 (`apply_mandatory_deny_only_veto`、上限 26) の順。拒否は `L.record_diff_reject` の既存 WAL 経路 (subtype と rule id を載せ、compiler 診断全文は載せない)。全 pass 後に書き、digest を再照合。
  - proposal loader: 最外層で重複 key 拒否 → `assert_closed_proposal_schema(coder_contract=policy-cpp|policy-ir)` → scalar の exact 型・値域 → IR は `parse_policy_ir`。
  - build admission: sort と同じ登録済み coder entrypoint と `--allow-coder-derived-build` の CLI opt-in、`CODER_AUTHORED`。review / generator receipt を渡さない。
  - 停止: `L.check_stop` を空 whiteboard で使い予算だけで止める。`LoopState` に field を足さない。
  - 履歴: 当該 campaign layout 内の 1 file (JSONL) に iteration・variant id・本文 (C++ 形は本文、IR 形は IR object と描画本文)・結果分類・reject subtype / rule id・verifier の構造化 digest・justification を書く。
  - firewall: `make_policy_coder_input(layout, *, baseline, critic_diagnosis=None)` 1 関数。projection.json は module 定数の固定 path、top key `{binary, scope, excluded}` 完全一致・`binary` は exact bool・`scope` は str を検査し、`recon_projection = {binary, scope}` だけ出す。履歴は同 layout の file だけを読み、justification を落として射影。critic_diagnosis は閉じた固定 field の object だけ受ける (自由 key は拒否)。自由文 `scope` の内容保証は主張しない。
  - CLI: `--preview-diff` (C++ / IR)・`--run-iteration`・`--no-build`・`--no-isolate-worktree`・`--allow-coder-derived-build`・coder 入力を出力する `--emit-coder-input`。critic digest の tag / file 名は本軸専用。
  - B-4・sort oracle・trigger wire・K2 knowledge は持ち込まない。規模の目安は sort driver (895 行) 以下。
- **単位 D** — `.claude/agents/coder-v4-autonomous-policy.md` (C++ 形)、`.claude/agents/coder-v4-autonomous-policy-ir.md` (IR 形) 新設、`.claude/agents/auditor.md` 改訂 (型 22〜26、免除の限定、チェックリスト)、`orchestrator/codex_roles/` (manifest.json・review_ledger.py・policy.py・spec.py の必要箇所)・`.codex/role-adapters/`・`tools/check_codex_agents.py`・`.codex/agents/README.md`・`orchestrator/tests/test_codex_agents.py` の追随。role 本文に具体戦略の例示・偵察結果・既知最良・小比較の情報を書かない。**統合はユーザー明示承認の後だけ** (承認前は子 worktree に置き、差分を提示する)。
- **親 (docs)** — runbook `docs/phase3-silo-policy-runbook.md` (sort runbook の 5 節骨格、planner 段なし、C++ / IR の分岐、F の前提として job body が未作成であることを §0 に明記)、`docs/README.md` の地図、insight・fragment。

依存: A・B 並列 → C (A・B 統合後) と D (C の schema を plan v2 で固定済みなので C と並列) → 統合 → 段 6。

## 変異の事前登録 (実装後に単一理由性と期待 node の完全集合を確定、DW-M01 / M08)

| ID | 壊すもの | 期待して落ちる test (名は実装で確定) | 区分 |
|---|---|---|---|
| M-E1 | driver の方策 gate で `check_policy_body` の構文拒否を受理扱い (grammar のみ拒否し g++ は通る本文 = 自己初期化などの fixture) | 構文拒否が TU・auditor・書込より先に止める test | kill |
| M-E2 | 単独 TU compile の拒否を受理扱い (構文は通り TU だけ落ちる fixture。存在しなければ登録を外す) | TU 拒否が auditor・build より先に止める test | kill |
| M-E3 | auditor digest 照合を外す | digest 不一致で `AuditorGateFailure` の test | kill |
| M-E4 | policy driver が渡す auditor 型上限を 21 に | 型 22〜26 の policy verdict の受理 test | kill |
| M-E5 | `auditor_gate` の既定上限を 26 に | 既定 (sort) で型 22 を拒否する既存 test | kill |
| M-E6 | IR parser の未知 key 拒否を外す | IR codec の未知 key 負例 | kill |
| M-E7 | IR parser の exact 型を `isinstance(x, int)` に (bool が通る) | IR codec の bool 混同負例 | kill |
| M-E8 | proposal loader の重複 key 拒否を外す | 重複 key 負例 | kill |
| M-E9 | coder 入力に `excluded` を加える | firewall の key 集合 test | kill |
| M-E10 | 履歴射影に justification を加える | firewall の justification 不在 test | kill |
| M-E11 | `default_cfg` の verify を legacy+s2 に | cfg 配線 test | kill |
| P-E1 | reject subtype を別名に | WAL / critic の subtype test | diagnostic pin (kill に数えない) |

## 計算

E の完了条件から live 実走を外したので、計算ノードは焦点走と受入だけ。見積りは受入 1 回 ≈ 0.25 node 時間 (実測単価、記憶) + 焦点走 数回 × 数分 = 約 0.3〜0.5 node 時間で 2 node 時間未満 (図は作らない)。変異 matrix は投入前に同 argv の 1 job で単価を測る。

## 研究前進 (brief からの修正)

完了判定 (1) の「pipeline.evaluate へ通す」は、`--no-build` の配線確認と fixture test までとする。実走 (build・verify・bench) の最初の証拠は F の実 LLM 1 iteration。
