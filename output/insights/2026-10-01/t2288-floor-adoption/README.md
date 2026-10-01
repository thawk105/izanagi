# [T-2288] B-4 床値 (floor-pair) の採用裁定 — 集約を採用し pin 値を確定したが、§5 floor セルへの記入は保留した (記入すると binary 未配置の checkout で材料レポートとその test が止まる)

`authority: none`
`default_effect: no-state-change`

2026-10-01。wave `dev-wave-b4-floor-adopt`、branch `worktree-dev-wave-b4-floor-adopt` (基点 local main
`5f9e8c549c1c1dcf8d26f3dae99486e0e0da223e`)。可変状態の正本は worklog 末尾と現行 phase doc であり、本書ではない。
時刻は UTC (成果物の field と `git log` から採り、推定していない)。

## 依頼と答え

依頼は「B-4 床値の採用裁定 (D1641 決定 2) を行い、採用なら事前登録
`docs/phase3-b4-reflux-ablation-preregistration.md` §5 の floor 欄へ集約の `artifact_path=…; sha256=…` を記入する。
docs のみ・計算 0。所有は floor 欄と自分の fragment だけ」だった。

**答え: 集約を採用し、pin 値を次で確定した。ただし §5 floor セルへの記入は本 wave では行わなかった。依頼は完了していない。**

```
artifact_path=output/env/pegasus/floor-pair/t2288-f1/b4-floor-aggregate__env-pegasus__protocol-silo__threads-48__workload-set-7095cfaaa30f9b4f5228__campaign-set-3553fb844072ea43111a.json; sha256=4896a1fd1735667c62a6ce8200d3f70faf9bc0d08e0afe7c6970e61f69d7dbdf
```

記入を試した木で B-4 系の test を走らせると 34 failed + 2 errors になり、記入を戻した木では同じ赤の file が全部緑だった
(下の「記入の試行」)。記入すると、spec が束縛する追跡外の binary を置いていない checkout では材料レポートが止まる。
これを直すには test の変更が要り、依頼の範囲 (docs のみ・所有 = floor 欄) を超える。

## 受理条件の照合 (親が実物で確かめたもの)

| 項目 | 確かめ方 | 結果 |
|---|---|---|
| 集約の実在と hash | `sha256sum`、`git ls-files --error-unmatch` | 実在・追跡済み (追加 commit `f315186c8`)、sha256 `4896a1fd…dbdf` は材料の値と全桁一致 |
| 床値 | 集約の `floor_exact` | `[436449544102615, 4503599627370496]` = 0.09691126658997518。0 以上 1 未満 |
| 1 窓・1 セルあたり n と欠測 (D1641 決定 3、D1695) | 6 本の窓 JSONL の終端行 (`jq`) | 6 本とも `terminal` / `complete` / `complete_sample_count 62` / `dropped_sample_count 0` / session 124 / measurement 248 |
| 2 窓の分離 24 h 以上 (D1974 項 3 が人手に残した項目) | c1 の session `finished_at` の最大と c2 の `started_at` の最小 | rr5 2026-09-19T13:49:12Z → 09-29T05:27:38Z、rr50 13:41:29Z → 05:27:26Z、rr95 13:41:57Z → 05:27:20Z (約 231.6〜231.8 h) |
| c1 の session 状態 | `status` の集計 | 3 workload とも 124 件すべて `complete` |
| 期待 spec 列 | 集約の `aggregation.expected_specs` と spec 3 本の `sha256sum` と D2138 項 7 の表 | rr5 `d13c3844…` / rr50 `b582d20c…` / rr95 `990e3a6f…` が 3 者で全桁一致 |
| spec の凍結が測定より前 | spec 追加 commit と w1 最初の session `started_at` | `0b4fbd7a6` (2026-09-17T21:58:18Z) < 2026-09-19T12:32:19Z |

**親が確かめていないもの。** 事前・中間・事後 probe の結果と binary sha256 が 1 種であることは、前 wave の証拠確認者
(D1641 決定 1) の記録 (`output/insights/2026-09-29/t2288-floor-pair-w2/README.md` の「証拠確認」) に依っている。
**事前無作為化は確認していない。** 同記録にも無作為化の確認は無い。読んだのは、spec が `randomization.algorithm =
hmac-sha256-rank/v1` と `seed_hex` を持ち、窓 JSONL の header が同じ algorithm と seed を写していることだけで、実行順が
その schedule に従ったかは見ていない。
spec と最初の測定の前後で照合できたのは、spec 追加 commit の記録時刻 2026-09-17T21:58:18Z が w1 の最初の `started_at`
2026-09-19T12:32:19.917452Z より前という順序だけである。期待列が本書の対象集合と意味的に一致すること、結果を見る前に
選ばれたことは機械的に証明されない (D1974 項 6、事前登録 §1 の限界)。

## 記入の試行 (記入した木と戻した木の対照)

- 記入した木 (floor セルに上の pin、未 commit): `python3 tools/run_tests.py -q` に B-4 系 16 file と
  `orchestrator/tests/test_check_docs.py` を渡し、自動判定で計算ノードへ回った (request `40678.nqsv`、Elapse 141 s)。
  結果 **34 failed, 1258 passed, 3 skipped, 2 errors**。内訳は `test_p3_b4_material_report.py` 31、
  `test_p3_b4_raw_record_producer.py` 3 (failed 1・error 2)、`test_p3_b4_floor_artifact_issuer.py` 1
  (`test_resolver_real_preregistration_is_absent`。docstring は「floor 登録 wave で更新する」)、`test_p3_b4_wiring_probe.py` 1。
- 記入を戻した木: 赤の出た 4 file だけを同じ方法で走らせ **259 passed** (rc=0、5 分 22 秒)。母集団は記入した木の走りと同一でない
  (16 file でなく 4 file)。どちらも受入形でない走りである。
- 赤の原因: runner の failure digest は 36 件中 11 件の抜粋を残し、25 件を予算で省略した。digest の 11 件のうち 10 件に共通するのは
  `binary b4-candidate を lstat できない` (`output/env/pegasus/binaries/7cdf0dc3…` が無い) で、うち 9 件は材料レポートの
  `authoritative_floor_rejected: spec_rejected_by_producer`、1 件は resolver を直接呼ぶ test の
  `B4FloorArtifactError: spec_rejected_by_producer`。残る 1 件は `test_source_and_test_are_the_only_non_output_worktree_changes`
  で、未 commit の事前登録の差分を「output 外の変更」として拾ったもの (floor の値や binary を見ていない)。digest に抜粋の無い 25 件のうち、
  `test_outputs_contain_no_combining_diacritic_codepoints` はログ冒頭に詳細が残り、同じ lstat 失敗だった。もう 1 件、ログ冒頭の
  切れた断片が `output/env/pegasus/binaries` の No such file を含む子プロセスの stderr と
  `test_p3_b4_material_report.py:1538: AssertionError` を残しており、1538 行は `test_cli_clean_subprocess_runs_twice_and_refuses_overwrite`
  の `assert first.returncode == 0, first.stderr` である。この test の原因を lstat 失敗とするのは、この断片と行番号からの推定で、
  test 名と例外の全文は残っていない。残る 23 件の原因は個別には確かめていない。
- 経路: resolver が pin を見つけると `load_authoritative_floor` が集約を出所から組み直し、期待 spec を
  `floor_pair_driver.load_frozen_spec` で読み直す。その中の checkout 入力の束縛が binary の実在・hash・receipt・calibration を
  検査する。binary は ignored file で merge では移らず、checkout ごとに `b4_binary_record place` で置く運用である
  (`docs/pegasus-runbook.md`、D2069 項 7)。実体は `/work/1/SFC/tanab/izanagi-b4-floor-binaries/binaries/` にあり、sha256 は spec の
  束縛値 `7cdf0dc3…` と一致した。binary を置いた checkout で記入後の test が通るかは確かめていない。

## floor_domain_error への影響 (一次資料とコードの範囲)

- **欄が `未記入` のまま (現在):** resolver は `None` を返し、評価器へ floor 不在が渡る。分析に到達すれば `floor_domain_error`
  (§5.1.1) → `analysis_invalid` → verdict 分岐 1 の protocol violation。現在と変わらない。
- **pin が検証を通る (binary を置いた checkout):** 正確な分数の floor が評価器へ渡り、floor 欠落による `floor_domain_error` の
  固定は外れる。他の理由 enum や分岐は変わらず、特定の verdict、§7.1 の 4 分類の実効化、B-4 の実走済みを意味しない。
- **pin が拒否される (binary を置いていない checkout):** 材料レポートは評価器を呼ばず `authoritative_floor_rejected` で生成を止める。
  分析 verdict 自体が出ない。
- 事前登録 §11.0 の追記 (2026-09-08) は「resolver が pin を拒否した場合は fail-closed で従来どおり floor 不在が渡り」と書くが、
  現行の `p3_b4_material_report.py` の `_load_and_evaluate` は resolver の `B4FloorArtifactError` を受けると
  `authoritative_floor_rejected` で失敗し、評価器を呼ばない。§11.3 の追記 (2026-09-17、D2103) も拒否される場合を書いている。
  §11.0 の当該文は現行コードと一致しない。事前登録は所有外なので本 wave では直していない。
- B-4 の還流 ablation は未実走で、「記述統計に限定し有意性を主張しない」(§5.1 の 2026-09-14 追記) は変わらない。

## submit-tree

依頼が撤去の可否を問うた `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2288-floor-pair-w1/submit-tree` は、本 wave の開始時点で
既に存在せず、`git worktree list` にも無い。撤去対象は無く、本 wave は撤去操作をしていない。撤去した主体と日時は確かめていない。

## 敵対相談 (read-only codex 2 本、逐語は `verbatim/`)

親の provisional 裁定 (`verbatim/s1-brief.md` の P1・P2) を 2 レンズで攻撃させた (レンズ A = 正しさ境界と整合、
レンズ B = 実効性と過剰・削除。どちらも静的検査だけでテストは走らせていない)。A は「記入保留は支持、ただし説明と完了扱いを
直す」条件で NO-GO、B は記入保留に限り GO。

| # | 所見 | 裁定 | 反映 |
|---|---|---|---|
| A1 | 受理条件の「全充足」は数値確認だけでは言えない (結果を見る前の選定、probe 等) | real・採用 | 上の表で親の確認と前 wave の記録に依る項目を分けた |
| A2 / B2 | 「全 checkout で 36 件が binary 原因」は一般化しすぎ | real・採用 | 「binary 未配置のこの木」「抜粋 11 件中 10 件」に絞った |
| A3 | wiring の 1 件は未 commit 差分型 | refuted (親の判断を支持) | — |
| A4 | binary 不在の拒否は現行契約どおり | refuted (親の判断を支持) | 欠陥とは書かない |
| A5 / B5 | 影響は受理と拒否で分けて書く。§11.0 追記は拒否時の挙動と不一致 | real・採用 | 上の「影響」節 |
| A6 / B2 | 依頼を完了と書けない | real・採用 | worklog は T-2288 を更新扱い |
| A7 | 保留は HARKing ではない (値と集合は固定のまま) | refuted (支持) | — |
| A8 | floor セルだけで有効登録と現行 test を両立する回避策は無い | refuted (支持) | — |
| B1 | 本 wave で記入して実装子に直させる方が筋か | refuted | 依頼の所有・docs のみの範囲を守る |
| B3 / B4 | 後続は test の文書入力の fixture 化 + 既存 place + 実文書回帰の更新 + 同じ commit で記入。binary 検査の省略や拒否を None に戻す案は規律 2 に反する | real・採用 | 次の一手と D の却下肢 |
| B6 | submit-tree は「既に存在せず撤去対象なし」で足りる | real・採用 | 上の節 |

**逐語の可逆な最小正規化 (`git diff --check` のため、可視文字は不変)。** `verbatim/consult-a.md` と `verbatim/consult-b.md` は
codex の出力から、行末の半角空白 2 個 (Markdown の改行指定) を削り、原文に無かった末尾の改行 1 byte を補った。

| file | 原文 sha256 / byte | 正規化後 byte | 空白 2 個を削った行 (正規化後の行番号) |
|---|---|---|---|
| `consult-a.md` | `070c595b0f5dd20069ef90f9e3e533000771bc1e3c77c463d49ae3bbcf4c61f8` / 8605 | 8570 | 3,4,7,8,11,12,15,16,19,20,23,24,27,28,31,32,37,38 |
| `consult-b.md` | `0a4a73e516a52e6f77616810e482c7fcd07e8b3580964471fecec6218f1afdd6` / 8297 | 8278 | 3,6,7,21,33,44,45,46,51,52 |
| `review.md` | `c4fc9b234ea280ac0022d5a45bf22f52cc65772f1ba04e42fea3735e083a3a4f` / 3514 | 3506 | 3,6,9 (加えて 11 行目は空白 3 個だけの行で、3 個を削った) |
| `focus.md` | `c085a47cdb7dabfc06c30d3cc834506a56f66f3676189cd7c72b269395f49797` / 3788 | 3785 | 11,14 |

復元は、表の各行の行末へ半角空白 2 個 (`review.md` の 11 行目は 3 個) を足し、末尾の改行 1 byte を除く (この手順で原文 sha256 に
戻ることを確かめた)。`s1-brief.md` と 4 本の prompt は原文のまま。

## 段 6 相当の read-only レビュー 1 本 (逐語は `verbatim/review.md`、prompt は `verbatim/review-prompt.md`)

記録 commit `f1500e274` の 8 file を一次資料と突き合わせる独立レビューを 1 本投じた (codex `review`、read-only、テストは走らせていない)。
レビューは集約と spec 3 本の sha256 を自分で計算して一致を確かめ、floor_exact・6 窓の終端件数・分離時間・焦点走と基準走の件数・
正規化表・fragment の文法も一致とした。結論は NO-GO (must 1)。親の裁定:

| # | 所見 | 裁定 | 反映 |
|---|---|---|---|
| 1 | 事前無作為化を前 wave の記録に依拠させたが、その記録に無作為化の確認は無い | real・must・採用 | 「確認していない」と書き、読んだのは spec の algorithm と seed だけと明記 (README・D fragment) |
| 2 | commit 時刻から「その時点に結果が無かった」とは言えない | real・should・採用 | 記録時刻の順序の照合だけに狭めた |
| 3 | 「抜粋 11 件」は failure digest 内の件数。10 件のうち authoritative_floor_rejected を伴うのは 9 件 | real・should・採用 | 内訳を書き直し、digest 外の 2 件の詳細も書いた |

焦点再レビュー (逐語は `verbatim/focus.md`、prompt は `verbatim/focus-prompt.md`) は所見 1・2 を closed、3 を partial とし、
should 2 件 (CLI の test の原因は断片と行番号からの推定にすぎない、「25 件は個別未確認」が追記と整合しない) を出した。
2 件とも real と裁定し、推定であることと 25 件の内訳 (2 件確認・うち 1 件推定、23 件未確認) を書き直した (README・worklog fragment)。

## 主張しないこと

- 集約の採用は、§5 floor 欄の記入でも事前登録の発効でもない。§5 は floor を含む 6 欄が `未記入` のままで、責任者行の開始時刻も
  `未記入` である。§6 の前提条件の充足も主張しない。
- binary を置いた checkout で記入後に材料レポートと test が通ることは確かめていない。
- digest に抜粋の無い 25 件のうち 23 件の赤の原因 (残る 2 件のうち 1 件は推定)、§0・§1 の全文への適合は個別に確かめていない。
- 床値 0.09691 を性能差として解釈していない。
