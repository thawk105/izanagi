## must-fix (成果物影響を 1 行で書けるもの)

以下、`C` = `orchestrator/campaign/autonomous_trial_completeness.py`、`R` = `orchestrator/campaign/trial_registry.py`、`T` = `orchestrator/tests/test_autonomous_trial_completeness.py`。`brief` と `plan` は指定された各 Markdown を指す。

**1. 新 opt-in の成功集合は広がる。「path identity だけ省略」という brief の契約では採用できない。**

根拠：`brief.md:58`、`s2-plan.md:61`、`C:4374`、`C:5075`、`C:5080`。

例えば、次の cell は plan の厳密述語を満たす。外側を exploratory・`do_build=true`・`status="partial"` とし、同じ error の fatal／terminal、failure projection、digest を整合させる。宣言先は存在しない campaign とする。

```json
{
  "workload": "ycsb-a",
  "workload_flags": {
    "ycsb_zipf_skew": "0.9",
    "ycsb_rratio": "50",
    "ycsb_rmw": "0"
  },
  "perf_config_scale": {"records": 100000, "threads": 4},
  "descriptor": {
    "schema_version": "8b-v1",
    "source": "campaign_search_config_projection",
    "contention": {"label": "high", "skew": 0.9},
    "read_write": {"read_ratio_percent": 50, "rmw": 0},
    "scale": {"records": 100000, "threads": 4},
    "correctness": "serializable_legacy_and_s2",
    "objective": "maximize_throughput_tps"
  },
  "descriptor_binding": {
    "output_sha256": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "campaign_id": "failure-example",
  "campaign_root": "/abs/diagnostic-output/campaigns/failure-example",
  "generations": [],
  "stop_reason": "supervisor-error",
  "error": {"type": "RuntimeError", "message": "before campaign creation"},
  "admission_decision": {
    "schema_version": "p3-autonomous-workload-trial-cell-admission-failure/v1",
    "admission_status": "failed",
    "error": {
      "type": "AutonomousTrialError",
      "message": "build cell campaign has no reports directory"
    }
  },
  "pending_critic_disposition": {
    "schema_version": "p3-autonomous-workload-trial-pending-critic-disposition/v1",
    "action": "discarded",
    "reason": "cell-admission-failure",
    "count": 0
  }
}
```

これは producer 実出力の主張ではなく、述語への具体的な構成例である。現行は root 無しなら `C:5075`、root 有りでも campaign directory 不在で `C:4255` が拒否する。directory だけ作っても Layer-3 不在を `C:4374` が拒否する。一方、plan はこの不在を診断成功の対象とする。

**成果物影響：従来は例外／CLI 非零だった report が、新 flag では receipt／CLI 成功になり、standalone の成功集合が増える。**

plan はこの変更を既に申告している。修正対象は親の契約・完了条件であり、opt-in や `certifying:false` 自体を「受理集合不変」の証拠にしてはいけない。

## real だが scope 外

**既存 failure-chain の「campaign ID/path 内部整合」は、ID が単一 path component であることまで保証しない。**

`C:4895` は ID の非空文字列・重複だけを検査し、`C:4907` は path 結合を行う。上例の `campaign_id` を `campaign_root` と同じ絶対パスにすると、絶対パスが左辺の `output_root / "campaigns"` を置き換える。failure 分岐は `C:4923` で抜け、後続の `_check_cell_campaign_identity` には進まない。

**成果物影響：宣言 root の不在・非 admitted は検査できても、その場所が `campaigns/<単一ID>` 配下だという参照保証は成立しない。**

これは既存 chain の性質であり、この wave で強化を要求する所見ではない。ただし `s2-plan.md:114` の「内部整合」をその強さで説明するのは過剰。

## 反証した攻め

- **admitted／混在／no-build／decision 無しが新分岐を通る：反証した。** `s2-plan.md:87` の build・単一 cell・厳密 failed decision と、先行する `C:3134` 以降の decision 検査が排除する。空 cells も新述語には入らない。
- **persisted Layer-3 がある cell が新経路で成功する：反証した。** 述語だけなら該当するが、plan が再利用する `C:4912` は実ファイルと dangling symlink の双方を拒否する。述語成立と最終受理は別。
- **registry の certifying 受入を新 flag だけで迂回できる：反証した。** `R:6264` と `R:6290` は chain／cross-binding を直接呼ぶ。files API の receipt を受入証拠として使う配線はない。将来の呼出変更や投影外の自動化については未確認。
- **厳密 key 判定が候補集合上で恒真：反証した。** 上例に `"cell-extra": true` を一つ足すと、`C:2534` の required-key 検査では排除されないが、plan の四つの完全一致集合から外れる。対して decision／disposition の厳密性は先行検査にも含まれるため、新機構固有の防護とは数えない。
- **既存二免除が暗黙に拡大する：反証した。** `s2-plan.md:101` は既存経路を優先し、述語も変更しない。`C:5062` の非空条件があるため空集合の `all(...)` による拡大もない。
- **(b)(c) が外部 root 引数を必須とする：呼出箇所では反証した。** `_path_identity` は `C:528` で cwd 基準の `resolve()` を使う。(b) は宣言 root 配下を読み、(c) の引数はその root と固定 purpose だけ（`C:4918`）。ただし `require_admitted_campaign` の実装は投影外なので内部までは確認していない。
- **既存 root 必須負例が plan により反転する：静的には反証した。** `T:2353` のテストは flag を渡さず、admitted decision を使う。plan 通りなら従来の同じエラーに到達する。実走での「緑」は未確認。

## nit

- **負例の発火地点を区別すること。** `s2-plan.md:165` の opt-in 不在や admitted 拒否は入口での拒否が目的。一方、`:169` の persisted、`:170` の independent admission、provider 改変は対象検査まで到達して拒否する必要がある。別の先行エラーでも合格する広い `raises` では機構を検証できない。plan の変異試験方針はこの区別と整合する。
- **producer に関する独立確認は未完了。** `brief.md:47` の fallback 生成と `:51` の「残る穴」の網羅性は、producer が許可された五ファイルに含まれないため検証できない。plan の正常 return 経路や producer テストの mock に関する訂正も、独立確認済みとは扱わない。
- `brief.md:66` の被覆不足は指定テストファイル内では整合する。campaignless 正例 `T:5104` は chain 単体であり、files API の正例ではない。

## 総括

最も効く所見は、新経路が root 要求の解除以上の変更であり、standalone の成功集合を増やすこと。
chain の failure 分岐については (b)(c) を保持できるが、現行 cross-binding の成功は保持できない。
指定範囲では、admitted cell の流入や registry の certifying 受入への bypass は成立しなかった。
親の択一は、**別の非 certifying 診断成功として契約を変更するか、従来の成功集合維持を必須として案を戻すか**。
前者なら plan の方向は成立するが、内部 path 保証の説明を狭め、producer の実出力は親が確認する必要がある。
静的検査のみ。ファイル変更・pytest 実走は行っていない。