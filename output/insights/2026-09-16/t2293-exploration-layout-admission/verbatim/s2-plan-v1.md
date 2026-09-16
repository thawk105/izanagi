## 変更面 (file:line と差分の形)

以下は現物の変更前行番号。必読の射影ファイルはすべて読めた。brief の主要アンカーに行ずれはない。

production の変更は `orchestrator/campaign/reflux_result_evidence.py` に限定する。

| 位置 | 差分 |
|---|---|
| L34 | `.layout` から `ExplorationCampaignLayout` を追加 import |
| L444–448、検査 L447 | `_ordered_attempt_materials` の exact-type 受理集合を両型へ変更 |
| L1089–1092、注釈 L1090 | `_context_roots` の `layout` 注釈を `CampaignLayout \| ExplorationCampaignLayout` に変更 |
| L1196–1214、検査 L1213 | `issue_campaign_result_evidence` の exact-type 受理集合を両型へ変更 |

両 gate の述語・エラー文言を揃える。

```python
if type(layout) not in (CampaignLayout, ExplorationCampaignLayout):
    raise ResultEvidenceError(
        "layout must be an exact CampaignLayout or ExplorationCampaignLayout"
    )
```

公開入口と projection 入口の `layout: object` は維持する。不正型を受け取って明示的に拒否する入口だからである。共通 gate helper の新設や、`isinstance` による受理は行わない。

`git grep -n -F 'layout must be an exact CampaignLayout'` と `rg` で確認した完全一致箇所は次のとおり。

- `orchestrator/campaign/reflux_result_evidence.py:448`
- `orchestrator/campaign/reflux_result_evidence.py:1214`
- `output/insights/2026-09-09/t2437-production-issuer/mutation/mutation-final-out.json:119`
- `output/insights/2026-09-09/t2437-production-issuer/mutation/mutation-probe-out.json:461`

**旧全文を pin する test・docs はない。** 後二者は過去の実行ログなので変更しない。部分文字列 `exact CampaignLayout` は `orchestrator/tests/test_p3_b4_closed_critic.py:3045` にもあるが、別 gate の test であり本件では変更しない。

## 維持する拒否述語 (受理の含意 / 拒否の含意を各 1 文)

**受理の含意：** `type(layout)` が `CampaignLayout` または `ExplorationCampaignLayout` と同一なら型 gate を通過するが、証拠発行には既存の context・capability・契約・receipt・root・WAL・record 検査すべての通過が必要である。

**拒否の含意：** 両型の subclass、duck typed 同形 object、非 layout 値は exact-type gate で拒否し、exact な探索 layout でも physical root が evidence root 外なら既存の包含検査で拒否する。

以下、`E` は `orchestrator/campaign/reflux_result_evidence.py` を指す。

| 入力 | 拒否する検査 | 前後の拒否層・単一理由性 |
|---|---|---|
| (a) `CampaignLayout` の subclass | 発行入口の E:L1213、projection 入口からは E:L447 | 発行入口の前段 E:L1209 は context の型検査であり、有効な context なら通る。ただし L1213 を緩めても後段 L447 が同じ subclass を拒否するため、発行入口だけの緩和変異には単一理由性がない。 |
| (b) `ExplorationCampaignLayout` の subclass | 同上 | (a) と同じ。探索 subclass の生成には、有効な exact 探索 layout が用意した root を使い、namespace 不備を混ぜない。 |
| (c) `root` / `wal_file` を持つ frozen dataclass または `SimpleNamespace` | 同上 | 有効な layout の root・実 WAL を参照させる。発行入口では後段 gate が重複するが、projection 入口では L447 より前に型検査はなく、WAL reader にも layout の exact-type 検査はない。 |
| (d) `str` / `Path` 等 | 同上 | 通常実装では属性アクセスより前に拒否される。gate を除くと属性不足による別エラーが起き得るため、この負例を「gate 緩和で発行可能になる」変異の観測 node にはしない。 |
| (e) evidence root 外の exact 探索 layout | E:L1110–1113、呼出し E:L1278 | 修正後は L1213 を通る。両 root を実在する通常 directory とし、他の発行入力を有効にすれば、先行する directory 検査も通る。loop 経由では `loop.py:303–306` が先に拒否するため、この負例は producer 直呼びで観測する。 |

(e) の包含検査を消しても、後段の `E:L1173–1176` が content path の `relative_to(evidence_root)` で拒否する。したがって、producer 直呼びで L1110 の発火を確認できることと、L1110 の単独変異に単一理由性があることは区別する。

## 負例 test

追加先は `orchestrator/tests/test_reflux_result_evidence.py` の producer 正例 L1123 付近とする。

共通の準備には既存の `_producer_layout` L311、`_producer_context`、`_log_producer_attempt` L327、`_issue_producer_record` L398 を使う。正常な layout で実 WAL を先に作り、その後に入力 object だけを置き換える。これにより、型以外の不備を混ぜない。

`_issue_producer_record` の L400 は、拒否対象も渡す test helper として `layout: object` に変更する。`_log_producer_attempt` の L328 は両 layout の union 注釈にする。

追加する test は以下とする。

| 関数名 | 入力・assert |
|---|---|
| `test_campaign_producer_refuses_layout_subclasses_before_writes` | official / exploration の subclass を parametrize。`pytest.raises(evidence.ResultEvidenceError, match="^layout must be an exact CampaignLayout or ExplorationCampaignLayout$")`。 |
| `test_campaign_producer_refuses_duck_layout_before_writes` | frozen dataclass / `SimpleNamespace` を parametrize。実 layout と同じ `root`、`wal_file` を保持させ、同じ型エラーを assert。 |
| `test_campaign_producer_refuses_non_layout_values_before_writes` | `str(real_layout.root)`、`Path(real_layout.root)`、`None` を parametrize。同じ型エラーを assert。 |
| `test_campaign_producer_refuses_exploration_root_outside_evidence_root_before_writes` | context は `tmp_path / "evidence"`、探索 layout は sibling の `tmp_path / "outside-output"` を base に作る。`match="^physical campaign root is outside the result evidence root$"` を assert。 |
| `test_ordered_wal_projection_refuses_layout_subclasses` | 両 subclass を `produce_ordered_wal_projection` に直接渡し、同じ型エラーを assert。 |
| `test_ordered_wal_projection_refuses_duck_layout` | frozen dataclass / `SimpleNamespace` を同 projection API に渡し、同じ型エラーを assert。 |
| `test_ordered_wal_projection_refuses_non_layout_values` | `str` / `Path` / `None` を同 projection API に渡し、同じ型エラーを assert。 |

発行入口の負例では、呼出し前後の `_file_snapshot` L426 が同一であることと、`context.expected_record_path` に record が存在しないことも確認する。(e) は evidence root と outside-output の両方を snapshot する。

projection 負例では、有効な build attempt と、実 WAL の terminal prefix から計算した digest を持つ `source_wal_ref` を渡す。型 gate を緩めた際に digest 不一致などで代わりに落ちない fixture にする。

既存 `_assert_issuance_refused` L185 は derive／assemble／record 発行経路と `ResultEvidenceIssuanceRefused` 専用なので、型・root エラーには流用しない。既存の `pytest.raises(evidence.ResultEvidenceError, match=...)` 形式に揃える。

## 正例 test (単体・統合)

**単体は既存正例を両 layout で parametrize する。**

`test_reflux_result_evidence.py:1123` の
`test_campaign_producer_issues_real_wal_projection_and_resolves_interval` に `official` / `exploration` のパラメータを追加する。

`_producer_layout` L311 に keyword 引数を追加し、既定値は official とする。

- official：現在の `CampaignLayout(...).ensure()` を維持。
- exploration：`exploration_campaign_layout("fixture-physical-run", os.fspath(evidence_root)).ensure()` を使用。
- 戻り値注釈は両 layout の union。

探索側の配置は次の形になる。

```text
<tmp>/evidence/
  exploration/
    namespace.json
    campaigns/fixture-physical-run/
      runs/wal.jsonl
```

`layout.py:580–585` の実 `ensure()` を通し、L578 の worktree-container 拒否と L582 の namespace marker 作成・照合を維持する。test の tmp base は `.claude/worktrees` と `.codex/worktrees` の外に置く。実行環境が worktree 内を tmp base に指定している場合は、runner の tmp 配置を直し、この検査を monkeypatch しない。

L1148–1185 の既存 assert、すなわち record path、WAL interval、terminal prefix、stage 列、provenance の key 集合、三種の content 配置を両ケースに適用する。探索ケースでは exact 型と namespace marker の存在も確認する。

**統合は探索専用の正例を一本追加する。**

`test_reflux_campaign_issuer.py:386–438` の `_drive_campaign` に `declared_use_class="official"` を追加し、L433 の固定文字列をその引数に置き換える。既存 caller の既定動作は維持する。`_drive_required_campaign` L521 は既に `**kwargs` を渡すので、その経路を使える。

追加名：

```text
test_real_run_campaign_exploration_issues_rejected_record
```

L543 の既存正例の初回実行部分を踏襲し、required contract、verified calibration、実 receipt builder、synthetic checkout、fixture trace と実 verifier を使って、次を呼ぶ。

```python
_drive_required_campaign(
    ...,
    declared_use_class="exploration",
    context=context,
)
```

これにより `_drive_campaign` 内で実際に
`loop.run_campaign(declared_use_class="exploration", result_evidence_context=context)`
が実行される。producer や layout 選択は stub 化しない。

root の対応は次のとおり。

| 値 | 設定・期待 |
|---|---|
| `output_root` | 実在する `<tmp>/output` |
| `context.evidence_root` | **同じ `<tmp>/output` base** |
| physical campaign root | `<tmp>/output/exploration/campaigns/<cid>` |
| record | `<tmp>/output/<context.expected_record_path>` |
| content | physical campaign root 配下の `reports/reflux-result-evidence-content/v1/` |

`loop.py:451–452` が探索 constructor を選び、L525–528 の事前検査と L542 の materialization が同じ constructor を使う。`layout.py:589–597` の root 形は D1747 と一致し、`loop.py:303` と producer L1110 の包含条件も満たす。

assert は以下を含める。

- `issued.aborted == 1`、`issued.committed == 0`、結果一件、実 verifier の `non-serializable`。
- `issued.layout_root` が `exploration_campaign_layout(issued.campaign_id, output_root).root` と一致。
- 導出 record が存在し、parse／resolve でき、outcome が `rejected`。
- `ExplorationCampaignLayout` で読んだ実 WAL interval と resolver の source bytes が一致。
- source-WAL／projection／provenance が探索 physical root の下に存在する。

これは拒否された物理結果の証拠発行を確認する test であり、certified 受理を増やす test ではない。

## 変異事前登録候補

P4 の四候補は、次の照準で段4の登録候補とする。行番号は変更前であり、実装前の登録時に対象式と合わせて固定する。

| 候補 | 位置・変異 | 期待する観測 node | 単一理由性 |
|---|---|---|---|
| M1：subclass 受理への緩和 | E:L447 のみを `if not isinstance(layout, (CampaignLayout, ExplorationCampaignLayout)):` にする | `test_ordered_wal_projection_refuses_layout_subclasses[official]`、`[exploration]` | **静的には成立。** projection 入口は外側 L1213 を通らず、内側 WAL API に型拒否はない。有効な WAL/ref を使うので拒否消失を観測できる。 |
| M2：duck typing への緩和 | E:L447 のみを `if not hasattr(layout, "wal_file"):` にする | `test_ordered_wal_projection_refuses_duck_layout[frozen]`、`[namespace]` | **静的には成立。** 同じ理由で重複する型 gate がなく、実 WAL を参照する duck object が projection を生成できてしまう。subclass 負例も kill し得るため、観測集合に含める。 |
| M3：内側だけ旧 gate に戻す | E:L447 を `if type(layout) is not CampaignLayout:` に戻す | `test_campaign_producer_issues_real_wal_projection_and_resolves_interval[exploration]`、新しい探索統合 test | **静的には成立。** 外側 L1213 は探索型を通し、有効な context/root を経て、この gate だけが探索正例を過剰拒否する。 |
| M4：外側だけ旧 gate に戻す | E:L1213 を `if type(layout) is not CampaignLayout:` に戻す | 同じ探索単体正例・探索統合 test | **静的には成立。** 有効 context は L1209 を通り、内側は探索型を受理するので、この gate だけが過剰拒否する。 |

M3 は projection の subclass／duck 負例も引き続き拒否するため、それらは kill の根拠に数えない。M4 も同様に探索正例を観測する。

次の照準は登録しない。

- **L1213 だけの `isinstance`／`hasattr` 緩和：** 同じ入力を L447 が拒否する。brief の「subclass 負例が単独で kill」は、この照準では成立しない。
- **両 gate を一括して緩める変異：** 二箇所を同時変更する必要はなく、上記 projection 経路への再照準で単一箇所の実効性を測れる。
- **L1110 の root 包含検査除去：** loop 経路では前段 L303、producer 直呼びでも後段 E:L1173 が同じ root 外入力を拒否する。別の official 負例も kill するという理由ではなく、拒否層の重複を理由に登録から外す。

以上は静的な登録候補である。実装前に登録し、実装後に baseline と変異の実走で観測 node・赤理由を確認するまでは KILLED と報告しない。

## scope 外と未確認事項

変更対象は production 一ファイルと test 二ファイルに限定する。以下は触らない。

- `acceptance_duration_ledger.json`：稼働中 t1232 wave の編集面。
- `p3_autonomous_workload_trial.py`、`reflux_formal_consumer.py`。
- `artifact_admission.py`、`p3_b4_closed_critic.py`、`s8b_oracle_exploration.py` の別 exact gate。
- Q2〜Q4：台帳遷移、起点専用 entry point、完了判定。
- 検疫、auditor veto、condition gate、record 検証、writer の運用前提。

record schema と既存入力に対する bytes 生成規則は不変とする。`result-evidence/v1`、`execution-provenance/v2` に field を足さず、use class も記録しない。異なる physical root 間では既存規則どおり ref path が異なるため、official と探索の出力 bytes が相互に同一とは主張しない。

今回行ったのは読取りと静的検算だけで、pytest・変異・build は未実行。実装後は `tools/run_tests.py` 経由で対象二ファイルを検証する。brief の到達性 probe は親の既存証拠として扱い、本段で再実測した結果とはしない。

## 総括

Q1 は、二つの exact-type gate に `ExplorationCampaignLayout` を追加し、型拒否負例・root 外負例・両 layout の単体正例・探索の統合正例を同時に確定する形で実装できる。

P4 は、緩和変異を内側 gate と projection 直呼びの負例へ再照準する必要がある。Q2〜Q4 は未着手のままとし、本 plan は33本の executor 結線や本番 authority の成立を意味しない。