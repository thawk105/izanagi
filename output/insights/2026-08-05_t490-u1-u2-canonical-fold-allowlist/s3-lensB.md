現状のプランは **NO-GO** です。実装境界そのものは概ね正しい一方、identity と独立 allowlist を証明するテストに生存変異が残っています。以下はすべて静的検査で、pytest は実行していません。

## 所見

### 1. P-D と identity 統合テストは production `src_token` の oracle になっていない

- 判定: **real**
- 根拠: 親の再測スクリプトは raw predicate の `hashlib.sha256()` を比較しているだけです（[probe_premises.py:43](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/probe_premises.py:43)、[同:47](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/probe_premises.py:47)）。本番 `src_token` は `g++ -E -P` の正規化出力を材料にする [source_digest.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/source_digest.py:320)、[同:640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/source_digest.py:640)、[同:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/source_digest.py:749) です。さらに計画テストも raw file bytes を token にする fake resolver です（[plan.md:120](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/plan.md:120)）。したがって正準化削除変異が fake では赤でも、本番 `src_token` 差を固定したことにはなりません。§7 の簡易 `g++` プローブ主張を否定するものではありませんが、段1再測と acceptance test は本番経路を再現していません。
- **成果物影響**: `pipeline.variant_id` は `src_token` を直接使うため（[pipeline.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/pipeline.py:87)）、certified 選択・試行台帳の variant 統合という主保証が fake 固有の赤で認証されます。
- 最小対処: exact／空白付きの実テンプレを production `source_digest.compute` または `resolve` に通す独立回帰を追加し、正準化削除時に実 token と実 `variant_id` が分岐することを計算ノードで固定する。

### 2. P2 の「emitter bytes を返す」保証には生存変異がある

- 判定: **real**
- 根拠: 計画は synthetic 入力で index builder の値を検査しますが（[plan.md:107](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/plan.md:107)、[同:152](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/plan.md:152)）、公開関数を `return text.strip()` にした変異は、現行 emitter が全て strip 恒等なので全 public test を通り、builder test も無傷です。公開関数が index の値を本当に返す保証になっていません。また、計画した import-time 重複 key 拒否（[plan.md:21](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/plan.md:21)）にも明示テストがありません。加えて quarantine テスト列挙は P-C の `\x0b` / `\x0c` を落としています（[plan.md:114](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/plan.md:114)）。現行受理契約は Python `str.strip()` 全体です（[trigger_gate_binding.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/trigger_gate_binding.py:87)）。
- **成果物影響**: 将来 emitter が外周空白を正準 bytes とした際、binding digest は raw emitter を hash する一方（[trigger_gate_binding.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/trigger_gate_binding.py:75)）、materialized source は strip 形になり、材料 proof の predicate/source 対応がずれます。
- 最小対処: synthetic index を公開 canonicalizer に注入または monkeypatch して値側の raw bytes が返ることを検査し、重複 key の `RuntimeError`、P-C の7種すべてを明示追加する。

### 3. U-2 の drift guard は独立 allowlist を証明しない

- 判定: **real**
- 根拠: 設計は producer 定数を流用しないと明記します（[plan.md:61](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/plan.md:61)、[同:74](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/plan.md:74)）が、テストは三集合の現在値の等価だけです（[plan.md:132](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/plan.md:132)）。次の二変異はいずれも計画テストを通ります。
  - `_PREPARE_CELL_CONFIGURATIONS = frozenset(s1_measurement_freeze.CONFIGURATIONS)` として将来拡張を自動認可する。
  - 正しい定数を未使用のまま、`configuration == "system-gate"` だけ拒否する。6正例・単一未知負例・集合等価はすべて緑です。
- **成果物影響**: 新 producer configuration または `"system-gate"` 以外の未知値が4分岐を抜け、[s1_direct_comparison.py:516](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:516) から flags-only の source/token を作り、材料レポートと台帳に誤った configuration を載せます。
- 最小対処: 上記二変異を matrix に追加する。独立な literal RHS を確認する静的検査と、複数の動的生成 unknown を拒否する挙動検査を入れる。allowlist 削除変異では checkout と resolver を permissive fake にし、他層で mask されず実際に yield まで達することも確認する。

### 4. 「材料 proof chain も統合される」という brief の説明は過大

- 判定: **real**
- 根拠: U-1 は `src_token` / `pipeline.variant_id` を統合しますが、S-1 review receipt は raw `item.cell` を hash します（[s1_direct_comparison.py:758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:758)）。S8b binding も raw freeze entry の `entry_sha256` を含めて `binding_sha256` を作ります（[s8b_materialization.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_materialization.py:117)、[同:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_materialization.py:124)）。材料レポートは両 hash を検査します（[s8b_oracle_report.py:867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_oracle_report.py:867)）。reject 用 `diffq_variant_id` も raw implementation を hash します（[p3_s4_loop.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:237)）。
- **成果物影響**: exact／空白付き入力は同じ successful variant になっても、材料レポートの `entry_sha256` / `binding_sha256`、review receipt、reject WAL 参照は引き続き別値です。
- 最小対処: scope は変えず、「統合するのは successful materialized source・`src_token`・`pipeline.variant_id`」と brief/plan の成果物主張を狭め、raw provenance は意図的に別のままと明記する。

### 5. 「上流が塞ぐため純増ゼロ」は U-1/U-2 とも refuted

- 判定: **refuted**
- 根拠: 公式 S-1 は18セル exact schema で閉じています（[s1_measurement_freeze.py:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_measurement_freeze.py:310)）。S8b freeze も6構成から再構成一致を要求します（[s8b_holdout_freeze.py:809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_holdout_freeze.py:809)）。しかし、以下の直接経路にはその閉包がありません。
  - U-1: `quarantine` は strip membership 後に raw implementation を `render_hole` へ渡します（[p3_s4_loop.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:202)、[同:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:225)）。既存テストも空白付き全32点が検疫を通ることを示します（[test_p3_s4_loop.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/tests/test_p3_s4_loop.py:171)）。
  - U-2: `prepare_cell` の未知値は4分岐を抜け `resolve` / yield に達します（[s1_direct_comparison.py:494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:494)、[同:562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:562)）。`s8b_materialization.prepared_binding` も任意 mapping/ID を cell に射影して呼ぶだけです（[s8b_materialization.py:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_materialization.py:103)、[同:135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_materialization.py:135)）。
- **成果物影響**: U-1 は直接 sink の source/diff 受理集合を実際に畳み、U-2 は直接 materializer の未知 configuration 受理集合を実際に縮めるため、純増はゼロではありません。
- 最小対処: 直接境界テストは維持する。公式 freeze だけを入力にしたテストを新 gate の証明として数えない。

### 6. consumer 取り残しは確認されなかった

- 判定: **refuted**
- 根拠: 独立列挙結果は以下です。

| 対象 | 全 production caller / seam |
|---|---|
| `is_canonical_predicate` | `s1_direct_comparison.py:521`、`s1_verify_extime_calibration.py:222`、`p3_s4_loop.py:203`。直接テストは `test_trigger_gate_binding.py:222-227`。 |
| `prepare_cell` | S-1 `run_role` の default/call（[s1_direct_comparison.py:623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:623)、[同:757](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s1_direct_comparison.py:757)）、S8b materialization の default/call（[s8b_materialization.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_materialization.py:145)、[同:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_materialization.py:136)）、floor の default/shared wrapper（[s8b_floor_campaign.py:2742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_floor_campaign.py:2742)、[同:985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_floor_campaign.py:985)）、oracle の default/shared wrapper（[s8b_oracle_driver.py:1155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_oracle_driver.py:1155)、[同:1316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/s8b_oracle_driver.py:1316)）。 |
| injection | S-1 `prepare_cell_fn`、materialization/floor/oracle の `prepare_fn`。既存 S8b テストの大半は fake、real canary は計画記載どおり `stock_common`。 |
| `render_hole` | production 呼び出しは [p3_s4_loop.py:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop.py:225) の1箇所だけ。 |

  trigger/sort marker も別値です（[axis_trigger_gating.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/axis_trigger_gating.py:23)、[p3_s4_loop_sort.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t490-u1-u2/orchestrator/campaign/p3_s4_loop_sort.py:96)）。P1 の共有境界と comparator 非干渉方針は正しいです。
- **成果物影響**: caller 漏れによって U-1/U-2 を迂回する未保護の production 経路は見つかりませんでした。
- 最小対処: caller 追加は不要。fake seam が実 gate の coverage に数えられないことだけ明記する。

## Nit

- 分割理由は **refuted** です。brief は production の `s1_direct_comparison.py` 所有が交差するとします（[brief.md:73](/work/1/SFC/tanab/dev-wave-jobs/t490-u1-u2/brief.md:73)）が、計画上 U-1 の production 編集は `trigger_gate_binding.py` と `p3_s4_loop.py`、U-2 だけが `s1_direct_comparison.py` です。交差するのは主に `test_s1_direct_comparison.py`。単一実装単位は選べますが、「production 所有が素集合でない」は誤った根拠です。成果物影響はありません。
- `FROZEN_MANIFEST` は既存 output bytes の非編集 sentinel であり、runtime materializer の挙動保証ではありません。コードだけ壊しても manifest test は赤くならないため、P-F 非干渉は新しい source-level test 側で証明すべきです。

## 総括

- 現プランは、テスト保証を補強するまで NO-GO です。
- P1 の共有 `quarantine` 境界と comparator 除外は妥当です。
- P3 の allowlist 配置も妥当ですが、独立性を現行集合の等価テストだけでは証明できません。
- U-1/U-2 とも直接 caller があり、上流閉包に対する純増はゼロではありません。
- production `src_token` を使わない fake identity oracle は差し替えが必要です。
- P2 には `return text.strip()`、重複 index、VT/FF の生存変異が残ります。
- proof chain 全体の統合は達成されないため、保証文を successful source identity に限定すべきです。
- caller の取り残しと S8b 3モジュールの漏れは確認されませんでした。
- pytest・build・freeze 再生成は実行しておらず、緑は主張しません。