## 判定

**本 wave は実装へ進めず、設計メモで止めるべきです。**

4 述語を検査する部品自体は既存関数の組合せで小さく書けます。しかし、cap-lift 固有の認定記録 path、receipt path、production caller、P6 実認定が存在しません。[`reflux_formal_consumer.py:1`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/reflux_formal_consumer.py:1) も P6 実装 wave が未実施と明記し、成功直前まで進んでも `P6Unavailable` を返します。[`reflux_formal_consumer.py:942`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/reflux_formal_consumer.py:942)

したがって topology helper だけを land しても、実 artifact から発火する正例を持たない未結線 gate になります。これは DW-G04 を満たさず、D1407 が却下した「到達不能な入口だけを land」に該当します。[`rulings-D1407.md:42`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/rulings-D1407.md:42)

## 編集対象と新設 file

今回の推奨変更:

- **編集 file: なし。**
- **新設 file: なし。**
- コードではなく、以下の conditional plan を親の設計メモへ戻す。

実 artifact path と full consumer 単位が揃った後の、topology 部分だけの最小編集位置:

- [`trial_registry.py:1243`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:1243) の直後 — `assert_effective_commit_exact_activation_topology(repository_root, *, content_commit, effective_commit, accreditation_path, receipt_path)` を追加し、既存 exact-parent、exact-additions、逐語 trailer を順に合成する。
- [`test_trial_registry.py:6073`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/tests/test_trial_registry.py:6073) から `:6249` の実 Git fixture 群の直後 — exact 2 create-only と trailer の正負例を追加する。
- `s8b_ratified_freeze.py` は編集せず、既存 `_added_paths` と `_is_none_commit` を package 内部から再利用する。
- topology 部分だけなら新設 file は不要であり、cap-lift 固有 module を先行新設しない。

D841 を満たす実装解禁後には、別途 `orchestrator/campaign/cap_lift_receipt.py` と対応テストが必要です。ただし path/schema/consumer preimage が未確定なので、現段階でその file を新設してはなりません。

## exact-parent 機構の再利用可否

[`assert_effective_commit_exact_parent:1243-1269`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:1243) は**そのまま再利用できます**。述語 (i) と (ii) は論理的に一つの exact-parent 検査で足り、別の非 merge gate は冗長です。

署名と内部依存は次のとおりです。

- `assert_effective_commit_exact_parent(Path, *, content_commit: str, effective_commit: str) -> None`
- `_parents_at_commit(Path, *, commit_id: str) -> tuple[str, ...]` は `rev-list --parents -n 1` の一行、ASCII、先頭 identity を検査します。[`trial_registry.py:1211`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:1211)
- `require_commit_object(Path, str) -> None` は full lowercase SHA-1 と exact object identity を要求します。[`trial_registry.py:1152`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:1152)
- `_assert_no_grafts_or_replace_refs(Path) -> None` と `_assert_not_shallow(Path) -> None` が out-of-band history 改変を拒否します。[`trial_registry.py:1168`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:1168)
- `_repository_root(Path) -> Path` は指定 path が exact Git top-level であることを要求します。[`trial_registry.py:969`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:969)
- `_git(Path, Sequence[str]) -> CompletedProcess[bytes]` は環境 allowlist、system/global config 無効化、literal pathspec、replace object 無効化を適用します。[`trial_registry.py:942`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:942)
- `_fail(gate, message)` は `TrialRegistryError("[gate] message")` を送出します。[`trial_registry.py:258`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:258)

診断語彙は `[repo-path]`、`[git]`、`[git-operational]`、`[commit]`、`[ancestry]` です。Git process 自体を起動できない場合だけ `_git` から `OSError` が直接出る点は既存の限界ですが、今回の scope で一般化しません。

この関数に足りないものは、述語 (iii)、(iv)、A の artifact 導入 commit としての発見、A が measurement HEAD の祖先であることです。後二者は現在の prereg consumer が別途行っている形が先例です。[`trial_registry.py:1466`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:1466)

## trailer 機構の再利用

[`s8b_ratified_freeze.py:518-555`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/s8b_ratified_freeze.py:518) を次の形で再利用します。

- `_raw_ai_agent_lines(message) -> List[str]` は大小文字や空白違いを含む全 `AI-Agent` 系行を拾います。
- `_parsed_ai_agent_values(message, root) -> List[str]` は `interpret-trailers --parse` の値を返します。
- `_is_none_commit(commit, root) -> bool` は raw 行が exact `AI-Agent: none` 1 本、かつ parse 値が `["none"]` の場合だけ真です。

`_assert_user_commit(commit, graph, root)` は再利用しません。理由は root commit を拒否せず、親数 `0` または `1` を区別せず、HEAD graph と `RatifiedFreezeError` に結合しているためです。[`s8b_ratified_freeze.py:558`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/s8b_ratified_freeze.py:558)

`_assert_candidate_commit` も再利用しません。D1407 は G に非 `none` の AI trailer を要求しておらず、この関数の candidate provenance 規則を流用すると受理集合を独断で狭めます。[`s8b_ratified_freeze.py:573`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/s8b_ratified_freeze.py:573)

`_is_none_commit` や diff 読取時の `RatifiedFreezeError` は、conditional wrapper で `[git-operational]` の `TrialRegistryError` に変換し、呼出側へ二種類の例外を露出させません。

## exact 2 create-only の既存実装

性質検索の結果、**既存実装があります**。

[`_added_paths:607-618`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/s8b_ratified_freeze.py:607) は `diff-tree --name-status -r` を読み、status `A` とそれ以外を分離します。直後の [`_verify_pairing:1273-1295`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/s8b_ratified_freeze.py:1273) が次を既に強制しています。

```text
added == {approval.path, pointer.path} and other == empty
```

したがって次が拒否されます。

- 既存 path の変更と mode 変更: `M`
- 削除: `D`
- rename 検出時: `R`
- rename 非検出時: `D` と `A` の組合せ
- 別 path の追加: `added` の exact set 不一致

同型の exact 1 path 実装も [`t080_freeze_migration.py:1253-1268`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/t080_freeze_migration.py:1253) にあります。新しい diff parser は不要です。

conditional wrapper は `_added_paths(A, root)` の結果を `{accreditation_path, receipt_path}` と比較するだけにします。

## s8c receipt 機構の再利用

[`s8c_acceptance_receipt.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/s8c_acceptance_receipt.py) から再利用できる部品は次です。

- canonical JSON bytes: `:172-184`
- duplicate key 拒否を含む strict decode: `:229-256`
- `_exact_keys`: `:259-266`
- SHA-256、commit、POSIX path validator: `:269-293`
- git env allowlist: `:95-97,580-600`
- HEAD の literal regular blob 読取: `:658-683`
- verifier 発行の封印型と再検証 pattern: `:152-169,1219-1243`

一方、`parse_acceptance_receipt_bytes` 自体は cap-lift receipt に再利用できません。v1-v4 の exact keys に固定され、`certifying is not False` を構造的に拒否するためです。[`s8c_acceptance_receipt.py:357`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/s8c_acceptance_receipt.py:357)

実装解禁後は cap-lift schema 用 parser を**一つだけ** `cap_lift_receipt.py` に置きます。producer と completeness はともにその parser/verifier と sealed value を使い、各側に schema parser を褯製しません。completeness は同じ parser で bytes を読み直したうえで、producer validator を呼ばず envelope の意味を独立再検査します。

## 正例と負例

正例は [`test_trial_registry.py:99-162`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/tests/test_trial_registry.py:99) の実 Git helper を使います。

- 実 repository を `git init` する。
- G を実 commit として作る。
- G の直子 A で canonical な認定記録 path と receipt path の 2 件だけを新規追加する。
- A の message を `activate\n\nAI-Agent: none` とする。
- Git 関数や trailer parser を monkeypatch せず、topology wrapper を通す。

負例はすべて一つの述語だけを壊します。

| 負例 | 単独の拒否理由 | 先行層を通す条件 |
|---|---|---|
| A を root commit にする | exact parent が空 | path 2 件と trailer は正しい |
| A を merge にする | parent 集合が `{G}` でない | G 側 diff と trailer は正しい |
| A の唯一親を別 commit にする | parent が exact G でない | 非 merge、path、trailer は正しい |
| expected 2 件に extra 1 件を足す | added set 不一致 | exact parent、trailer は正しい |
| G に既存の第三 path を A で変更 | `other=M` | expected 2 件も create-only |
| G の既存 path を削除 | `other=D` | expected 2 件も create-only |
| G の既存 path の mode だけ変更 | `other=M` | bytes、parent、trailer は正しい |
| G の path を expected path の一方へ rename | `R` または `D+A` | もう一方は正常追加、parent/trailer は正しい |
| trailer 欠落 | exact-none false | exact parent と diff は正しい |
| trailer 重複 | exact-none false | exact parent と diff は正しい |
| key の大小文字違い、末尾空白 | raw 逐語検査だけが拒否 | parse 値は `none` になり得る |

shallow、graft、replace ref、root、merge、別親は [`test_trial_registry.py:6073-6249`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/tests/test_trial_registry.py:6073) に既存実 Git 負例があります。wrapper 用に同じ gate を重複登録せず、既存 exact-parent テストを依存証拠にします。

現時点では cap-lift artifact の実 schema と P6 認定記録が無いため、上記は topology 単体の正例であり、cap-lift の end-to-end positive control とは主張できません。

## 受理集合が動かないこと

推奨どおり無変更なら、受理集合は自明に不変です。

conditional な未結線 helper だけを加えた場合も直接の受理集合は変わりませんが、発火しない gate を land する価値がないため採りません。

現行の境界は次で維持されています。

- producer の承認上限は `MAX_APPROVED_GENERATIONS = 2` のままです。[`p3_autonomous_workload_trial.py:139`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:139)
- 3 入口は同じ `_validate_generation_budget` を通ります。[`p3_autonomous_workload_trial.py:501`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:501)
- completeness は run-envelope と campaign-chain の双方で上限 2 を再検査します。[`autonomous_trial_completeness.py:2289`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/autonomous_trial_completeness.py:2289)、[`autonomous_trial_completeness.py:4829`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/autonomous_trial_completeness.py:4829)
- registered manifest は引き続き整数 2 だけを受理します。[`trial_registry.py:743`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:743)

したがって receipt 無しの 1 世代・2 世代は縮小されず、3 世代以上も新たに受理されません。

## P1 への回答

(a) **narrow scope は、そのまま cap-lift 実装単位として land すると不適切です。** 純粋な汎用 Git helper だけなら D841 の「receipt だけ」に字義上は該当しません。しかし T-434 の実装成果として扱うなら、receipt と consumer closure が無いので D841 の positive-control 要求を満たしません。[`rulings-D841.md:3`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/rulings-D841.md:3)

代わりの実装単位は、D1407 が定める P6 本体、実認定、receipt、new manifest、producer、journal、report、completeness、Layer 3、runbook を含む G 全体です。

(b) **DW-G04 は満たせません。** repo に cap-lift 固有の認定記録 path、receipt path、発火済み計測 ID はありません。temporary Git fixture の path は production artifact path の代用になりません。したがって設計メモに留めます。

(c) **現裁定から G の複数 commit 化を承認してはいけません。** D1407 は単数の「内容 commit G が実装一式を導入する」とし、A をその直子に固定しています。[`rulings-D1407.md:6`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t434-two-stage-binding/rulings-D1407.md:6)

開発中の作業 commit は許容しても、認定前に一つの G へ squash し、その exact G を認定して A を作るのが現在の安全な読みです。commit train の terminal tree を G と扱いたい場合は、「G は累積 tree の tip でよく、全 ancestor と A を同一 transaction で land する」と明示する追加裁定が必要です。

## 実際に効く層と裁定パッケージ

現行 exact-parent 機構が実際に効いているのは preregistration binding consumer です。[`trial_registry.py:1499`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t434-two-stage-binding/orchestrator/campaign/trial_registry.py:1499)

cap-lift については、conditional topology helper 単体が効くのは直接呼出しと単体テストだけです。次は未結線であり、本 scope で実装済みと扱えません。

- P6 の意味的充足本体、calibration、反転変異、独立 attestation、認定記録と失効照合
- cap-lift receipt の唯一 parser、sealed verified type、A の発見、A blob と HEAD blob の同一性
- producer の `main`、`run_trial`、`_run_workload`
- journal `run-start`
- supervisor 正常 report と `_budget_indeterminate_report`
- completeness の run-envelope と campaign-chain
- new registered manifest version と registry acceptance
- Layer 3 top-level envelope
- runbook の consumer 記述
- G と A を同一 land transaction にする機械的または運用上の強制

条件 11 の証拠契約、8c 事前登録本文、凍結 bytes、D882 が予約した runbook の承認上限文は、この裁定パッケージでも編集対象外です。

pytest は実行しておらず、以上は基準 commit `28ebff456b9f57a927854950b5030fa77aec6529` に対する静的検査です。

## 総括

既存の exact-parent、exact 2 create-only、逐語 `AI-Agent: none` を組み合わせれば topology 検査自体は小さく実装できます。しかし cap-lift の実 artifact と consumer が無いため、現 wave での land は DW-G04 を満たさず、D841 準拠の実装単位にもなりません。

推奨は無変更で設計メモへ戻し、P6 と全 consumer を含む一つの G を確定、実認定後に人間 A を作ることです。最大の不確実性は、D1407 の「G」が単一差分 commit を意味するか、同一 land transaction 内の累積 tip を許すかが逐語では確定していない点です。