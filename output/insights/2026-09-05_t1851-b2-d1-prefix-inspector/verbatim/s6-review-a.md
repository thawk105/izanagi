## blocker

### 所見 1 — M14 の実台帳 2 世代テストが欠落

- (a) [実測] 裁定は段 6 で「同一 root に有効な v2 世代 A/B を作り、artifact/proof は B、外部引数は A」とする実台帳テストを必須化しています。現物には fake inspector 版と単一世代の binding 差替えしかなく、real inspector と live wrapper を結合した 2 世代 node はありません。
- (b) [実測] 必須条件は [s4-adjudication.md:120](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md:120)。現存する fake test は [test_s8b_floor_stats.py:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:883)、単一世代の差替え test は [test_s8b_attempt_registry.py:3486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:3486) です。
- (c) [推測] 放置時、外部 context が A でも reported proof 由来の B を path/expected に流用する変異が受理され、certified result と report が外部 admission ではなく別世代台帳 B を参照できる受理集合になります。
- (d) [推測] 所有 file `orchestrator/tests/test_s8b_floor_stats.py` に、実 `create_attempt_registry` と実 `inspect_attempt_registry_prefix` を使った A/B 2 世代 test を追加してください。正常実装は A を選んで B proof を拒否し、M14 変異だけが B を replay して受理する単一理由形にします。

## must-fix

### 所見 2 — pure verifier の actual validator 結合が stub され、D1522 が partial

- (a) [実測] 全 v5 test の共通 helper が actual `validate_attempt_registry_prefix_proof` をローカル再実装へ差し替えています。差し替えの呼出し回数 assertion もなく、統合後に同じ test を実走しても actual validator と pure verifier の結合は検査されません。また live M14 test は wrapper の拒否例だけで、同じ wrapper を通る正例対照がありません。
- (b) [実測] 再実装は [test_s8b_floor_stats.py:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:646)、無条件 monkeypatch は [test_s8b_floor_stats.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:696)。production の actual call は [s8b_floor_stats.py:766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:766)、live test の唯一の結果は [test_s8b_floor_stats.py:951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_stats.py:951) です。
- (c) [推測] 放置時、pure verifier が validator を迂回して reported/expected を直接比較する変異が検出されず、両方が同じ malformed proof なら bool の N、zero head、wrong schema を持つ v5 が受理集合へ入れます。
- (d) [推測] 所有 file `orchestrator/tests/test_s8b_floor_stats.py` でローカル validator を除去し、actual validator を包む spy に置換してください。reported/expected の 2 回呼出しを assertし、actual validator の正例と malformed 負例を同じ test に置きます。live wrapper にも同一 test 内の受理正例を追加します。

### 所見 3 — supersede 禁止の v4 pin node を変更

- (a) [実測] `test_floor_campaign_directly_reexports_shared_leaf_objects` は不変 pin 表の対象ですが、その node 内へ 7 行が追加されています。元の v4 assertion 自体は残っていても、「node を 1 行も変えない」という受入条件には不適合です。
- (b) [実測] 禁止指定は [s4-adjudication.md:88](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md:88)。変更された node は [test_s8b_floor_contract.py:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_contract.py:164)、追加行は [test_s8b_floor_contract.py:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_contract.py:181) です。
- (c) [実測] 現時点の artifact 値と v4 受理集合は変わりませんが、不変 oracle の参照範囲が変わり、単位 C が v4 pin を supersede する境界を監査しにくくします。
- (d) [推測] 所有 file `orchestrator/tests/test_s8b_floor_contract.py` で当該 node を base と完全一致へ戻し、LEGACY/V5/readable schema の assertion は新規 test node へ移してください。

## nit

[実測] nit はありません。

## plan v2 逐条照合

| 節 | 判定 | 根拠 |
|---|---|---|
| 1 root/path | [実測] closed | `shared_admission_root` と readonly lock のみを使い、exact path を読む実装です。[s8b_attempt_registry.py:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:857) |
| 2 replay | [実測] closed | v2 guard、binding 比較、全 payload replay の順です。[s8b_attempt_registry.py:935](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:935) |
| 3 inspection | [実測] closed | `len(rows)` 後に `rows[N-1]` を比較します。inspection に `rows[-1]` はありません。[s8b_attempt_registry.py:1039](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1039) |
| 4 proof validator | [実測] closed | exact 7 key、両 literal、hex64、bool 除外正整数、zero head 拒否があります。[attempt_registry_core.py:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:284) |
| 5 pure verifier | [実測] closed、test partial | header 2 field、expected 必須、両 proof validation、7 field 等値を実装しています。[s8b_floor_stats.py:771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:771) |
| 6 live wrapper | [実測] 実装 closed、M14 evidence missing | binding は外部 freeze/protocol/schedule だけから生成されています。[s8b_floor_stats.py:1133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:1133) |
| 7 contract | [実測] production closed、pin 違反 | `RESULT_SCHEMA` と default は v4 のままです。[s8b_floor_contract.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_contract.py:35) |

## 不変性・fail-open・digest

- [実測] v4 の base key set、default schema、`RESULT_SCHEMA` は従来どおりで、静的比較上 v4 artifact の受理集合変更はありません。
- [実測] v3 の既存文字列は [s8b_floor_stats.py:760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:760) と既存 pin test の双方で保存されています。
- [実測] core S5、v2 retryable 空集合、adapter S6、既存 reader/writer/recovery の hunk は変更されていません。例外は所見 3 の contract pin node だけです。
- [実測] reported 欠落時の skip、例外握り潰し、reported binding による expected/path 選択は production code にありません。filesystem/lock は `unverifiable`、schema/binding/replay/head は `mismatch` に分離されています。
- [実測] protocol digest は wrapper の `canonical_protocol_sha256` と admission の canonical JSON が同じ JSON 設定です。holdout caller は raw bytes との一致も [s8b_holdout_freeze.py:1405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_holdout_freeze.py:1405) で検査します。
- [実測] schedule digest は wrapper の no-newline canonical bytes と admission の [s8b_holdout_admission.py:5614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_holdout_admission.py:5614) が一致します。実 caller の schedule は `build_schedule` が返す `list[dict]` です。
- [実測] registry genesis 自体は導出せず caller の binding を保存します。[s8b_attempt_registry.py:1813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1813)。現導出に不一致は見つかりませんが、実結合の保証不足が所見 1 です。

## 段 3 レンズ A 判定

| 所見 | 判定 | 理由 |
|---|---|---|
| A-1 header 相互束縛 | [実測] closed | production 比較と freeze/protocol 各負例があります。 |
| A-2 M14 別世代 | [実測] missing | fake 版のみで、裁定指定の実台帳 2 世代版がありません。 |
| A-3 readonly root | [実測] closed | write helper tripwire、unsafe sibling、bytes/inode 不変検査があります。 |
| A-5 再 chain 改変 | [実測] closed | 再 chain 済み head mismatch と未再計算 chain failure が分離されています。[test_s8b_attempt_registry.py:3365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:3365) |
| A-6 到達可能 N | [実測] closed | 裁定後の N=1/3/4/5 と valid append を検査します。[test_s8b_attempt_registry.py:3215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_attempt_registry.py:3215) |
| A-7 v4 下層検査 | [実測] closed | mode/perf 別 v4 key set へ literal 不在 assertion があります。[test_s8b_floor_contract.py:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_contract.py:394) |

## 自己申告照合

- [実測] integrated patch と作業 tree の SHA-256 はともに `c660b69d6727a7f2caefe3d801b58919ffd5b76ac85f07ffd3aef0e9c13e3444` です。
- [実測] 8 file、`+1472/-11`、unit 1 の `19+22=41 node`、unit 2 の 11 function/13 node は申告どおりです。
- [実測] 食い違いは unit 2 報告の「統合後の実 API 実走は親作業」です。[s5-unit2.md:43](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s5-unit2.md:43)。現 test は統合後も validator を毎回 fake へ差し替えるため、単に親が実走しても actual API は通りません。
- [実測] unit 1 の pin 不変申告は unit 1 所有範囲では正しいです。統合後の contract pin 変更は unit 2 が「既存 node を拡張」と明記しており、数値の虚偽ではなく受入条件違反です。
- [実測] pytest は依頼どおり実走していません。

## 総括

- blocker: 1 件。
- must-fix: 2 件。
- nit: 0 件。
- production の主要 gate は静的には正しいものの、M14 の必須実台帳証明が欠落しています。
- 判定: **NO-GO**。