## must-fix (成果物影響を 1 行で書けるもの)

**1. `proposal` の存在だけで producer 状態の確認を迂回できる。裁定 (D) 違反。**

根拠: [autonomous_trial_completeness.py:5115](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1232-impl/orchestrator/campaign/autonomous_trial_completeness.py:5115)。

`"proposal" in generation` なら即 `continue` するため、preview・harness の不在と role 履歴の整合性を確認しません。後続の `_cross_binding_proposals` は bytes・hash・格納ディレクトリ・wire を検査しますが、proposal 内の planner/coder と当該 generation の role 結果との一致は検査しません。

さらに producer は [p3_autonomous_workload_trial.py:4409](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1232-impl/orchestrator/campaign/p3_autonomous_workload_trial.py:4409) で、`arm_execution is not None` の場合だけ proposal 参照を report に記録します。新述語は逆に `arm_execution` を禁止しており、この宣言を許す根拠がありません。

**成果物影響:** 実 producer の早期失敗 report に、role 履歴と結び付かない proposal 参照を追加しても、診断成功 receipt を取得できる受理集合になります。

静的反例の cell 構造は以下です。`c` は新テストの `_failure_only_producer(..., mode="roles")` が返す元 cell、`g` はその最初の generation。既存値を保存し、proposal だけ追加します。

```python
{
    "workload": c["workload"],
    "workload_flags": c["workload_flags"],
    "perf_config_scale": c["perf_config_scale"],
    "descriptor": c["descriptor"],
    "descriptor_binding": c["descriptor_binding"],
    "campaign_id": c["campaign_id"],
    "campaign_root": c["campaign_root"],
    "generations": [{
        **g,
        "proposal": {
            "path": str(run / "proposals" / "injected.json"),
            "sha256": injected_bytes_sha256,
        },
    }],
    "stop_reason": c["stop_reason"],
    "admission_decision": c["admission_decision"],
    "pending_critic_disposition": c["pending_critic_disposition"],
    "error": c["error"],
}
```

`injected.json` を canonical JSON として、例えば次の内容とその正しい hash で用意します。

```json
{
  "planner": {"axis": "silo-backoff-trigger-gating"},
  "coder": {
    "axis": "silo-backoff-trigger-gating",
    "wire": "00000",
    "justification": "unrelated proposal",
    "confidence": 0.5
  }
}
```

cell の厳密 key 集合は維持されます。共通検査の role/accounting は無変更で、proposal helper の現行検査にも適合します。preview・auditor が存在しない早期失敗なのに proposal 宣言を受理します。これは実行済み再現ではなく、静的な到達経路の構成です。

この経路では proposal 宣言を拒否する方向へ狭め、追加参照を拒否する負例を置くのが producer の現物に沿います。実装報告 [s5-author.md:27](/work/1/SFC/tanab/dev-wave-jobs/t1232-rootless-failure-report/artifacts/t1232-rootless-failure-report/s5-author.md:27) の導出は、保存時点だけでなく、この宣言条件も含めて訂正が必要です。

## real だが scope 外

- **絶対 `campaign_id` による包含保証の欠如。** [autonomous_trial_completeness.py:4907](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1232-impl/orchestrator/campaign/autonomous_trial_completeness.py:4907)。例えば `campaign_root="/tmp/outside"`、`campaign_id="/tmp/outside"` なら、導出した `output_root` に関係なく `output_root / "campaigns" / campaign_id` は `/tmp/outside` になります。
  **参照への影響:** `campaigns/<ID>` 外の directory が failure campaign の検査対象になり得ます。既存 chain の性質であり、新 gate は要求しません。receipt の `declared-campaign-layer3-chain` と `campaign_output_root_binding:"not-verified"` は、この包含保証を申告していません。

## 反証した攻め

- **既定・rooted・既存免除の弱体化:** [autonomous_trial_completeness.py:5168](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1232-impl/orchestrator/campaign/autonomous_trial_completeness.py:5168) の4条件がすべて必要です。`False`、`True` 以外の値、root 指定、既存2免除では新 helper に入りません。提供差分では従来処理も残っています。受理・拒否の変更は見つかりませんでした。

- **accounting の素の例外:** helper 単独なら `:5088` は `KeyError`／`TypeError` を起こせますが、公開 API は先に `:2331` の Mapping、厳密 keys、非負 exact int 検査を通します。欠損・型不正は構造化 `_fail` になります。CLI の `:5242` が捕捉する例外に収まり、この入力から traceback が漏れる経路は成立しません。

- **generation／roles の欠損・型不正:** `:5060`〜`:5061` 単独の `.get()` は安全ではありませんが、先行する `:2594`、`:2605`、`:2613`、`:2625` が list／Mapping／role entry を検査します。非 Mapping の generation や欠損 roles は新述語へ到達しません。

- **proposal 不在側の presence-only 判定:** `:5120` は preview/harness が欠けたら無条件成功、ではありません。role 集合と `supervisor-error` も要求します。空 generation 集合ではループが空になりますが、共通状態機械・accounting 検査が残ります。問題は上記 must-fix の **proposal 存在側**です。

- **role 名の追加による fail-open:** `:5121` の固定集合外の role は、proposal 不在なら拒否されます。現在は共通 role-prefix 検査も存在します。将来 role が増えた場合も、この条件は受理を広げず狭めます。

- **provider/raw の不在を素通り:** `:5093` は exploratory と矛盾する provider 宣言を拒否し、`:5105` は valid role ごとに raw の参照と bytes を必須検査します。0 role も accounting 一致が必要です。

- **receipt の恒常的な過剰申告:** `:5187` の checks は、0件の場合も件数・不在条件を検証する契約として読めます。Layer-3 chain も実際に呼ばれます。ただし must-fix の入力では proposal の producer 状態との整合が未証明です。

- **裁定 (G):** diagnosis は許可 key 集合に含まれず、追加負例もあります。狭める選択は守られています。提供差分上、(A)(B)(C)(E)(F) に違反は見つかりませんでした。

## nit

- **既存テスト不変・編集面 (H) は確認未了。** [impl.diff:1](/work/1/SFC/tanab/dev-wave-jobs/t1232-rootless-failure-report/impl.diff:1) から末尾まで、差分は検証器1ファイルだけです。テスト現物だけでは [s5-author.md:7](/work/1/SFC/tanab/dev-wave-jobs/t1232-rootless-failure-report/artifacts/t1232-rootless-failure-report/s5-author.md:7) の「既存本文無変更」を比較確認できません。成果物の変更を立証していないため DW-G05 として分離します。
- 新テスト部分には現行 hash の fixture 差し込みや揮発 payload の焼き込みは見つかりませんでした。`:5807` の `raises` は後で既定経路の例外文字列と完全比較しており、広い捕捉だけで緑にする形ではありません。実走結果は追認していません。

## 総括

静的レビューでは must-fix 1件です。
proposal の存在だけで状態確認を飛ばす経路が、裁定 (D) の閉じた受理拡大を破っています。
既定・rooted 経路の弱体化と、指定された欠損値からの公開 API の素の例外流出は反証しました。
diagnosis を除外する裁定 (G) は守られています。
テスト不変と編集面全体は差分不足で未確認です。pytest その他の検査は実行していません。