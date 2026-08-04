# T-410 実装プラン

## 推奨設計

`P <reason>` を、sort 軸専用の `SortIntegrityWitness` に変換し、`Integrity.sort_witnesses` として保持する。JSON では `result.integrity.sort_witnesses` に露出する。

受理判定は既存の `permutation_violations` カウンタだけに依存させ、witness は診断・同値判定専用とする。`clean()`、`verdict`、`certified` には一切結線しない。

## 現状認識の補正

brief の「`policy.py:245-290` が evidence schema の exact-key 検査を行う」という記述は正確ではない。

- [policy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/codex_roles/policy.py:245) の `_verifier_invariants()` は、現在は `integrity.clean` などの意味検査であり、integrity 全体の exact-key 検査ではない。
- 閉じた JSON Schema は [manifest.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/codex_roles/manifest.json:1623) と [verifier.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/.codex/role-adapters/verifier.json:39) にある。
- ハッシュ固定は [review_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/codex_roles/review_ledger.py:31) と同ファイルの `SCHEMA_SHA256`（123–126 行）にある。

したがって、この3層を同じ実装単位で更新しないと dormant role adapter の整合が壊れる。

## 1. witness の型定義

[model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/model.py:9) の import と 101–150 行を変更する。

```python
@dataclass(frozen=True)
class SortIntegrityWitness:
    reason: str
    thid: Optional[int] = None
    kind: Literal["sort-permutation"] = field(
        default="sort-permutation",
        init=False,
    )

    @property
    def equivalence_key(self) -> Tuple[str, str]:
        return (self.kind, self.reason)
```

`Integrity` には、既存の positional constructor を壊さないよう、現在最後にある `notes` の後へ追加する。

```python
sort_witnesses: List[SortIntegrityWitness] = field(default_factory=list)
```

フィールドの根拠は以下のとおり。

- `reason`: P 行自身が持つ唯一の payload。[parse.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/parse.py:154) は現在 `P <reason>` の2 tokenだけを読む。
- `thid`: P 行ではなく trace ファイル名から推定した出所情報。
- `kind`: 軸ごとの閉じた契約を識別する判別子。
- `txid`、key、変更前後のサイズ、rcdptr 値などは存在しないため追加しない。

C++ 側では [transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/tests/fixtures/silo_ladder_rung1/stock/cc/silo/transaction.cc:395) の 413–432 行が、`size-changed` または `rcdptr-set-changed` と thread stream だけを emit している。C++ は変更しない。

### thid の復元規則

[trace.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/external/ccbench/include/trace.hh:17) の命名規則を根拠に、trace path `p` に対して次で確定する。

\[
\operatorname{thid}(p)=
\begin{cases}
\operatorname{int}(m_1) &
\text{if }\operatorname{fullmatch}(\texttt{trace\_(\textbackslash d+)\textbackslash.log},
\operatorname{basename}(p))=m\\
\texttt{None} & \text{otherwise}
\end{cases}
\]

`parse_trace_dir()` は現在 [parse.py:203](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/parse.py:203) で `trace_*.log` を受け付けるため、非 canonical 名を新たな parse error にしてはならない。復元不能時は `thid=None` とし、受理集合を維持する。

## 2. 同値関係

P1 の「reason 種別のみ」を、sort 軸内の同値関係として採用する。ただし、他軸との衝突を防ぐためグローバルなキーには kind を含める。

sort witness \(w\) の同値キーは、次の確定式とする。

\[
\kappa_{\mathrm{sort}}(w)
  = (\texttt{"sort-permutation"}, w.\mathrm{reason})
\]

\[
w \equiv_{\mathrm{sort}} w'
\iff
w.\mathrm{kind}=w'.\mathrm{kind}=\texttt{"sort-permutation"}
\land
w.\mathrm{reason}=w'.\mathrm{reason}
\]

`thid`、出現順、出現回数は同値キーに含めない。同じ原因が別 thread で発生しても、「同じ理由で危険」と分類できるためである。

reason は正規化せず、完全一致で扱う。

- 既知 reason は現在 `size-changed` と `rcdptr-set-changed`。
- 未知 reason は既存 parser が受理する単一 token であり、受理集合維持のため parse error にしない。
- 未知 reason はその文字列自身を別の危険クラスとして保存する。
- 未知 `kind` は別問題であり、sort adapter が解釈できないため fail-closed とする。

これは D138 決定 (8) の「軸ごとに別契約」を `kind` で表し、決定 (4) の「未知 kind は fail-closed」を満たす。一方、未知 reason の拒否は既存入力の意味を変えるため行わない。

## 3. JSON 露出と後方互換

[report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/report.py:42) の `result_to_dict()` で、既存 integrity キーの後へ次を追加する。

```json
"sort_witnesses": [
  {
    "kind": "sort-permutation",
    "reason": "size-changed",
    "thid": 3
  }
]
```

同値キーは `kind` と `reason` から一意に導出できるので、JSON には重複して保存しない。復元不能な thread は `"thid": null` とする。

### integrity 内を選ぶ理由

`result.integrity.sort_witnesses` を推奨する。

- witness と `permutation_violations`、`clean` が同じ integrity 契約にまとまる。
- [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/campaign/pipeline.py:797) は結果全体をそのまま渡す。
- [digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/critic/digest.py:245) の 255–260 行は nested integrity dict を保存するため、新キーも自然に生存する。
- result 級 exact-key 集合を変更しなくてよい。
- D138 決定 (8) に反する汎用 result-level witness 名前空間を作らずに済む。

代案の result 直下は、`_integrity_counters_zero` の int 前提を回避できる一方で、次の問題があるため却下する。

- [silo_ladder_rung1.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/campaign/silo_ladder_rung1.py:1415) の result 級 exact-key 検査も結局変更が必要。
- critic の rejection loader は現在未知の result 直下キーを保持しない。
- counter とその構造化根拠が別階層になる。
- 将来の異種 witness を一つの曖昧な契約に混ぜやすい。

### 旧 evidence の限定互換

silo ladder では次の2形状だけを認める。

- 新 K13: 既存12キーと `sort_witnesses`。常に詳細検証する。
- 旧 K12: `permutation_violations == 0` の記録済み evidence に限り認める。

旧 K12 で `permutation_violations > 0` は拒否する。危険な記録から witness だけを欠落させる downgrade を許さないためである。

## 4. consumer 追随の完全列挙

| 場所 | 実装内容 |
|---|---|
| [model.py:9–12](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/model.py:9) | `Literal` import、`SortIntegrityWitness` 定義 |
| [model.py:101–150](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/model.py:101) | `Integrity.sort_witnesses` を末尾追加。`clean()` は変更しない |
| [verifier/__init__.py:15–39](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/__init__.py:15) | 新型を公開 |
| [parse.py:31–39](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/parse.py:31) | canonical trace filename regex を追加 |
| [parse.py:46–79](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/parse.py:46) | `ParseIssues.permutation_violations` を witness の list に変更 |
| [parse.py:89–183](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/parse.py:89) | ファイルごとの inferred thid を使って P 行を witness 化。新しい parse failure は追加しない |
| [core.py:82–95](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/core.py:82) | witness list を `Integrity` にコピー。count は list 長、notes は `w.reason` から従来どおり生成 |
| [report.py:42–75](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/report.py:42) | integrity 内に exact witness object を直列化 |
| [report.py:95–115](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/report.py:95) | 人間向け出力は notes が既に reason を表示するため変更不要 |
| [t152_write_intent_coverage.py:440–463](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/campaign/t152_write_intent_coverage.py:440) | nested dict の passthrough を確認。実装変更不要 |
| [t152_write_intent_coverage.py:523–538](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/campaign/t152_write_intent_coverage.py:523) | `sort_witnesses` を非 counter と明示し、この driver では list かつ空を要求。未知 integrity key は引き続き拒否 |
| [s5_permutation_coverage.py:87–125](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/campaign/s5_permutation_coverage.py:87) | 生 trace parser を維持し、別途 witness reason counter と形状検査を追加 |
| [s5_permutation_coverage.py:160–245](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/campaign/s5_permutation_coverage.py:160) | raw reason、witness reason、counter の三者一致 check を追加 |
| [silo_ladder_rung1.py:821–823](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/campaign/silo_ladder_rung1.py:821) | K12/K13 の限定互換 helper |
| [silo_ladder_rung1.py:1415–1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/campaign/silo_ladder_rung1.py:1415) | K13 exact-key、item schema、count 一致、未知 kind 拒否 |
| [silo_ladder_rung1.py:2817–2839](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/campaign/silo_ladder_rung1.py:2817) | 旧 K12 との比較では `pv==0` かつ再計算 witness 空の場合だけ新キーを正規化除外 |
| [manifest.json:1623–1762](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/codex_roles/manifest.json:1623) | verifier input/output の integrity を exact `{clean, permutation_violations, sort_witnesses}` に更新 |
| [policy.py:245–287](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/codex_roles/policy.py:245) | exact keys、item 型、未知 kind、count 一致、`pv>0 ⇒ !clean` を検査 |
| [review_ledger.py:31–48](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/codex_roles/review_ledger.py:31) | verifier manifest hash 更新 |
| [review_ledger.py:123–126](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/codex_roles/review_ledger.py:123) | verifier input/output schema hash 更新 |
| [.codex/role-adapters/verifier.json:39–181](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/.codex/role-adapters/verifier.json:39) | manifest から機械的に再生成 |
| [.codex/role-adapters/verifier.json:183–213](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/.codex/role-adapters/verifier.json:183) | 生成物の hash ledger 更新 |
| [digest.py:245–264](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/critic/digest.py:245) | nested dict は既に保持するため production 変更不要。回帰テストのみ追加 |
| [digest.py:603–622](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/critic/digest.py:603) | 非空 witness は generic integrity rendering に出るため変更不要 |
| [cli.py:60–86](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/cli.py:60) | `result_to_dict()` と既存 exit status を使うため変更不要 |
| [pipeline.py:797–807](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/campaign/pipeline.py:797) | result dict を透過するため変更不要 |

### 実走時だけ壊れうる潜在経路

最重要は [t152 の `_integrity_counters_zero()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/campaign/t152_write_intent_coverage.py:523) である。

現在は `clean` と `notes` 以外をすべて `int` と仮定する。単体テストの自前 fixture が旧 K12 のままだとテストは通るが、実 verifier が新しい list を返す実走時だけ `isinstance([], int)` が失敗する。fixture 更新だけで済ませず、本体 helper の非 counter 集合と空 witness 契約を明示的に直す。

同様に、codex role の単体 fixtureだけ更新しても、manifest・生成 adapter・hash pin が同期していなければ runtime/checker でのみ壊れるため、これらは一括変更する。

## 5. 受理集合不変の証明

旧 Integrity 状態を \(x\)、任意の witness list を \(L\)、新状態への埋め込みを \(E(x,L)\) とする。

`sort_witnesses` を [model.py:144–150](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/model.py:144) の論理積に追加しないため、

\[
clean_{\mathrm{new}}(E(x,L))=clean_{\mathrm{old}}(x)
\]

[model.py:185–198](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/model.py:185) の verdict 関数を \(F\) とすると、

\[
verdict_{\mathrm{new}}
=F(n_{\mathrm{txns}},serializable,clean_{\mathrm{new}})
=F(n_{\mathrm{txns}},serializable,clean_{\mathrm{old}})
=verdict_{\mathrm{old}}
\]

同じく [model.py:200–203](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/verifier/model.py:200) から、

\[
certified_{\mathrm{new}}
=(n_{\mathrm{txns}}>0\land serializable\land clean_{\mathrm{new}})
=certified_{\mathrm{old}}
\]

実 trace では `len(sort_witnesses) == permutation_violations` を保証する。ただし、手で不整合な `Integrity` を構築した場合も witness list 自体は受理判定に影響させない。

`n_txns ∈ {0,1}`、`serializable ∈ {False,True}`、`permutation_violations ∈ {0,1}`、witness が空/非空の直積をテーブルテストし、paired object の `clean()`、`verdict`、`certified` が等しいことと、既存の期待値双方を pin する。

witness list を `clean()` に加える案、`verdict`/`certified` から直接参照する案は、絶対規律2に違反するため却下対象とする。

## 6. 既存4本と純増検出力

[test_verifier.py:490–550](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/tests/test_verifier.py:490) の4本は現在、次を被覆している。

- `test_permutation_violation_indeterminate`: P が count と `INDETERMINATE` に反映される。
- `test_permutation_violation_control_serializable`: P がない control が serializable。
- `test_permutation_violation_reasons_parsed`: 2 reason の parse と notes 集約。
- `test_permutation_violation_between_txn_blocks`: P が transaction block 外にあっても検出され、txid に属さない。

これらは、型付き witness、thid、JSON object、同値キー、未知 reason、consumer schema、全分岐の受理不変を検出できない。新設テストの純増検出力はこの部分に限定する。

## 7. s5 driver

`_count_p_reasons()` は置き換えない。

verifier が生成した witness を verifier 出力自身から数えて positive control にすると、parser・core・JSON の同じ誤りを driver も受け入れる自己検証になるためである。

代わりに次の三者を独立に比較する。

1. `_count_p_reasons()` による生 trace の reason multiset
2. verifier JSON の `sort_witnesses` による reason multiset
3. `integrity.permutation_violations`

既存 erase/swap の reason positive control は引き続き 1 を使い、新しい check で 1 と 2 の完全一致、および `len(sort_witnesses) == 3` を要求する。

なお [既存 s5 artifact](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/output/env/linux-baremetal/calibration/s5_permutation_coverage.json:7) は aggregate count だけを保存し、driver は [s5_permutation_coverage.py:163–169](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/campaign/s5_permutation_coverage.py:163) で一時 trace を削除する。したがって既存 artifact は過去の count の参照にはなるが、新 witness 経路が同じ trace を再現した証明にはならない。

## 8. テスト計画

| nodeid | 落ちる条件 |
|---|---|
| `orchestrator/tests/test_verifier.py::test_sort_witness_structured_json_and_source_thread` | P が exact `{kind, reason, thid}` にならない、または filename の thid を誤る |
| `...::test_sort_witness_equivalence_key_is_reason_only` | thread や出現順を同値キーへ混入する |
| `...::test_sort_witness_unknown_reason_is_preserved` | 未知 reason を破棄・既知値へ丸める・parse error にする |
| `...::test_sort_witness_noncanonical_filename_preserves_acceptance` | 非 canonical `trace_*.log` を新たに拒否する、または架空 thid を作る |
| `...::test_sort_witness_does_not_change_acceptance_truth_table` | witness の有無が `clean()`、`verdict`、`certified` を変える |
| `orchestrator/tests/test_t152_write_intent_coverage.py::test_integrity_counter_helper_accepts_empty_sort_witnesses` | 新しい実 verifier 出力を list 非 int として誤拒否する |
| `...::test_integrity_counter_helper_rejects_nonempty_sort_witnesses` | P==0 control に非空 witness が混入しても通す |
| `orchestrator/tests/test_silo_ladder_rung1_driver.py::test_verifier_integrity_schema_accepts_new_and_zero_only_legacy_shapes` | K13 を拒否する、または P-positive K12 downgrade を許す |
| `...::test_verifier_integrity_schema_rejects_unknown_sort_witness_kind` | 未知 kind を fail-open する |
| `orchestrator/tests/test_codex_agents.py::test_verifier_sort_witness_policy_preserves_count_and_rejects_unknown_kind` | role schema/policy が item shape、count、kind の不整合を見逃す |
| `orchestrator/tests/test_critic.py::test_sort_witness_survives_integrity_rejection_path` | rejection 保存・再読込・render の途中で witness が消える |
| `orchestrator/tests/test_s5_permutation_coverage.py::test_witness_reason_counts_reconcile_with_independent_trace_parse` | raw P と witness の理由別件数が一致しない |
| `...::test_reason_reconciliation_detects_missing_or_wrong_witness` | witness 欠落や reason 誤変換を reconciliation が見逃す |

最後の s5 テストファイルは新規であり、現行の file:line は存在しない。

既存 fixture も更新する。

- [test_t152_write_intent_coverage.py:27–49](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/tests/test_t152_write_intent_coverage.py:27): `sort_witnesses: []` を counter 群の外に追加。
- 同 343–370 行: empty/nonempty helper ケース。
- 同 760–795 行: representative witness の passthrough。
- [test_silo_ladder_rung1_driver.py:72–86](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/tests/test_silo_ladder_rung1_driver.py:72): 新 K13 fixture。
- 同 602–685 行: closed schema と限定 K12 互換。
- [test_silo_ladder_rung1_evidence.py:1038–1042](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1038): committed K12 との比較に、空 witness だけの限定正規化。
- [test_codex_agents.py:908–983](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t410-sort-integrity-witness/orchestrator/tests/test_codex_agents.py:908): verifier fixture と negative cases。

実装後に親が計算ノード側で targeted pytest、`python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py`、必要な provenance 検査を行う。本プラン作成時には pytest を実行しておらず、緑は主張しない。

## 9. 段5の実装単位

分割せず、1 worker が担当することを推奨する。

witness の `kind` literal、JSON exact shape、counter/list 一致、旧 K12 の限定互換、manifest と hash pin が単一の原子的契約を構成する。複数 worker に分けると、中間状態で verifier、campaign consumer、role adapter の契約が互いに不一致になりやすい。

所有対象は次の一集合とする。

- `orchestrator/verifier/{model,parse,core,report,__init__}.py`
- `orchestrator/campaign/{t152_write_intent_coverage,s5_permutation_coverage,silo_ladder_rung1}.py`
- `orchestrator/codex_roles/{manifest.json,policy.py,review_ledger.py}`
- `.codex/role-adapters/verifier.json`
- 対応する `orchestrator/tests/` の既存ファイル
- 新規 `orchestrator/tests/test_s5_permutation_coverage.py`

C++、`external/ccbench`、`output/`、FROZEN_MANIFEST の23成果物は所有対象外とする。

## 総括

- 推奨案: `SortIntegrityWitness(reason, thid, kind="sort-permutation")` を `Integrity.sort_witnesses` に追加し、同値キーを `("sort-permutation", reason)` とする。受理判定は既存 counter のまま維持する。
- 却下案: result 直下への露出、thid を同値キーへ含める案、未知 reason の拒否、witness を `clean()`・P6・cap-lift に結線する案、s5 の raw parser を置換する案。
- P0: 賛成。実 artifact と s5 の独自 parser があり、実装ゲートは成立する。
- P1: 条件付き賛成。sort 軸内は reason-only、全体の識別には kind を含める。
- P2: 賛成。ただし t152、silo exact schema、role manifest・生成 adapter・hash pin まで閉じる必要がある。
- P3: 一部賛成。ログインノードでの実走省略と緑を主張しない点には賛成するが、既存 aggregate artifact だけでは新 witness 経路の再現を証明できない。
- 残る不確実性: `kind` の確定 literal と、`pv==0` に限る旧 K12 互換を段4で裁定する必要がある。また raw s5 trace が残っていないため、新経路の historical E2E 実測は将来の認可された再実行まで未確認となる。