安定した root に対する**受理集合の反例は見つかりませんでした**。ただし、裁定が要求した検証成果物に must-fix が2件あります。production の修正を要求する所見ではありません。

以下、H＝[変更後 module](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2802-floor-attempt-recovery/orchestrator/campaign/s8b_holdout_admission.py)、T＝[変更後 test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2802-floor-attempt-recovery/orchestrator/tests/test_s8b_holdout_admission.py)、B＝指定 base module、P＝[差分 probe](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2802-floor-attempt-recovery/probe/t2802_diff_probe.py) です。

静的検査のみ実施しました。提供ログでは admission **282 passed**、consumer **2522 passed / 16 skipped**、差分 probe **24/24一致**です。受入全走・変異実測・性能測定の証拠とは区別します。

## must-fix

### MF1. N1 の期待文書が production constructor と独立していない

- **根拠:** T:1849–1853、1868、2848、2855。新規 N1 の `expected` は `_floor_expected_marker` → production の `_floor_attempt_document_for_state` から生成されます。裁定 §1 A-S1・§4.1 は固定 literal の期待文書を要求しています。
- **成果物への影響:** constructor の同じ誤りを実測値と期待値が共有でき、「固定期待文書で不変性を固定した」という裁定上の説明が成立しません。message の固定性には問題ありません。
- **是正案:** N1 の期待文書を test 側で独立に構成してください。schema・event・role・キー集合は literal、fixture に依存する digest 等は fixture の入力・発行済み値から明示的に組み立て、production の文書 constructor を期待値生成に使わない形にします。

### MF2. 差分 probe の正例対照が、指定された M1 変異になっていない

- **根拠:** P:196–203 は候補関数全体を `return dict(expected_marker)` に置換します。P:276–277 は変更後 module での `--selftest` を拒否します。提供結果の `positive_control` は `null`。裁定 §4 は **M1 形の一時変異で差分検出する実走**を要求しています。
- **成果物への影響:** 比較器が大きな差を検出できることと、今回の memo hit の弱体化を検出できることが混同され、裁定指定の検証が未成立になります。
- **是正案:** 下記 M1 を独立した変異 source に適用し、通常モードの probe を実走してください。`e-later-nontarget-marker-campaign_run_id` で base が元の全文 message により拒否し、変異側が受理して不一致になることを保存します。既存 stub 対照を残しても、M1 対照の代用にはしません。

## should

### S1. 差分 probe に「各 claim 複数 attempt」と legacy の系列を追加する

- **根拠:** P:125–165 は1 claim・3 attempt、P:240–260 の追加 claim は1 attemptです。legacy fixture は利用していません。
- **成果物への影響:** 24状態一致の射程は generation 中心であり、複数 claim の miss/hit 混在と legacy の同値性を全面的に実測したとは書けません。
- **是正案:** 段6で次を追加すると有効です。
  - 2 claim × 各2 attempt、marker と A 行の双方に各 claim の hit を含む状態。
  - その非 target marker／A 行での coverage 不正。
  - legacy claim v1/v2 の正常 hit、membership 不正、無関係 floor 行不正。
  - 同一プロセスで正常呼出し→claim/main 改竄→再呼出しを、独立した結果名で記録。

なお、**hit coverage と2回目の呼出しが皆無という指摘は当たりません**。P:172–195 は同 claim の未登録 attempt を検査し、P:95 の実行順反転により各状態で current を2回呼びます。さらに状態間の改竄もあります。ただし、それを専用の寿命検証として明示した記録ではありません。

### S2. M8 の KILL 理由を「改竄拒否」に帰属させない

- **根拠:** T:3012–3025 の正常2呼出し・回数 assertion が、T:3026–3049 の改竄より先です。module singleton 化では全件実行中の別 root の履歴も混入できます。
- **成果物への影響:** `KILLED` を「同 root の改竄を検出した証拠」と記録すると変異台帳が不正確になります。author は回数 assertion の先行を正しく申告しています。
- **是正案:** 現行 N6 の帰属は「呼出し間保持を読取回数で検出」とします。改竄による受理集合の変化も帰属させるなら、回数 assertion と独立した node を用意し、新鮮なプロセスで正常呼出し→改竄→再呼出しを実走してください。全件走の赤とは別に最初の失敗位置を記録します。

## nit

### N1. 「context が例外経由でも漏れない」は厳密には強すぎる

- **根拠:** H:5339 のローカル変数は、例外が伝播した場合に通常の Python traceback の frame から参照できます。
- **成果物への影響:** insight でオブジェクトの絶対的な寿命保証を書くと過大になります。ただし次の候補呼出しで再利用する production 経路はありません。
- **是正案:** 「戻り値・closure・module state に公開せず、次回呼出しで再利用しない」と記述してください。traceback 対策の実装追加は不要です。

## 同値性・test・変異の確認結果

| 対象 | 静的判定と根拠 |
|---|---|
| hit coverage | H:4778–4785／4968–4977 で list 型・要素型・重複・membership を検査済みの projection だけが登録されます。同一 claim の安定した読取結果では、hit の membership 単独検査と同値です。 |
| 成功時だけ登録 | H:4735→4738、4899→4904。constructor／marker equality の失敗時に新しい projection を保存する経路はありません。main の生行列が先に保存されることとは区別できます。 |
| 遅延 main・順序 | B:4737／4946 → H:4795／5045。target claim／coverage の失敗より前に main を読みません。v1 全 floor 行検査は H:4799–4814 で miss ごとに残ります。 |
| authority の出所 | H:4843–4850／5018–5028 は claim・検証済み digest/key・manifest に由来します。marker の campaign 等は混入しません。digest は marker が選ぶ lookup identity ですが、claim identity と照合済みです。 |
| wrapper | H:4696、4858、5036 は `context=None`。H:5155／5162／5784 の既存 caller も維持。既存全関数 signature の AST 一致を確認しました。 |
| message | `rg` による floor consume／generation literal 集合は新旧一致。追加確認として module 全体の `raise` 式の AST 集合も差分なしです。 |
| N1〜N10 の期待 message | 全文 literal／固定 template は production と整合。N9 の `{name}` は fixture の実ファイル名だけを補間し、例外本文や揮発 payload から期待値を生成していません。 |
| 観測 wrapper | T:3002–3008 は元 reader に委譲します。DW-O14 に反する authority の差替えはありません。 |
| legacy・到達不能 | T:1899 に legacy 読取互換を明記。T:1875–1877 に3検査の到達不能性を記録し、偽の authority による負例はありません。 |
| 既存 test | patch の test 差分は追加2 hunkのみ、削除行なし。既存期待値の変更なしです。 |
| lock | consume H:4361→4372、query H:5448→5456 の lock 内で context を生成。新しい lock 外読取はありません。advisory lock を無視する変更や一過性 I/O の履歴同値は保証対象外です。 |

author の **9 anchor はすべて出現数1**でした。変異ごとの帰属は次のとおりです。ここでの KILL／SURVIVED は実測結果ではありません。

| 変異 | 判定 |
|---|---|
| M1 | N2 `[claim-mismatch]` は非 target・A不在なので後段の冗長 gate に捕まりません。旧 T:2729＝現 T:2796 も別 message で赤になり得るため、新規専有検出力に数えません。 |
| M3 | N2 `[attempt-not-covered]` は妥当な文字列・canonical filename。membership 削除後の別理由の拒否は見当たりません。 |
| M4 | N2 は複製でなく改名。identity 重複による二重帰属なし。 |
| M5 | N3 `[duplicate]` は正常 marker に対応する canonical A 行の重複。shape・orphan が先に拒否しません。 |
| M6g／M6v | N5 `[records-generation]`／`[records-v1]`・`[records-v2]` は records だけ変更。main equality に帰属できます。 |
| M7 | 旧 T:2750＝現 T:2817 の M+A−で検出。M+A+ の早期 `None` に遮られません。既存検出力です。 |
| M8 | 上記 S2。回数検出と改竄拒否を分離して記録します。 |
| P0 | H:5393 の constructor 成功後、identity の2値は検証済み文字列です。静的 JSON root で `str` 除去は等価です。 |

## 変異 spec 案

各変異は独立適用です。M8だけ同一変異内の2置換です。`old` / `new` はデコードして使う JSON 文字列です。

M1 は登録前の `memo_key in context.projections` で hit を判定するため、初回 miss を弱めません。

```json
[
  {
    "id": "M1",
    "old": "    expected = _canonical_measurement_generation_floor_attempt_document(\n        attempt_id=attempt_id, **projection.document_fields,\n    )\n",
    "new": "    fields = dict(projection.document_fields)\n    if context is not None and memo_key in context.projections:\n        fields[\"campaign_run_id\"] = marker[\"campaign_run_id\"]\n    expected = _canonical_measurement_generation_floor_attempt_document(\n        attempt_id=attempt_id, **fields,\n    )\n"
  },
  {
    "id": "M3",
    "old": "    elif attempt_id not in projection.attempt_ids:\n        raise HoldoutAdmissionError(\n            \"floor measurement generation claim attempt coverage is invalid\"\n        )\n",
    "new": ""
  },
  {
    "id": "M4",
    "old": "        if path != _floor_canonical_marker_path(root, canonical):\n",
    "new": "        if False:\n"
  },
  {
    "id": "M5",
    "old": "        if identity in ledger_by_identity:\n",
    "new": "        if False:\n"
  },
  {
    "id": "M6g",
    "old": "    if main != expected_main:\n        raise HoldoutAdmissionError(\n            \"floor measurement generation ledger differs from its claim\"\n        )\n",
    "new": ""
  },
  {
    "id": "M6v",
    "old": "    if main != expected_main:\n        raise HoldoutAdmissionError(\"floor consume main ledger differs from its claim\")\n",
    "new": ""
  },
  {
    "id": "M7",
    "old": "    if completed_attempt:\n",
    "new": "    if False:\n"
  },
  {
    "id": "M8",
    "edits": [
      {
        "old": "def _floor_attempt_recovery_candidate_locked(\n",
        "new": "_T2802_MUTATION_CONTEXT = _FloorAttemptRecoveryContext()\n\n\ndef _floor_attempt_recovery_candidate_locked(\n"
      },
      {
        "old": "    context = _FloorAttemptRecoveryContext()\n",
        "new": "    context = _T2802_MUTATION_CONTEXT\n"
      }
    ]
  },
  {
    "id": "P0",
    "old": "        identity = (\n            str(canonical[identity_field]), str(canonical[\"attempt_id\"]),\n        )\n        if identity in ledger_by_identity:\n",
    "new": "        identity = (\n            canonical[identity_field], canonical[\"attempt_id\"],\n        )\n        if identity in ledger_by_identity:\n"
  }
]
```

## 総括

**NO-GO：検証成果物に must-fix 2件。production の受理集合変更は見つからず。**
MF1：N1 の期待文書を production constructor から独立させる。
MF2：M1 形の実変異で差分 probe の検出対照を実走・保存する。
変異の KILL と帰属は未実測。今回の確認は静的レビューと提供ログの照合まで。
