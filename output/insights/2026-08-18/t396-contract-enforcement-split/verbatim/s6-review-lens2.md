段 6 レンズ 2 の判定は **NO-GO、must-fix 3 件**です。実差分の pin 閉包と adapter byte parity は正しい一方、変異会計と provenance に未閉鎖があります。

### Must-fix 1 — 1 commit では waiver が「発火済み」と会計されない

4 枚のうち `.codex/`、`orchestrator/*.py` は実装面です。[規約](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/docs/ai-provenance.md:46)上、Codex author と、adapter を適用した親の author 帰属、waiver が必要です。

最低限の最終 trailer block は次の形です。model/reasoning は実表示値を使い、確認不能なら規約どおり `unknown` とします。

```text
AI-Agent: product=codex; model=gpt-5.6-sol; reasoning=high; role=author; scope=contract-and-test
AI-Agent: product=<parent-product>; model=<actual-or-unknown>; reasoning=<actual-or-unknown>; role=author; scope=adapter-render-apply
AI-Agent-Waiver: reason=codex-sandbox-readonly-dotcodex; ratified=2026-08-18
```

同じ `author` が複数行なので両方に `scope` が必須です。実質的に採用された manager、integrator、reviewer があれば別行も必要です。全行は本文との空行後に連続する最終 trailer block へ置きます。

ただし checker は commit 内に Codex author が一人でもいると先に成功し、waiver を「適用済み」と数えません。[validate_implementation_author](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/tools/check_ai_provenance.py:1231) は path ごとの author/scope 対応を検査せず、waiver の stdout 会計も `waived_applied` の場合だけです。[出力箇所](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/tools/check_ai_provenance.py:2600)

したがって、この 1 commit 形では人間可読な帰属は記録できますが、親による adapter 適用を checker が機械証明できません。段 7 ではユーザー裁定による段 4 §5 の supersede、対象 path、waiver 件数 1 を worklog に明記し、checker が waiver 0 と出しても「免除未使用」と報告しないことが必要です。この checker 限界を許容するかも親裁定が要ります。

成果物影響: certified 値と受理集合は変わりませんが、provenance 監査結果が adapter の実著者と waiver 適用件数を誤って表し、試行台帳の参照根拠が不正確になります。

### Must-fix 2 — M6 は KILLED を保証しない

M6 の「`file-stdio` から identifier を 1 個削る」は対象が非一意です。[DENY_TABLE](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/campaign/coder_effect_gate.py:71) には多数の identifier がありますが、category probe は `read();` だけです。[専用 probe](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/tests/test_coder_effect_gate.py:68)

- `read` を削除すれば `test_each_deny_table_category_has_a_mutation_killing_probe[file-stdio]` が殺します。
- `ofstream` を削除すれば measured injection と統合 seam が殺します。
- `filesystem` など個別 probe の無い identifier は静的には SURVIVED し得ます。

従って M6 は exact anchor を `read` に固定するか、選んだ identifier 専用の既存 probe がある位置へ再照準する必要があります。

成果物影響: 未修正では mutation ledger が host-effect 受理集合拡大への検出力を過大申告し、将来その identifier を含む候補が材料レポートや certified 選択へ到達し得ます。

### Must-fix 3 — M1/M3/M4 の expected-node／primary-kill 帰属が不成立

- **M1:** 旧 source pin に戻すと [load_role_specs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/codex_roles/spec.py:583) が eager import 中に `SOURCE_FILE_SHA256 drift` を送出します。pytest node の実行前なので failed node 0 件となり、DW-M08 会計では停止します。standalone checker 経路へ再照準が必要です。
- **M3:** adapter の埋込本文から 1 行だけ削ると、exact-once 検査より先に renderer byte parity が拒否します。[checker](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/tools/check_codex_agents.py:214)上の期待 node は少なくとも `test_current_sources_render_byte_exact_and_native_is_empty` と `test_source_body_is_embedded_exactly_once_before_product_override` の 2 件です。primary kill を exact-once とするのは誤帰属です。
- **M4:** adapter 内 ledger pin だけ戻しても、先に byte parity が拒否します。期待 node は少なくとも `test_current_sources_render_byte_exact_and_native_is_empty` と `test_all_adapters_pin_model_policy_and_blocked_runtime_activation` の 2 件です。独立 ledger 照合だけの kill ではありません。

M2 は stale adapter という単一原因で、上記 3 adapter test が失敗候補です。M5 は構造 gate 通過後に [effect gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/campaign/p3_s4_loop.py:242) が呼ばれるため、実効 gate への照準は正しいです。いずれも probe 後に完全集合を登録する必要があります。

成果物影響: 未修正では mutation ledger が「どの防壁が材料レポート／certified 候補を守ったか」を誤記し、proof chain の検出力主張が不正確になります。

### Pin 閉包

識別子 key と path の両検索を行いました。内容を実際に消費する live 面は次です。

- agent 本文を inline する運用手順: [phase3-s5-sort-runbook.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/docs/phase3-s5-sort-runbook.md:59)
- source bytes の独立 pin: [review_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/codex_roles/review_ledger.py:15)
- generic path 解決、pin 検査、renderer、semantic digest: [spec.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/codex_roles/spec.py:538)
- adapter byte parity／本文 exact-once: [check_codex_agents.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/tools/check_codex_agents.py:214)
- 独立 test: [test_codex_agents.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/tests/test_codex_agents.py:127)
- 生成 adapter 自身: [.codex/role-adapters/coder-v4-autonomous-sort.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/.codex/role-adapters/coder-v4-autonomous-sort.json:1)

role 名だけを参照する `manifest.json`、`policy.py`、`p3_s4_loop_sort.py`、trigger-gating sibling、`agent-architecture.md`、`src/coder-spec.md` は本文 bytes を複製・pin していません。decisions、archive、既存 output は歴史記録であり、更新対象ではありません。

review ledger の更新状況は正しいです。

| 面 | 状態 | 判定 |
|---|---|---|
| `SOURCE_FILE_SHA256` | 対象 key のみ更新 | 正しい |
| `ROLE_MANIFEST_SHA256` | 未更新 | manifest entry 不変なので正しい |
| `DESCRIPTION_SHA256` | 未更新 | frontmatter description 不変なので正しい |
| `SCHEMA_SHA256` | 未更新 | 入出力 JSON 例・schema 不変なので正しい |
| `ROLE_IO_CONTRACTS` | 未更新 | required fields／mode 不変なので正しい |
| `DEVELOPER_INSTRUCTION_TEMPLATE_SHA256` | 未更新 | template 不変なので正しい |
| `EXPECTED_ROLE_COUNT` | 未更新 | 13 role 不変なので正しい |

旧／新 source hash、旧／新 adapter 全体 hash、旧／新 `semantic_digest` を repo 全体で検索しました。source hash の live 出現は ledger 1 箇所と adapter 内 2 箇所だけです。adapter 全体 hash、ledger file 全体 hash、semantic digest を別に pin する live 箇所はありません。

### Adapter byte parity

メモリ上で `get_role_spec` → `render_adapter` を実行して比較しました。

- actual と rendered: 完全 byte 一致
- bytes: 14,940
- 両者の SHA-256: `b7b3c2dafa97a3756a05dbe00b630eacb18f226a8bdd875a0f9d9befa252837c`
- source SHA-256: `fbabef04095f73b7fc517290afc66d4fb8779144184eaf7c078fc17d50d7ca9a`
- semantic digest: `b01fb78b5f6cc33a2ce75b9bd49481b9622b7a4c0760326c14e043256875ac06`
- sorted key、2-space indent、末尾 LF、NFC、`source.sha256`、ledger 内 source pin はすべて一致

`python3 tools/check_codex_agents.py` も rc=0 でした。これは静的 checker の結果であり、pytest の緑ではありません。手編集の痕跡はありません。

成果物影響: この面の所見は closed です。adapter が将来使用可能になった場合も、Claude role と異なる禁止集合を提示する差異はありません。

### テスト削除の波及

削除 node の exact name は live `docs/`、`orchestrator/`、`tools/`、`.claude/`、`.codex/`、`src/` で 0 件です。repo 全体では過去の mutation ledger 2 枚だけに各 6 回あり、live consumer ではありません。

- `test_plain_runner_coverage.py` は `test_*.py` のファイル存在と自走 harness を動的に検査します。対象ファイルと `__main__` は残るため影響なし。
- `test_pytest_collection_config.py` は収集 directory を固定しますが、総 node 数は固定していません。
- 固定 file 集合や固定 node 数を持つ別 meta-test は見つかりませんでした。
- docs で削除 node を逐語名指しする箇所はありません。archive に対象ファイルの過去の行番号説明が 1 件ありますが、歴史記録なので更新不要です。

失われる直接検出力は、通常 `for`、range-for、data-dependent `while`、`while (0)`、空の通常 `for` の 5 件です。直接の受け皿はありません。[false literal の姉妹テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t396-contract-alignment/orchestrator/tests/test_coder_effect_gate.py:182)は別入力だけを覆い、代替になりません。

成果物影響: 現在の production 受理集合、certified 選択、材料レポート値は不変です。ただし将来この 5 形を誤って拒否する回帰は検出されなくなります。これは段 4 が明示採用した既知残余です。

### M7

禁止 bullet 1 行を削除し、source pin と adapter を整合再生成すれば、source hash、semantic digest、byte parity、exact-once、JSON shape はすべて再び整合します。禁止文の逐語または意味を独立固定する test はありません。歴史 output に同じ文が残っても live gate ではありません。

従って M7 の **SURVIVED 期待は正しい**です。注入後 diff で削除実在を確認する条件は必要です。

成果物影響: 禁止集合を意図的に再承認して縮めると coder の契約上の受理集合が広がり、不適切な候補が材料レポート／certified 選択へ到達し得ることを示します。

pytest、mutation harness、`check_docs.py`、provenance full-history 監査はすべて未実走です。静的 checker rc=0 を受入緑とは数えていません。

## 総括

- 判定: **NO-GO**
- must-fix: **3 件**
- pin 閉包: closed
- adapter renderer byte parity: closed
- テスト削除の live 波及: なし
- 失われる 5 件の検出力: 受け皿なし、裁定済み残余
- M7: SURVIVED 期待が正しい
- M6: exact identifier 未指定のため KILLED 期待が不成立
- M1/M3/M4: failed-node／primary-kill の再照準が必要
- provenance: 1 commit 混載時の path 別 waiver 会計が未閉鎖