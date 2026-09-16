## 所見ごとの closed / partial / regressed 表

以下は**静的再レビュー**です。pytest・変異・現物 CLI は実行していません。fix 報告の試験結果も独立認定していません。

参照略号：

- `caller` = [orchestrator/campaign/p3_b4_prerun_caller.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-prerun-issue-caller/orchestrator/campaign/p3_b4_prerun_caller.py)
- `test` = [orchestrator/tests/test_p3_b4_prerun_caller.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-prerun-issue-caller/orchestrator/tests/test_p3_b4_prerun_caller.py)
- `issuer` = `orchestrator/campaign/p3_b4_prerun_issuer.py`
- `ruling` = 射影の `s6-ruling.md`
- `fix` = 射影の `s6-fix.md`

| 所見 | 判定 | コード・記録による検算 |
|---|---|---|
| A1：欠落元の誤参照 | **closed** | `caller:99`・`:100` はともに `None`。候補位置は `:95`〜`:97` に残る。`test:125`〜`:129` は候補位置と null の両方を検査する。 |
| A2：`RecursionError` 漏れ | **closed** | `caller:82` が捕捉し、`:83` で `CampaignInputUnreadable` に変換。`:150`〜`:156` で JSON／rc=2 へ到達する。`test:236`〜`:240` は深い JSON が実際に `RecursionError` を起こす前提も検査する。 |
| A3：診断感度 pin の記録 | **partial** | `ruling:7`・`:36`・`:37`・`:42`、`fix:19` は分類を訂正済み。コード上も M3／M4 は残る11項目で `caller:158` の停止を維持し、M9 は `:140` の出力項目だけを除く。ただし、要求された **insight／worklog への別枠記録は確認できない**。今回の差分も実装・test の2ファイルだけである。親の記録作業が残る。 |
| A4：M10 の具体化 | **closed** | `ruling:43` の置換対象が `caller:116` に一意に存在する。全 planned path が同じになり、`issuer:420`〜`:424` の `PLANNED_RESULT_PATH_DUPLICATE` に到達。`test:191` の `rc == 0` が赤になる。実測認定は別途必要。 |
| B1：未使用3 field の必須化 | **closed** | `caller:78` は dict と `iteration`／`result` の存在だけを検査。最小 rejected 行は `test:135`、result 欠落は `:234`、非 dict 行は `:242` で検査する。 |
| B2：静的分類と探索結果の混同 | **closed** | `caller:56`〜`:59` が保存形式の既知の制限に基づく静的分類、個別 artifact 探索ではないこと、null の理由を明記する。 |

**regressed と判定する所見はありません。**

## 回帰

**例外捕捉の拡張は限定されています。** `caller:82` は `RecursionError` を追加しただけで、`KeyboardInterrupt`・`SystemExit`・`GeneratorExit` を捕捉しません。一般の `RuntimeError` や `MemoryError` も捕捉対象には増えていません。`issue()` 側も従来どおり `B4PrerunIssuerError` だけを捕捉します（`caller:131`）。

**`{"iteration": 1, "result": null}` は解釈可能な非候補行になります。** `caller:78` の存在検査を通り、`:80` の文字列 `"rejected"` との比較は偽です。この行だけなら候補0、空 batch の発行器呼出しへ進みます。今回の裁定は result の型・列挙値検証を追加せず、厳密に `"rejected"` だけを候補にするものなので、正しい挙動です。段5の5-key 行でも result の型検査はなかったため、型判定の回帰でもありません。

**null 化後の候補所在は十分です。** 読むファイルは `campaign_root / "loop_state.json"` に固定され（`caller:64`）、`whiteboard_index` が配列位置を指し、`iteration` がその行の記録値を保持します。iteration が重複しても index で区別できます。相対 campaign root の再現には実行 cwd の記録が必要ですが、これは null 化以前からの性質です。

候補が n 件あれば欠落は12n件で、n>0なら発行器へ進みません（`caller:93`〜`:106`、`:158`）。後続 campaign が読めなければ全体が typed stop します。fix による途中発行経路はありません。

## 変異 anchor と M5 / M8 の具体置換

実装ファイルに対する `grep -F -c` で、下表の逐語は**すべて1行だけ**に存在しました。各行内にも重複はありません。M5 は v2 に old 逐語が未定義なので、今回の具体案の anchor を検査しています。

| ID | old 逐語／対象 | 行 | 件数 |
|---|---|---:|---:|
| M0 | `# All twelve sources are absent in the current storage format.` | 92 | 1 |
| M1 | `if row["result"] == "rejected":` | 80 | 1 |
| M2 | `if missing:` | 158 | 1 |
| M3 | 下記 `bootstrap_member` の全行 | 32 | 1 |
| M4 | 下記 `arm_digest_received` の全行 | 37 | 1 |
| M5 | `        batch, missing, campaigns = collect_scheduled_batch(args.campaign_root)` | 149 | 1 |
| M6 | `issuer._REPOSITORY_ROOT / "output/b4-prerun-publication"` | 124 | 1 |
| M7 | `}, 2` | 135 | 1 |
| M8 | `payload, rc = issue(batch)` | 162 | 1 |
| M9 | `"manifest_row_count": len(publication.manifest.rows),` | 140 | 1 |
| M10 | `f"{attempt.attempt_id}.json"` | 116 | 1 |

M3／M4 の old は、それぞれ次の全行と改行です。new は空文字列です。

```python
    "bootstrap_member": "No evidence of initial proposal membership in a bootstrap set fixed in advance.",
```

```python
    "arm_digest_received": "No per-attempt record establishes digest receipt or non-receipt.",
```

**M5 の具体案**

`caller:148`〜`:149` の次の old を置換します。

```python
    try:
        batch, missing, campaigns = collect_scheduled_batch(args.campaign_root)
```

new：

```python
    try:
        batch, missing, campaigns = (), (), ()
        for root in args.campaign_root:
            campaign_batch, campaign_missing, campaign_info = (
                collect_scheduled_batch((root,))
            )
            batch += campaign_batch
            missing += campaign_missing
            campaigns += campaign_info
            if campaign_info[0]["rejected_rows"] == 0:
                payload, rc = issue(())
                if rc != 0:
                    payload.update(
                        candidate_count=sum(
                            campaign["rejected_rows"] for campaign in campaigns
                        ),
                        campaigns=campaigns,
                    )
                    print(json.dumps(payload, sort_keys=True))
                    return rc
```

`issue()` は発行器例外を捕捉して rc=2 に変換するため、ここではその戻り値で最初の例外からの早期終了を表現します。

- T1：最初の campaign で拒否されて戻り、`test:94` の全3 campaign の集計期待が赤になります。**呼出し回数は1回のまま**であり、複数回呼出し検査が赤理由ではありません。
- T2：先頭 success campaign で発行器に到達し、`test:109` の不足報告 reason 期待が赤になります。
- T3：campaign が1個なので、元と同じ空 batch 拒否・1回呼出しになり、赤にはなりません。

**M8 の具体置換**

old：

```python
            payload, rc = issue(batch)
```

new：

```python
            payload, rc = (issue(batch) if batch else ({"issued": None}, 0))
```

T1／T3 はいずれも batch が `()` なので、発行器を呼ばず rc=0 を返します。最初に赤になるのは、それぞれ `test:91`、`:153` の **rc=2 期待**です。`issued: null` の検査に依存しません。候補ありのテストは `if missing:` 側に入り、T5 は `issue()` を直接呼ぶため、この変異に影響されません。

## 変異ごとの期待 node 完全集合

以下は**各変異を単独適用した場合の静的予測**です。M5 は上記の具体案に固定します。

全 node の共通接頭辞は `orchestrator/tests/test_p3_b4_prerun_caller.py::` です。表の「赤になる変異」以外では、その node は赤にならない予測です。`∅` は M0〜M10 のすべてで赤にならないことを表します。

| 略号 | node 名 | 赤になる変異 |
|---|---|---|
| T1 | `test_success_only_campaigns_reach_issuer_once_with_empty_batch_and_no_root` | M5, M6, M7, M8 |
| T2 | `test_mixed_campaigns_report_all_missing_sources_and_never_call_issuer` | M2, M3, M4, M5 |
| Tmin | `test_minimal_rejected_row_is_a_candidate` | M2, M3, M4 |
| T3 | `test_fail_row_is_not_a_candidate` | M1, M6, M7, M8 |
| T4 | `test_publication_root_is_not_an_argument` | ∅ |
| T5 | `test_issue_half_serializes_real_receipt_for_a_complete_batch` | M6, M9, M10 |
| U1 | `test_unreadable_campaign_never_calls_issuer[checkpoint_absent]` | ∅ |
| U2 | `test_unreadable_campaign_never_calls_issuer[lock_absent]` | ∅ |
| U3 | `test_unreadable_campaign_never_calls_issuer[json]` | ∅ |
| U4 | `test_unreadable_campaign_never_calls_issuer[whiteboard]` | ∅ |
| U5 | `test_unreadable_campaign_never_calls_issuer[trial]` | ∅ |
| U6 | `test_unreadable_campaign_never_calls_issuer[row]` | ∅ |
| U7 | `test_unreadable_campaign_never_calls_issuer[result_absent]` | ∅ |
| U8 | `test_unreadable_campaign_never_calls_issuer[deep_json]` | ∅ |
| Tall | `test_all_candidates_have_all_missing_fields` | M2, M3, M4 |

この対応から得られる、変異ごとの赤 node 完全集合は次のとおりです。

| 変異 | 赤 node 完全集合 | 静的根拠 |
|---|---|---|
| M0 | ∅ | 通常コメントの本文変更だけで動作不変。 |
| M1 | `{T3}` | `"fail"` が候補になり、不足報告へ変わる。その他の正常行は success／rejected のみ。 |
| M2 | `{T2, Tmin, Tall}` | 不足停止を迂回し、空 batch の発行器拒否になる。T2／Tmin は reason 不一致、Tall は `missing` 欠落で赤。 |
| M3 | `{T2, Tmin, Tall}` | T2 は field 集合不一致、Tmin は11件≠12件、Tall は33件≠36件。 |
| M4 | `{T2, Tmin, Tall}` | M3 と同じ件数変化。欠落する field は `arm_digest_received`。 |
| M5 | `{T1, T2}` | 先頭の候補0 campaign で早期終了。 |
| M6 | `{T1, T3, T5}` | fixture の cwd は `elsewhere`、事前登録 root は `repository`。`issuer:218` の名指し検査で拒否。T1／T3 は reason 不一致、T5 は rc 不一致。 |
| M7 | `{T1, T3}` | 発行器拒否の rc が0になる。入力解釈不能・不足停止の rc=2 は変更されない。 |
| M8 | `{T1, T3}` | 空 batch で発行器を省略し rc=0 を返す。 |
| M9 | `{T5}` | `test:194` の `issued` key 集合一致が赤。発行内容・受理集合は変わらない。 |
| M10 | `{T5}` | 201個の planned path が重複し、発行器拒否で rc=2 になる。空 batch では path が生成されない。 |

**裁定 v2 の M2 期待集合には Tmin の追加が必要です。** M3／M4 の括弧書きも、完全な nodeid として登録する必要があります。

U1〜U8 はすべて、入力解釈の段階で `CampaignInputUnreadable` になります。M5 の案でも、各ケースは唯一の campaign を読み終える前に止まるため `issue(())` に到達しません。T4 は argparse が collection 前に拒否します。

M3・M4・M9 の赤は**診断感度 pin**です。fail-closed の検出力には加算しません。DW-M08 の実測での完全一致は、親の probe で確定する必要があります。

## 現物予測の再確認

現物の checkpoint／lock を再読しました。

| campaign（`output/campaigns/` 以下） | trial | whiteboard 行数 | result | rejected |
|---|---|---:|---|---:|
| `p3-s4-loop-s4-autonomous-0b53a387` | `p3-s4-loop` | 4 | 全 success | 0 |
| `p3-s5-sort-loop-s5-sort-autonomous-3be89e0d` | `p3-s5-sort-loop` | 1 | 全 success | 0 |
| `p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5` | `p3-s8a-trigger-loop` | 2 | 全 success | 0 |

全7行に `iteration`・`direction`・`magnitude`・`result`・`delta_pct` があります。sort の最上位 iteration は2ですが、報告する whiteboard 行数は1です。

fix 後も、候補0 → `missing == ()` → 空 batch で発行器へ1回到達、という予測は変わりません（`caller:80`、`:106`、`:162`）。先行する発行器検査と乱数取得が成功する条件で、結果は次のままです。

- `reason`: `"design_not_feasible"`
- `detail`: `"fewer than 201 eligible scheduled attempts"`
- `candidate_count`: `0`
- `campaigns`: 入力順で base／sort／trigger、行数4／1／2、rejected 各0
- 終了コード：**2**

読取り時点で `output/` は存在し、`output/b4-prerun-publication` は不在でした。空 batch は `issuer:840`〜`:844` で拒否され、`:882` の公開処理へ進まないため、この経路では publication root を作りません。実行後の確認は未実施です。

## 総括

**実装修正の A1・A2・B1・B2 と M10 の具体化は closed。回帰は見つかりません。A3 は insight／worklog の記録確認が残るため partial です。**

親への引継ぎは、M2 の期待集合への Tmin 追加、上記 M5 具体置換の採用、全15 node に対する変異 probe、診断感度 pin の別枠記録です。現物の予測は引き続き候補0・空 batch・`design_not_feasible`・rc=2です。

ファイル作成・編集、git 状態変更、pytest・変異・現物 CLI の実行は行っていません。