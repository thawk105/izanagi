静的レビューのみ実施した。pytest は指示どおり未実走。`git diff --check 4f0d020..HEAD` は clean だった。

## 所見

### 所見 1: consumer 閉包に `test_autonomous_trial_completeness.py` が取り残され、既存テスト群が新 admission の入口で停止する

- 根拠: [test_autonomous_trial_completeness.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_autonomous_trial_completeness.py:96) は旧 8c campaign ID 群を保持し、[同:1187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_autonomous_trial_completeness.py:1187) の手組み lock は `axis+reflux` なのに schema marker がなく、[同:1240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_autonomous_trial_completeness.py:1240) の WAL に binding/commitment/provenance もない。そのまま [同:1273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_autonomous_trial_completeness.py:1273) で Layer3 admission に入る。
- 攻撃シナリオ: `_layer3_campaign()` を使う M10・campaign-chain 系テストを走らせると、狙った completeness 変異へ届く前に「trigger proposal の marker 欠落」で一律停止する。
- 成果物影響: completeness 防壁が本来の変異を検査できず、受入全走も赤になる。
- 提案: 同ファイルを B1 の必須 consumer に追加し、全 workload/trial の旧新 ID、raw binding、start commitment、provenance を独立 literal fixture として更新する。
- 型タグ: [捏造/幻覚] [ドリフト]
- severity: **blocker 候補**

### 所見 2: clean な no-build と fixture main が、新しい binding/provenance admission と接続されていない

- 根拠: clean `do_build=False` は [p3_s4_loop_trigger_gating.py:496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:496) で WAL を書かず `dry-pass` を返す一方、public funnel は [同:677](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:677) の後に [同:688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:688) で admission 必須の digest を作る。validator は [wal.py:714](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/wal.py:714) で空の build-start 集合を拒否する。fixture main も [driver:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:827) から直接機械部を呼び [同:836](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:836) で digest を作るが、provenance は明示的に書かない。
- 攻撃シナリオ: 8c fixture provider は auditor `pass` を返すため、文書化された `--provider fixture --no-build` は空 WAL admission で停止する。build 有効 fixture main は binding を書けても [artifact_admission.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/artifact_admission.py:431) の provenance 必須条件で停止する。
- 成果物影響: no-build 配線 report・critic digest・fixture E2E が生成できない。
- 提案: dry-pass を正式 admission へ入れない明示経路、または no-build を識別する閉じた artifact 契約を設計する。fixture main は `drive_iteration` 相当の provenance funnel へ統合する。
- 型タグ: [恒真ゲート] [ドリフト]
- severity: **blocker 候補**

### 所見 3: direct trigger の epoch テストは自己矛盾しており、8c 全 workload の epoch 契約も未実装

- 根拠: [test_campaign.py:1748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_campaign.py:1748) は `ccba936e` を旧 ID に入れ、直後に current ID が旧集合外と assert する。しかし [test_p3_s4_loop_trigger_gating.py:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:106) と [同:546](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:546) は現在の OTHER ID を同じ `ccba936e` と固定している。8c 側は [test_p3_autonomous_workload_trial.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_p3_autonomous_workload_trial.py:150) の ycsb-a 一件だけで、ycsb-b/c、即時 pre-T428 ID、旧 path 非書込がない。
- 攻撃シナリオ: direct epoch テストは最初の ID assert で確実に赤になり、後段の旧 path 非書込検査へ到達しない。8c では marker 継承を b/c だけ落とす変異が生存する。
- 成果物影響: campaign freshness と旧 root 非汚染を証明できず、受入全走も赤になる。
- 提案: direct の即時旧 ID を `0e79a5f1` / `63bc09ae` に戻し、現 ID と分離する。8c は A/B/C 全 workload の旧新 ID と旧 root 非書込を表形式で固定する。
- 型タグ: [恒真ゲート] [ドリフト]
- severity: **blocker 候補**

### 所見 4: provenance 照合が集合比較のため、attempt 単位の欠落を検出できない

- 根拠: [artifact_admission.py:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/artifact_admission.py:442) は WAL start と provenance を `(variant, commitment)` の `set` に潰して比較する。一方 WAL 契約は [wal.py:704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/wal.py:704) で `build_attempt_id` 単位に一対一化している。既存テスト [test_artifact_admission.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_artifact_admission.py:329) は単一 attempt の digest 改変しか扱わない。
- 攻撃シナリオ: 同じ variant/source/binding/nonce を持つ abort→retry 二 attempt を異なる attempt ID で作ると、両 start は同じ pair に縮退する。provenance entry を一件だけ残しても集合は一致し admission を通る。
- 成果物影響: admitted campaign の attempt 台帳から一部 provenance を消しても、Layer3/report が正当化される。
- 提案: provenance に `build_attempt_id` を持たせ、各 start が少なくとも一つの entry から参照される関係を検査する。duplicate proposal は明示的な既存 attempt 参照として区別する。
- 型タグ: [恒真ゲート] [捏造/幻覚]
- severity: **blocker 候補**

### 所見 5: commitment の preimage が裁定の逐語契約と一致せず、テストも実装自己参照になっている

- 根拠: 裁定は [s4-ruling.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/output/insights/2026-08-04_t428-reflux-wiring/s4-ruling.md:15) で `sha256(canonical(binding) ∥ nonce)` と定義する。実装は nonce を JSON 内へ含めたうえで [trigger_gate_binding.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/trigger_gate_binding.py:156) の `sha256(canonical_json(binding))` のみ。テストも [test_trigger_gate_binding.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_trigger_gate_binding.py:70) で同じ helper 出力から期待値を作る。
- 攻撃シナリオ: 裁定文どおりに独立 verifier を実装すると、現行 producer/replay が使う commitment と一致しない。内部 A/B/C/D は全て同じ helper を使うため、この不一致だけは全テスト緑でも隠れる。
- 成果物影響: report/provenance commitment が裁定準拠の外部再検算と非互換になる。
- 提案: canonical bytes と nonce の連結方法を byte 列まで一意化し、独立 literal golden vector を追加する。現方式を採るなら裁定側の式を先に整合させる。
- 型タグ: [恒真ゲート] [ドリフト]
- severity: **要検討**

### 所見 6: `trigger_binding` は「直前」と記述されるが、validator は任意の先行位置を受理する

- 根拠: writer は [wal.py:548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/wal.py:548) で “immediately before” と宣言するが、validator は [同:735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/wal.py:735) で `binding_index < start_index` だけを検査する。テスト [test_campaign.py:889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_campaign.py:889) は duplicate と start 後だけで、間への別 record 挿入を試さない。
- 攻撃シナリオ: `raw-A, raw-B, start-A, abort-A, start-B...` の交差順を作っても両 binding は検証を通る。
- 成果物影響: attempt 対応自体は ID で保たれるが、WAL が主張する直前配置・クラッシュ境界を成果物から証明できない。
- 提案: 直前性が契約なら `binding_index == start_index - 1` を強制し interposition 変異を追加する。単なる先行性でよいなら docstring と裁定記述を縮小する。
- 型タグ: [恒真ゲート] [ドリフト]
- severity: **要検討**

### 所見 7: agent / manifest / adapter / policy の四面 parity は wire の形だけで、意味契約までは閉じていない

- 根拠: agent は [coder role:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/.claude/agents/coder-v4-autonomous-trigger-gating.md:64) で bit 順・極性・`kUnset=true` を明示する。manifest の projection は [manifest.json:962](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/codex_roles/manifest.json:962) で bit 順と極性を持つが `kUnset` は「emitter 専権」まで、adapter override も同じ短縮形。policy は [policy.py:482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/codex_roles/policy.py:482) で key 集合と `[01]{5}` しか固定しない。テスト [test_codex_agents.py:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_codex_agents.py:877) も形だけである。
- 攻撃シナリオ: manifest/adapter の bit 意味または `kUnset` 極性だけを変更し、schema・policy・pin を追随させれば checker は意味ドリフトを検出しない。
- 成果物影響: dormant role の将来有効化時に、同じ wire が異なる gate 意味として扱われうる。
- 提案: bit 順・極性・`kUnset=true` の単一 semantic literal を四面へ束縛し、exact parity テストを置く。
- 型タグ: [恒真ゲート] [ドリフト]
- severity: **要検討**

`review_ledger.py` の変更キー自体は trigger role の source/manifest/description/output schema にだけ閉じており、他 role の pin 汚染は見つからなかった。[権限逸脱] の実装所見はなし。[セッション死・救出] についても、対象 HEAD 内は P→A/B/C→横断 fix の統合状態で、stub の片肺残存は見つからなかった。

## 変異登録の検出力

| ID | 静的判定 | 主な検出面 |
|---|---|---|
| M-A1 | 実在 | old `implementation` 拒否 |
| M-A2 | 実在 | invalid wire corpus |
| M-A3 | 実在 | LSB bit-order + 無編集 `test_reflux_ir` golden |
| M-A4 | 実在 | preview/run 同一 materialization |
| M-A5 | 実在 | generic sink 32-membership |
| M-A6 | 実在 | autonomous parser/provider/preview |
| M-B1 | 実在 | missing binding replay/admission |
| M-B2 | 実在 | mask/sha 単独改変 |
| M-B3 | 実在 | source/receipt 不一致 |
| M-B4 | 実在 | replay tamper |
| M-B5 | 実在 | `records_by_stage` bypass |
| M-B6 | 実在 | artifact admission tamper |
| M-B7 | 実在 | marker 欠落・unknown classification |
| M-B8 | 実在 | `variant_id` signature/preimage |
| M-B9 | **弱い** | 単一 pair mismatch のみ。所見4の attempt multiplicity を殺さない |
| M-C1 | 実在 | unknown mode 拒否 |
| M-C2 | 実在 | sort/backoff sink・proposal 受理 |
| M-C3 | 実在 | loader/direct axis mismatch |
| M-C4 | 実在 | bool/out-of-range mask |
| P+1 | **弱い** | `run_one_iteration` 機械部だけ。所見2の public `drive_iteration`/digest を通らない |
| P+2 | 実在 | 32 正準述語の generic sink 通過 |
| P+3 | 実在 | sort/backoff legacy proposal と sink の受理 |

また、段2で予定された `test_record_diff_reject_without_binding_preserves_legacy_payload` は存在しない。[test_p3_s4_loop.py:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_p3_s4_loop.py:247) は semantic roundtrip のみで、stage 順・payload key 集合を固定しない。現コードの binding 未指定 payload は静的には旧形を維持しているが、回帰検出力は不足している。skip/xfail の新規混入は見つからなかった。

## 親残作業

- `docs/phase3-s8c-autonomous-trial-runbook.md`: 対象 HEAD では未編集で、現在も coder が「具体 gate 述語を合成」、`syntax gate` を通すと記述している。
- `docs/axis-onboarding.md`: 対象 HEAD では未編集。共有 worktree には親の未commit編集があるため、本実装 diff の完了とは数えない。

## 総括

最重要 3 件は次のとおり。

1. clean no-build と fixture main が新 admission に接続されず、文書化された 8c 配線試験が停止する。
2. 列挙外 consumer と自己矛盾した epoch テストにより、受入全走が静的に赤で、8c 全 workload の旧 root 非汚染も未証明。
3. provenance の集合比較が attempt multiplicity を消し、一部 attempt の provenance 欠落を admitted とする。

全体判定: **NO-GO**。静的に確定する実行経路停止とテスト自己矛盾があり、pytest 未実走という不確実性だけを理由にした判定ではない。