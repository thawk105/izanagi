# [T-1748] 追跡済み受領証の cross-binding leaf を現物から再導出して照合する

- wave: `dev-wave-t1748-receipt-leaf-binding` / branch `worktree-dev-wave-t1748-receipt-leaf-binding`
- 起点 main: `37cb5696b`
- 実装 commit: `ff958823e`
- 日付: 2026-09-07 〜 2026-09-08 (JST)

## 何が壊れていたか

追跡済み受領証を後から読む standalone verifier `verify_acceptance_receipt` は、manifest・registry・
lifecycle・各 trial の報告と attempt journal を再読して再ハッシュする一方、**cross-binding leaf
だけは受領証の中の leaf 値から aggregate を再計算して突き合わせるだけ**で、leaf の元になった
projection を現物から再導出していなかった。したがって leaf を任意の値へ差し替え、aggregate を
その値から作り直した受領証が検証を通った。発行時 (`trial_registry.py:6168` の
`verify_s8c_cross_binding`) の保証が、受領証の耐久保証になっていなかった。

**現行 main で生きていた証拠**: 既存 v5 fixture (`test_s8c_acceptance_receipt_v2.py:505`) は
6 本の leaf を `sha256("cross-binding-leaf-{i}")` という合成文字列に置いており、それで
`verify_acceptance_receipt` が成功していた。

## 何を直したか

current v5 の各 trial について、受領証が名指しし verifier が既に再読している report bytes と
attempt journal bytes から `verify_s8c_cross_binding` を呼び直し、返る `receipt_sha256` を
宣言 leaf と照合する。既存の aggregate 検査は削除も代用もせず残す。

**恒真でない理由**: 照合の左辺は現物 (report・journal・build のとき campaign 実体) から導かれ、
右辺は受領証の宣言値である。受領証の leaf は再導出の入力に 1 bit も入らない。leaf と aggregate を
揃えて差し替えても左辺は変わらない。

## 鍵になった実測 — 引数はすべて受領証から復元できる

段 1 brief は「build mode では campaign 実体に到達できないので完全な再導出は不可能」と見立てて
いたが、これは**誤り**だった。親が発行側を辿って反証し、段 2 と段 3 レンズ B が独立に同じ結論に
達した (3 者一致)。

| 引数 | 発行側 | 受領証からの復元 |
|---|---|---|
| `report` | `item.report` | `trial.report_path` を再読 (verifier が既に再読・再ハッシュ済み) |
| `events` | journal の JSONL | `trial.attempt_journal_path` を再読 (同上) |
| `run_root` | `item.journal_path.resolve().parent` (`trial_registry.py:6081`) | `attempt_journal_path` の解決済み path の親 |
| `output_root` | `campaign_roots[0].parent.parent`。`run_root.parent.parent` との一致を `trial_registry.py:6133-6137` が強制 | `run_root.parent.parent` |

この事実により、成果物を増やす案 (leaf の preimage を sidecar として永続化する) は不要になった。

## 射程 — current v5 に限る

修正は `schema_version == p3-8c-trial-acceptance-receipt/v5` にだけ効く。legacy v3/v4 は従来どおり
aggregate のみを検査する。**「`verify_acceptance_receipt` 全体で任意 leaf が通らなくなった」とは
書けない。** 成立する主張は「current v5 と、そこから伸びる下流 capability 経路について、
cross-binding leaf の発行時保証が耐久保証になった」までである。

legacy へ広げなかった理由は 2 つ。(a) 唯一の production consumer
`layer3_report.build_accepted_report` は `require_current_verified_receipt` を通し、同関数が v5 以外を
無条件拒否するため、legacy は下流のどの capability にも到達しない。(b) legacy の再導出には当時の
campaign 現物が要り、失われていれば読めなくなる — readable compatibility の不当な縮小になる。

段 3 レンズ A の唯一の must-fix はこの射程不一致であり、実装を広げるのではなく主張の書き方を
正確にすることで閉じた (段 4 裁定)。

## 実測

| 走行 | 結果 |
|---|---|
| 変更前の焦点走 (receipt v1/v2 + trial_registry) | 289 passed / 76.07s (request 981683.nqsv) |
| 変更後の焦点走 (上記 + layer3_report + spawn_sites + duration ledger + plain runner) | 577 passed / 97.63s (request 981769.nqsv) |
| `test_s8c_acceptance_receipt_v2.py` 単独 | 39 passed。新設の負の対照が PASSED を名前で確認 |
| `test_trial_registry.py` 単独 | 229 passed |
| 全史 provenance 監査 | 8543 件、新規違反なし |
| 変異 matrix | baseline PASSED・KILLED 8・SURVIVED 0・MISMATCH 0・期待 node 完全一致 8/8 |

## 変異 matrix

`mutation-spec.json` と `mutation-ledger.json` が正本。8 変異はすべて
`orchestrator/campaign/s8c_acceptance_receipt.py` の新設面に当てた。

| # | 変異 | 殺した node |
|---|---|---|
| M1 | leaf 照合の block を丸ごと無効化 | 新設の負の対照 1 件 |
| M2 | 期待値を再導出値でなく宣言 leaf 自身にする (自己照合化) | 同 1 件 |
| M3 | 照合の向きを反転 (正当な受領証を拒否する向き) | 15 件 (v2 の 13 + registry の 2) |
| M4 | schema guard を v5 から v4 へずらし v5 で発火させない | 新設の負の対照 1 件 |
| M5b | 最後の trial だけ leaf 照合を飛ばす | 新設の負の対照 1 件 |
| M6 | 再導出へ渡す journal events を空にする | registry の 2 件 |
| M7 | `run_root` を journal の親でなく repository root にする | registry の materialized build 1 件 |
| M8 | build report を no-build へ強制し常に no-build leaf を作る | 同 1 件 |

**M3 が受理集合を縮小する wave に要求される「承認外の過剰拒否」の正例**である。

M1 / M2 / M4 / M5b が**新設の負の対照 1 件だけ**を殺したことが、その 1 件がこの機構を単独で
見張っている証拠になる。M6 / M7 / M8 は発行経路を通る実物のテストを殺しており、発行側と検証側が
独立に引数を導いていることを示す。

**恒真な正例についての注記 (段 6 レビュー B 所見 3)**: `_upgrade_to_current` が作る no-build 正例は、
production と同じ計算を同じ引数で 2 回やっているだけなので**それ単体では引数導出の正しさを
証明しない**。意味を持たせているのは materialized build 側の正例
(`test_trial_registry.py::test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads`)
で、発行経路と検証経路が別々に引数を導く。M7 / M8 がこの正例だけを殺すことが、その穴が
埋まっている実測である。

## 手落ちと是正

1. **M5 の初回登録が過剰決定だった。** `receipt.trials[:-1]` で loop 自体を短くしたため、leaf 照合
   以外の digest 照合まで飛び、22 件が赤くなった。`DW-M03` に従い、最後の trial の**leaf 照合だけ**を
   飛ばす M5b へ差し替え、単一理由 (新設の負の対照 1 件) に絞り直した。
2. **M3 の期待 node が 2 件足りず初回 MISMATCH になった (attempt 2)。** login 自走 probe を
   「変異ごとに必要な 1 file だけ」に絞った結果、M3 で `test_trial_registry.py` 側の 2 件を
   観測できていなかった。本走は両 file を走るので 15 件赤くなり、登録した 13 件と一致しなかった。
   実測 15 件で登録し直して attempt 3 で完全一致。**照合の向きを反転する変異のように「正当な
   受領証をすべて拒否する」型は、対象 file を絞った probe では期待集合を確定できない。**
3. **変異 harness の起動が attempt 1 で rc=2 になった。** 計算ノード混雑時に付けた D612 の
   queue-wait 上書き (3600+600=4200 秒) が、変異 spec の `timeout_seconds` (2400) を超えており、
   harness が起動前に拒否した。queue が空いた時点で上書きを外して解決。

## 逐語

- `verbatim/s1-brief.md` — 段 1 brief
- `verbatim/s1-brief-addendum.md` — 親の実測補遺 ((P1-b) の反証)
- `verbatim/s2-plan.md` — 段 2 プラン
- `verbatim/s3-lensA.md` — 段 3 レンズ A (恒真性)。must-fix 1
- `verbatim/s3-lensB.md` — 段 3 レンズ B (過剰拒否と scope)。must-fix 0
- `verbatim/s4-adjudication.md` — 段 4 裁定
- `verbatim/s5-author.md` — 段 5 実装子の報告
- `verbatim/s6-reviewA.md` — 段 6 レビュー A (裁定一致と防壁弱体化)。must-fix 0
- `verbatim/s6-reviewB.md` — 段 6 レビュー B (負の対照の検出力と巻き添え)。must-fix 0

## 子の工数

codex 6 本 (plan 1・consult 2・author 1・review 2)。全て `launcher_rc=0`。
model は全段 `gpt-5.6-sol`、reasoning は plan / consult が `xhigh`、author / review は docs 権威導出。
