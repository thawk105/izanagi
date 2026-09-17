# [T-1912] B-4 事前登録 §7.2 / §10 の「4 者の束縛を強制しない」記述を追補で訂正した

- `authority: none`
- `default_effect: no-state-change`
- 作成: 2026-09-17 (dev-wave、branch `worktree-dev-wave-t1912-prereg-erratum`、docs のみ、codex 子 0 本)
- 起点 commit: `38353207f719acb0871cfe3d9bbe3a02490282bb` (local main = origin/main)
- 裁定: D1986 項 3 (2026-09-14、ユーザー裁定)。本 wave はその記録手番であり、新しい設計判断はない
- 一次資料 (前 wave): `output/insights/2026-09-14/t1912-pair-completeness/README.md`
- 本書は記録の凍結であり、可変状態の正本ではない (正本は worklog 末尾と現行 phase doc)

## 何を変えたか

`docs/phase3-b4-reflux-ablation-preregistration.md` の 2 箇所へ **追記 (2026-09-17、[T-1912]、D1986 項 3)** を
足した。既存の bytes は 1 行も変えていない (挿入のみ)。

1. §7.2「機械強制の現在地」の「pair の完全性と receipt shopping」項の直後。
   「同じ block・同じ precursor から来たことを強制しない」が 2026-08-29 の [T-2049] (`227ec6892`) 以降の
   実装を表さないことを書き、最終組立て (`assemble_b4_raw_analysis`) が何を束縛するか、正例・負例の
   test 名、束縛が示す範囲の限界 (転記の一貫性まで)、そして**閉じていない publication 間の選別**を書いた。
2. §10「本書が閉じないこと」の「pair の完全性と receipt shopping の遮断」項の直後。
   項目が閉じない事項のまま残る理由を publication 間の選別に限定して書いた。

D1884 / D1896 と同じ形 — 保証の文言を閉じた範囲 (1 つの publication の内側) に限定し、閉じていない経路を
1 項も削らず、機構 (gate・検査・台帳) を足さない。§5 の値セル、§5.1.1 の凍結 bytes (consumer の exact pin)、
§6 の publication root 宣言行 (issuer が「ちょうど 1 行」を検査) は不変。

## 親が現行 main で実測した事実 (追記の根拠)

- `orchestrator/campaign/p3_b4_raw_record_producer.py` の `assemble_b4_raw_analysis`:
  on / off の `identity.pair_id` 一致、`binding` 完全一致、`binding` と封印 registry・凍結 manifest から
  再導出した `expected_binding` (attempt_id / block_id / driver / registry_sha256 / manifest_sha256 /
  precursor_hash = registry の `initial_proposal_sha256` / reference_tps / reference_snapshot_hash /
  reference_receipt_hash) の exact 一致、`(campaign_id, iteration, arm)` の一意性、raw の `precursor_hash` を
  照合済み `binding` から代入 — いずれも一次資料の記述どおり現行 source に実在する。
- 同 module の非保証 (module 冒頭の列挙): 「`initial_proposal_sha256` を計算・記録する経路が repo に無いため、
  precursor と実 campaign の束縛は転記に留まる」。追記はこの限界を併記した。
- `orchestrator/tests/test_p3_b4_raw_record_producer.py` に `test_m01_assembly_rederives_precursor_from_the_sealed_registry`、
  `test_m04_final_assembly_rejects_different_on_off_pair_ids`、
  `test_m08_publication_rejects_reuse_of_campaign_iteration_arm_tuple`、
  `test_positive_201_block_certified_preserves_decimal_and_all_pair_protocol_bindings` が実在する。
- `git log -1 227ec6892` = 2026-08-29 `[T-2049] B-4 の raw 試行記録 producer と耐久書き込みを実装する`。
- B-4 issuer の固定名成果物 (`prerun-issuer-receipt.json` 等) は `output/` 配下に 0 件 (2026-09-08 の追記の事実は今も真)。

## 一次資料 (2026-09-14) 以降に変わった事実 — 追記は現行形で書いた

一次資料は「`p3_b4_prerun_issuer.py` は呼び出しごとに新しい publication root と予定 artifact path を発行する」と
書いていた。**2026-09-16 の [T-2545] (D1881、commit `7b0b43d04`) でこれは変わった。** 発行器は事前登録 §6 が
名指す 1 つの root (`output/b4-prerun-publication`) だけへ create-only で発行し、それ以外を拒否する
(`_require_preregistered_publication_root`、`_ensure_new_publication_root`)。

ただし `load_b4_prerun_publication` と `p3_b4_material_report._load_and_evaluate` は呼び手が指定した root を
そのまま 1 つだけ読む (loader は事前登録 root との一致を検査しない。§6 が同旨の非保証を明記済み)。
したがって「別の checkout から、または既存 root を退けたうえで、名指しどおりの root へ publication をもう 1 つ
発行し、結果を見てから有利な方だけを材料レポート生成へ渡す」経路は残る。最終組立ては渡されなかった
publication の存在を知らない。**D1986 項 3 の結論 (閉じない・文面へ出す) はこの新事実で変わらない。**
追記は「呼び出しごとに新しい root」ではなく、この現行形で書いた。

## 追記が扱わなかったこと

- **同じ model/prompt から来たことの強制。** 最終組立ての束縛に model/prompt は含まれない。§10 の
  `expected_claude_model_snapshot` 項 (admission record の機構は閉じたが値は未登録) の現在地に委ね、閉じたと
  書いていない。
- **publication 間の選別を閉じる機構。** 閉じるには publication をまたぐ追記専用の権威 (file-drawer 項と
  同じ機構) が要り、D1936 前文の「付随する gate・台帳・汎用化を足さない」と同項 8 の「母集合を作るための
  追加基盤は採らない」に抵触する。D1986 項 3 が閉じないと裁定済み。再開はこの 2 決定を改める新裁定を要する。

## 検査

- `python3 tools/check_docs.py`: 違反なし。
- 「B-4 prerun publication root」を含む行数: 1 (不変)。
- `git diff` の hunk は §7.2 と §10 の各項の直後の 2 つだけで、§5.1.1 (§6 見出しより前の凍結範囲) は非接触。
- 焦点走・受入全走の結果は worklog エントリに書く。
- 変異 matrix は実装面の差分ゼロで免除 (DW-S04)。

## 逐語

追記の全文は本 wave の docs commit の diff が正本である (本書へ再掲しない)。
