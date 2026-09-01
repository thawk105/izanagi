# 段 4 裁定 — [T-2049 続] B-4 材料レポート生成器と正規コマンド

親裁定。base commit `24014bdb2` (段 4 直前に main を再確認、乖離 0 commit、新しい裁定の着地なし)。
入力は段 2 プラン `s2-plan.md`、段 3 `s3-consult-a-sol.md` / `s3-consult-b-luna.md`、
および親自身の実測。

## 0. 結論

**実装する。** 新規 2 file (`orchestrator/campaign/p3_b4_material_report.py` と
`orchestrator/tests/test_p3_b4_material_report.py`) に閉じ、既存 file は 1 byte も変更しない。
段 2 プランを土台にし、下記 R1〜R9 を反映した plan v2 で実装する。

## 1. 親の provisional 裁定の撤回

**(P2) を撤回する。** CLI 必須 `--floor` 引数は**採らない。**

- `docs/phase3-b4-reflux-ablation-preregistration.md:382-384` は
  「`floor` — §5 の凍結 artifact から読んだ値。関数の引数として渡す。関数内で導出しない。」と定める。
- §5 は D1060 により 1 欄も埋まっていない。したがって CLI 引数は caller の自己申告を
  凍結値の位置へ入れることになる。
- 親 brief 自身が「判断値を caller から受け取らない」と書いており、(P2) はそれと自己矛盾していた。
  段 3 の 2 レーンが独立にこれを指摘した。**親はこの指摘を受け入れる。**

正規コマンドは `floor=None` を既存評価器へ渡し、`floor_domain_error` を伴う
`protocol_violation` をそのまま材料化する。独自の「判定不能」への読み替えもしない。

**(P1)(P3)(P4) は維持する。** ただし (P1) は R4、(P4) は R5 と R9 で条件を足す。

## 2. 親自身の実測値の一般化を狭める

段 1 の「46 passed / 28.44s = producer から分析判定までの経路は現行 main で生きている」は
広すぎた。段 3 の 2 レーンが独立に指摘したとおり、次に狭める。

- fixture は 1 block の real seed と 200 block の複製である
  (`test_p3_b4_raw_record_producer.py:881-917`)。
- evaluator には test caller が `floor=0` を注入している (同 :1576-1583)。
  正規コマンドの `floor=None` 経路とは別物である。
- したがって 46 passed が支持するのは「**fixture 上で producer→assembler→evaluator の
  API 合成が現行 main で動く**」までであり、正式 publication、planned artifact 欠落、
  producer rejection、report generator、4 分類の到達性は支持しない。

## 3. 所見の real / refuted と採否

### R1 [Critical、real、採用] planned artifact 欠落 / producer rejection で report が丸ごと消える

- 出所: sol #1。
- 根拠: `p3_b4_raw_record_producer.py:1908-1917` は planned leaf が 1 件欠けただけで
  assembly 全体を拒否する。プランはそれを `B4MaterialReportError` にして report を作らない。
- **成果物影響 (DW-G05):** 走らせた 200 block と欠落した 1 block の**双方が報告から消える。**
  事前登録 §7.1 が名指しで禁じる file-drawer そのものであり、本 wave の成果物の中心契約を破る。
- **裁定:** assembly 成功を report 作成の前提にしない。
  `publication.manifest.rows` と `planned_result_artifacts` から先に 201 block / 402 arm の
  枠を作り、各行に artifact の在否を載せる。assembly が拒否された場合も report を出し、
  拒否理由と、その時点で観測できた在否を載せる。分析結果は「assembly 拒否のため未評価」と
  明示し、raw 値を推測で埋めない。
- **非保証として明記させる:** 元の `B4RawRecordRejection` の全値は永続化されないため、
  publication root だけを入力とする consumer は、過去の rejection を完全には復元できない。
  レポートが報告できるのは**レポート生成時点で観測した在否と拒否理由**までである。
  producer を変えて rejection を耐久化する案は本 wave の scope 外 (§5 へ回す)。

### R2 [High、real、採用] 完全射影検査が表示値の改変を検出しない

- 出所: sol #2。
- 根拠: プランの検査対象は source UTF-8 の SHA-256 multiset・件数・順序だけ
  (`s2-plan.md:77-83`)。行と Markdown の派生 field は照合されない。
- **成果物影響:** `terminal_reason` を行と Markdown で null に変えても全検査が通る。
  読み手が実際に見る表が誤りのまま「完全射影検査済み」と称する。D829 に正面から反する。
- **裁定:** producer の source object を**無加工の構造化値**として JSON に置く。
  行の派生 field ごとに、その source / manifest / registry 上の出所と値を照合する。
  負例は public document builder の経路を通し、一値 mutation が拒否されることを示す。
- **scope 判定:** これは成果物自身の中心契約 (完全射影) の正例・負例であり、
  仮想リスク向けの gate 追加ではない。scope 内。

### R3 [High、real、採用 (主張の限定として)] 正規経路から 4 分類のうち 3 分類が到達不能

- 出所: sol #3 と luna #1 が**独立に一致**。
- 根拠: `p3_b4_analysis_path.py:349-352` → `p3_b4_analysis_contract.py:778-789`。
  `floor=None` は必ず `FLOOR_DOMAIN_ERROR` → `verdict=PROTOCOL_VIOLATION` になる。
- **裁定:** 機構は変えない (`--floor` も既定値も足さない)。**主張のほうを狭める。**
  - レポートは自分が「事前登録 §5 未発効の状態で作られた evidence-only 材料レポートであり、
    分析 verdict は floor 不在に起因する `protocol_violation` である」ことを
    機械可読に宣言する。
  - **本 wave は「§7.1 の 4 分類を実効化した」と主張しない。** 実効化されるのは 1 分類である。
  - 4 verdict の renderer テストは残すが、**renderer 限定の将来互換試験**と明記し、
    「正規経路が 4 分類を生成できる証拠」として数えない。
- **ユーザーへ返す事項 (§5):** 4 分類を実効化するには権威ある floor artifact が要る。
  これは別 task である。

### R4 [High、real、採用] output-root guard が path alias と祖先方向を閉じていない

- 出所: sol #4 と luna #5 が**独立に一致**。
- 根拠: `autonomous_trial_completeness.py:3317-3336` が campaign root を `rglob("*")` で
  全列挙し、同 :3379-3385 で `artifact_refs` との厳密一致を要求する (親が独立に確認済み)。
  campaign 配下へ 2 file を書くと、この検査が実際に赤になる。
  字面比較だけでは symlink 親経由と祖先方向を閉じられない。
- **裁定:** 書込みに使うものと**同じ resolved path** で比較し、
  (a) output root == campaign root、(b) output root が campaign 配下、
  (c) campaign が output root 配下、の三方向をすべて拒否する。
  symlink component を拒否する。一般化した official-root admission は足さない。

### R5 [High、real、採用] `anomaly_class` に precursor の red class を代入していた

- 出所: luna #2。親の独立調査とも一致する。
- 根拠: `p3_b4_analysis_ledgers.py:90-97` の `B4DigestRedClass` は
  「B-4 treatment assignment 前に記録された red class」であり、arm 実行時の anomaly class ではない。
  producer の source object に `anomaly_class` は無い (:1354-1434 を親が全走査)。
- **裁定:** §7.1 の必須項目 `anomaly_class` は `availability: "absent"` とする。
  `precursor_digest_red_classes` を**補助 field** として全要素を順序どおり載せ、
  `evidence_issues` も別名のまま完全射影する。**同名識別子を二義化しない** (DW-O13)。

### R6 [中、real、採用] 例外境界が未設計

- 出所: luna #3。
- **裁定:** `_load_and_evaluate()` で既知の issuer / ledger 例外だけを理由を保存して
  `B4MaterialReportError` へ変換する。assembly rejection と evaluator の invalid result は
  別経路のまま保つ。各分岐について「出力を 1 file も書かない」テストを 1 本ずつ置く。

### R7 [中、real、採用] clean subprocess の条件が不足

- 出所: luna #4。
- **裁定:** `orchestrator/tests/test_layer3_report.py:2523-2533` と同じ環境
  (`PYTHONPATH` 除去、`PYTHONNOUSERSITE=1`、repo 外の `cwd`) をそのまま採る。
  加えて `tools/check_subprocess_bytecode_guard.py:315-335` に従い
  `-B` または `PYTHONDONTWRITEBYTECODE` を付ける (sol #5 の指摘)。
  subprocess 起動は上書き拒否を含め 2 回である。

### R8 [中、real、採用] fixture scope と invoke 回数の見積り根拠が不足

- 出所: luna #6。
- **裁定:** `tmp_path_factory` を使う **module-scope の immutable publication fixture** を
  明記する。実 `invoke()` は on/off 各 1 回の計 2 回に固定する。
  CLI の 2 回目は**入力を再評価する前に**既存 2 file の存在で拒否する。
  焦点走と受入全走の exact argv を plan v2 に書く。
  pytest node 内から別 suite を起動する構成を禁止する。

### R9 [中、real、採用] `initial_proposal_sha256` は registry に実在する

- 出所: 親の独立調査。段 2 プランは「初期 snapshot hash は取れない」としていた。
- 根拠: `p3_b4_analysis_ledgers.py:137` の `B4ScheduledAttemptInput` は
  `initial_proposal_sha256` を field として持つ。同 :138-140 に
  `reference_snapshot_hash` / `reference_receipt_hash` もある。registry はレポートが読む入力である。
- **裁定:** 一律 `absent` にしない。registry の `initial_proposal_sha256` を
  **値として載せ**、`binding: "transcribed"` の限定と producer の非保証
  (「`initial_proposal_sha256` を計算・記録する経路が repo に無いため、precursor と実 campaign の
  束縛は転記に留まる」) を同じ行から辿れるようにする。
  検証済みの初期 snapshot hash と**等値に扱わない。**
  D829 (producer が出した値を view 側で消さない) に従う。

## 4. refuted / 不採用

- **(P2) の CLI `--floor`** — refuted。§1 のとおり。
- **昇格 validator / AST 由来の宣言検査の新設 (D787 の向き)** — 不採用。
  D787 は別装置 (`tools/codex_reasoning_ab.py`) に対する裁定であり、
  本 wave への新設はユーザー裁定により scope 外。機械可読な `certification_scope` の
  **宣言だけ**を置き、`certified` という名前も昇格 validator も作らない。
  段 3 の 2 レーンとも新設を求めていない。
- **一般化した official-root admission** — 不採用。R4 の限定修正に留める。
- **certified-selection connection** — scope 外 (ユーザー確定裁定)。
- **producer を変えて rejection を耐久化する** — real だが scope 外。§5 へ。

## 5. ユーザーへ返す事項 (本 wave では実装しない)

1. **権威ある floor artifact が無い限り、B-4 の材料レポートは `protocol_violation` しか出せない。**
   §7.1 の 4 分類を実効化するには、事前登録 §5 の floor 欄を発効させる別 task が要る (D1060)。
2. **producer の rejection が永続化されていない。** publication root だけを入力とする consumer は
   過去の rejection を完全には復元できない。file-drawer を機械的に閉じきるには
   producer 側の durable rejection ledger が要る。
3. **certified-selection connection** は 5 語のうち最後の 1 語として残る。

## 6. 変更面と規模の上限

- 新規 `orchestrator/campaign/p3_b4_material_report.py` (1 file)
- 新規 `orchestrator/tests/test_p3_b4_material_report.py` (1 file)
- **既存 file の変更は 0 file。** 下記は 1 byte も変更しない。
  `p3_b4_analysis_contract.py` / `p3_b4_analysis_adapter.py` / `p3_b4_analysis_ledgers.py` /
  `p3_b4_analysis_path.py` / `p3_b4_analysis_prereg_consumer.py` /
  `p3_b4_prerun_issuer.py` / `p3_b4_raw_record_producer.py` / `layer3_report.py` /
  `docs/phase3-b4-reflux-ablation-preregistration.md` / hooks / schema / `flaky_test_holds.py` /
  `tools/codex_reasoning_ab.py`

## 7. 変異事前登録 (DW-M01)

実装前に、下記の機構を単一理由で pin する変異を登録する。anchor 逐語は実装後に
`DW-M07` に従って最終 commit で確定し、probe → 本登録 → 再走の順で回す。
各変異は「同じ入力を拒否する層が前後に無く、無効化時の赤理由が一つに絞れる」ことを
投入前にコードで確認する。確認できなければ登録せず実効 gate へ再照準する。

| ID | 対象機構 | 変異の向き | 期待 |
|---|---|---|---|
| M01 | 完全射影の枠づくり (R1) | assembly 拒否時に report を作らず例外にする | KILLED |
| M02 | 完全射影の枠づくり (R1) | 欠落 leaf の行を枠から落とす | KILLED |
| M03 | 行 field の出所照合 (R2) | `terminal_reason` を行だけ null にする | KILLED |
| M04 | 行 field の出所照合 (R2) | `campaign_id` を行だけ別値にする | KILLED |
| M05 | 完全射影の件数 (R2) | 402 行のうち 1 行を落とす | KILLED |
| M06 | 完全射影の一意性 (R2) | 1 行を複製する | KILLED |
| M07 | source bytes の round-trip (R2) | 埋込み source UTF-8 を 1 byte 変える | KILLED |
| M08 | floor 不在の正直さ (R3) | `floor=None` を既定値へ差し替える | KILLED |
| M09 | verdict の言い換え禁止 (R3) | `indeterminate` を否定的結論へ言い換える | KILLED |
| M10 | output guard 一致方向 (R4) | output root == campaign root の拒否を外す | KILLED |
| M11 | output guard 配下方向 (R4) | output root が campaign 配下の拒否を外す | KILLED |
| M12 | output guard 祖先方向 (R4) | campaign が output root 配下の拒否を外す | KILLED |
| M13 | output guard の実体 path (R4) | resolved path 比較を字面比較へ戻す | KILLED |
| M14 | anomaly_class の非二義化 (R5) | `precursor_digest_red_classes` を `anomaly_class` として出す | KILLED |
| M15 | 例外境界 (R6) | loader 例外を素通しさせる | KILLED |
| M16 | 上書き禁止 (R7/R8) | 既存出力の上書き拒否を外す | KILLED |
| M17 | 不在と 0 の区別 (P4) | `availability:absent` を値 0 / 空文字へ変える | KILLED |
| M18 | 転記の限定 (R9) | `initial_proposal_sha256` の `binding:"transcribed"` 限定を外す | KILLED |

## 8. 段 5 の分割

実装面は 1 単位 (新規 module + 新規テストは密結合) に閉じるため、Codex `role=author` は 1 本。
親は実装面を直接編集しない。
