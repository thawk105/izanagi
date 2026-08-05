## must-fix

### 1. `critic/digest.py` の直接実行は nominal type の二重ロードで壊れる

- **(a) 何が壊れるか:** 文書化されている `python3 orchestrator/critic/digest.py --campaign-dir ...` では、実行中の `IdentityProjection` は `__main__.IdentityProjection` だが、factory が返すのは再 import された `critic.digest.IdentityProjection` である。`isinstance()` が偽になり、正規 campaign から critic digest を生成できない。
- **(b) 根拠:** [`digest.py:25`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:25)、[`digest.py:630`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:630)、[`digest.py:792`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:792)、[`p3_s4_loop.py:74`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:74)、[`.claude/agents/critic.md:13`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/.claude/agents/critic.md:13)。
- **(c) 最小の是正案:** `IdentityProjection` を第三の中立モジュールへ移して双方から import するか、CLI を必ず canonical な `critic.digest` 側へ委譲する。文書どおりの直接コマンドを実行する回帰テストを追加する。

**成果物影響:** WAL の certified 選択自体は不変でも、critic digest とそこから作る材料レポートの参照が生成不能になる。

### 2. 異なる wire/report 形状を同じ `v2` として発行し、reader は新 field を無検査で receipting する

- **(a) 何が壊れるか:** 同一 schema version のまま、role payload が `variant` から `candidate_label` に変わり、digest 欠落値が文字列から `None` に変わり、report 内 role event に `declassifications` が増えている。一方 completeness は同 field の存在・型・policy・role 別制約を一切検査しない。既存 v2 は読めるが、新 v2 の欠落・任意値も黙って受理する fail-open である。
- **(b) 根拠:** [`p3_autonomous_workload_trial.py:142`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:142)、[`p3_autonomous_workload_trial.py:941`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:941)、[`p3_autonomous_workload_trial.py:1744`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1744)、[`p3_autonomous_workload_trial.py:1754`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1754)、[`autonomous_trial_completeness.py:183`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/autonomous_trial_completeness.py:183)、[`autonomous_trial_completeness.py:450`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/autonomous_trial_completeness.py:450)、[`trial_registry.py:2390`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/trial_registry.py:2390)。既存方針も role payload の意味変更には bump を要求している（[`decisions.md:5647`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/decisions.md:5647)）。
- **(c) 最小の是正案:** role/report schema を v3 に上げ、reader を version-aware にする。旧 v2 は legacy branch で読む。v3 は `declassifications` の存在、list/object 型、policy literal、digest、auditor 以外は空であることを検査する。

**成果物影響:** formal receipt が `declassifications` 欠落・捏造 report を完全と判定し、同じ schema ID の下で試行台帳の report/journal hash が異なる意味を指す。

### 3. pseudonym を依然として `variant=` と表示しており、WAL 識別子との参照整合が壊れる

- **(a) 何が壊れるか:** JSON payload は `candidate_label` に改名したのに、critic digest の verify・liveness・diff・abort 表示は `variant=candidate-0001` のままである。読者や critic は campaign-local pseudonym を WAL の raw variant と誤認する。
- **(b) 根拠:** [`digest.py:642`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:642)、[`digest.py:687`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:687)、[`digest.py:725`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:725)、[`digest.py:767`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:767)、対して [`p3_autonomous_workload_trial.py:1754`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1754)。
- **(c) 最小の是正案:** critic-facing renderer の表示名を全経路で `candidate_label=` に統一する。RAW projector は値を raw のまま返しても、field 名で wire identity と区別する。出力に projected label を `variant=` として含めないテストを置く。

**成果物影響:** 材料レポートが WAL に存在しない `candidate-XXXX` を variant として引用し、certified/rejected candidate の参照先を誤る。

### 4. M11・M12・M15 の変異帰属が段4裁定を満たしていない

- **(a) 何が壊れるか:** 一意 anchor の文字列一致だけを確認しており、原子的変異と指定テストへの帰属が成立していない。

  | 変異 | 静的判定 |
  |---|---|
  | M1 | anchor は一意。指定 relation test の kill 経路はあるが、その baseline が既知の赤なので attribution は未確定。 |
  | M2–M10 | 各 anchor は一意で、対応 channel assertion に直接到達する。 |
  | M11 | `render_rejections()` と `make_critic_digest()` の二つの signature を一変異として登録している。atomic でないため M11a/M11b に分割が必要。 |
  | M12 | `tag` と `reflux` の二項を一度に消す compound mutation。さらに anchor は trigger consumer だけで、autonomous re-render consumer を網羅していない。 |
  | M13 | anchor は一意で、登録済み ID の正方向テストに到達する。 |
  | M14 | anchor は一意。ただし裁定どおり diagnostic pin である。 |
  | M15 | 指定テストは composite detector assertion より先に source-file SHA assertion で落ちる。golden term による kill と帰属できず、artifact acceptance にも接続していない。 |

- **(b) 根拠:** 段4の M1–M15 定義は [`s4-adjudication.md:64`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-p2-noninterference/s4-adjudication.md:64)。M12 を見落とす AST allowlist は [`test_p3_s4_loop.py:830`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_s4_loop.py:830)。M15 の assertion 順序は [`test_reflux_ir.py:274`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_reflux_ir.py:274)、detector の非 artifact 性は [`reflux_ir.py:23`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/reflux_ir.py:23)。
- **(c) 最小の是正案:** M11 を API ごとに分割する。M12 を `tag`/`reflux` および trigger/autonomous consumer ごとの原子的変異に分け、AST 検査へ autonomous caller を加える。M15 は emitter digest を固定して golden digest だけを変えられる helper 単位のテストを作るか、acceptance mutation から diagnostic mutation へ降格する。

**成果物影響:** mutation matrix が実際には未検出の consumer/default drift と非 acceptance pin を「kill 済み」と記録し、材料レポートが誤った安全性根拠を参照する。

## should-fix

### 5. 未知 ID 拒否が trial の受理集合と terminal status を変える事実が契約化されていない

- **(a) 何が壊れるか:** 旧経路では任意の非空 `variant` を渡せた exploratory/custom drive が、対応する `BUILD_START` のない値を返すと `UnknownCriticIdentity` になり、critic 実行前に `supervisor-error`、generation `partial`、trial terminal `partial` へ変わる。公式 WAL の build/certify/reject 集合が不変でも、公開実行経路の受理集合は縮んでいる。
- **(b) 根拠:** [`p3_s4_loop.py:296`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:296)、[`p3_autonomous_workload_trial.py:1738`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1738)、[`p3_autonomous_workload_trial.py:1295`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1295)、[`p3_autonomous_workload_trial.py:1351`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1351)、[`p3_autonomous_workload_trial.py:2091`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:2091)。
- **(c) 最小の是正案:** 「公式 WAL admission 集合は不変」と「custom/exploratory acceptance は縮小」を分けて明記する。未知 ID について、critic event が作られず generation/lifecycle が partial になることまで固定する境界テストを追加する。

### 6. repo 全体の consumer 検査が自称する網羅性を持たない

- **(a) 何が壊れるか:** 現在の実コード呼出しには projector 引数が入っているが、網羅テストは production の `make_critic_digest()` 6 呼出し中、autonomous trial を除く5呼出ししか対象にしていない。また trigger test の `lambda *_a, **_k` は projector・tag・reflux の欠落や誤値を飲み込む。
- **(b) 根拠:** [`test_p3_s4_loop.py:830`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_s4_loop.py:830)、[`test_p3_s4_loop_trigger_gating.py:603`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:603)、autonomous caller は [`p3_autonomous_workload_trial.py:1746`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1746)。
- **(c) 最小の是正案:** production path allowlist に autonomous trial を加え、期待件数を6にする。単なる keyword 存在でなく、production projector factory の結果、正しい tag、設定由来 reflux が渡ることを検査する。monkeypatch は明示 signature の spy に替える。

### 7. land 前に追随が必要な docs が残っている

- **(a) 何が壊れるか:** operator と後続実装者が、projector を任意と理解したり、pseudonym を raw variant として引用したり、schema v2 の旧 reader で新 report を検証したつもりになる。
- **(b) 根拠:**
  - [`axis-onboarding.md:295`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/axis-onboarding.md:295): `make_critic_digest()` の新必須 projector が未記載。
  - [`phase3-s4b-runbook.md:102`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/phase3-s4b-runbook.md:102)、[`phase3-s5-sort-runbook.md:143`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/phase3-s5-sort-runbook.md:143): digest 内 ID が campaign-local label であることが未記載。
  - [`phase3-s8c-autonomous-trial-runbook.md:27`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/phase3-s8c-autonomous-trial-runbook.md:27)、[`phase3-s8c-autonomous-trial-runbook.md:151`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/phase3-s8c-autonomous-trial-runbook.md:151)、[`phase3-s8c-autonomous-trial-runbook.md:219`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/phase3-s8c-autonomous-trial-runbook.md:219): `candidate_label`、`None`、declassification、未知 ID の partial 化が未記載。
  - [`phase3.md:435`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/phase3.md:435): 今回閉じる範囲と残る P2 境界が未反映。
  - [`decisions.md:8138`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/decisions.md:8138): D164 は `harness_result.variant` を記録しており、新 wire 契約との差分を説明する後続 decision がない。
- **(c) 最小の是正案:** D164 を歴史改変せず、新 decision を追加して schema bump、campaign-local projection、受理集合縮小、未解決 V1–V4 を記録する。上記 phase/runbook/onboarding も同じ land で更新する。

## nit

### 8. IR detector 名が artifact identity と見分けにくい

- **(a) 何が壊れるか:** `IR_EMITTER_GOLDEN_CHANGE_DETECTOR_ID` は `SCHEMA_ID` や `canonical_emitter_sha256` と同じ identity namespace の値に見える。現時点ではコメントで否定しているだけで、将来の consumer が receipt/origin identity として流用しやすい。
- **(b) 根拠:** [`reflux_ir.py:21`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/reflux_ir.py:21)、[`reflux_ir.py:23`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/reflux_ir.py:23)、[`reflux_origin_ledger.py:260`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/reflux_origin_ledger.py:260)、[`reflux_origin_ledger.py:380`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/reflux_origin_ledger.py:380)。
- **(c) 最小の是正案:** `CHECKOUT_IR_EMITTER_GOLDEN_REGRESSION_ID` のように checkout-only regression detector と分かる名前へ寄せ、artifact schema/origin ID ではない旨を runbook に固定する。

## 総括

- **NO-GO。**
- 最大の理由は、同じ schema v2 のまま role wire と report shape を変更し、reader が `declassifications` を fail-open で receipting する点である。
- 文書化済み critic CLI は `IdentityProjection` の二重ロードにより実行不能になる。
- pseudonym を `variant=` と表示するため、WAL と材料レポートの参照整合が成立しない。
- WAL の公式 build/certify/reject 集合が変わらないという限定主張は維持できるが、custom/exploratory 入力の受理集合と terminal status は変わる。
- M11・M12・M15 は段4の atomicity／指定テスト帰属条件を満たさず、15/15 の変異証拠にはできない。
- Python consumer の単純な引数付け忘れは見つからなかったが、autonomous consumer を網羅検査が取り残し、`**kwargs` monkeypatch が意味上の欠落を隠す。
- pytest は実行しておらず、既知の3赤も新規所見には数えていない。