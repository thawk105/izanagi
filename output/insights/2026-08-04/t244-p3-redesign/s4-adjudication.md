# 段 4 裁定 — [T-244] D121 P3 再設計 + 再実装 (2026-08-04)

## 裁定: 実装へ進む。プラン v2 + 本裁定の修正指示 Δ1〜Δ15 をプラン v3 として確定する

## 走行中に着弾した新事実 — ユーザー明示裁定 (12:44)

`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md` (12:44 着弾、
wave 開始時の inbox 実測 12:4x 以後) にユーザー発話「５件は推奨通りで」の一次控えがあり、
**[T-244] P3 の U-A〜U-G 全件が親推奨どおり採用**、帰結として「**P3 実装 wave を再起票できる**」
と明記されている (spool fragment 化は `worktree-rulings-20260804` が担う。本 wave は重複起票しない)。

- brief の provisional 裁定 P1 (「wave 起票を採用の意思表示と読む」) は**根拠ごと破棄し、
  この明示裁定へ差し替える** (brief-erratum-1.md)。レンズ A-1 / B-1 の攻撃どおり、黙示推論は
  D147 却下案 (a) と同型であり、採ってはならなかった。結論は明示裁定により同じへ着地する
- U-A〜U-G の再裁定は不要。残余は (a) `DW-G04` の扱い (下記)、(b) runtime head の commit 主体
  (Δ15 で「git commit しない」を決定として記録)、の 2 点で、いずれも本裁定内で閉じる

## `DW-G04` / 未結線 leaf (A-2, B-2, B-3) の裁定

**real (gate 文言は満たさない) だが、実装は進める。** 根拠: (165) の裁定パッケージは「未結線 leaf =
発火しない保証と同型」(B-1) と `DW-G04` 不充足 (B-2) を**ユーザーに明示提示した上で**、
U-G (leaf 単体は prototype 止まり、P3 充足は producer 結線 + P7 まで含めて数える) を推奨し、
ユーザーが 12:44 に推奨どおり採用して「実装 wave を再起票できる」と裁定した。よって
「発火 artifact を書けない条件付き機能は設計メモ止まり」という G04 の既定は、この個別案件に
ついてユーザー裁定で上書きされている。親の独断ではない。引き換えに **U-G の正直な会計を厳守する**:
成果物名は「P3 用 origin-ledger prototype (codec/FSM/registry)」まで、worklog / D fragment には
**P3 = 依然 FAIL、cap-lift 上限 1 不変**を逐語で書く (Δ14)。
B-3 の `DW-G01` (生死確認) は部分 refuted — 本件の「生死」は FSM/CAS/replay そのものであり、
codec + テストの prototype がその最安確認である。100 行 driver では対象性質を撃てない。

## 所見の裁定表

| # | 裁定 | 扱い |
|---|---|---|
| A-1 / B-1 (P1 は裁定代行) | real (攻撃時点) → 明示裁定で解消 | brief erratum。根拠差し替え |
| A-2 / B-2 (DW-G04) / B-3 (未結線) | real → ユーザー裁定が上書き | 上記節。U-G 会計を厳守 |
| A-3 (brief の anchor 過大) | **real** | brief erratum + Δ9 の名乗り (plan 異議を採用) |
| A-4 (batch 恒真化: alias/padding/架空 digest) | **real (alias/架空)** / batch 間適応は refuted (Imax で束縛される設計本体) | Δ1 salted commit-reveal + seal 時 IR 検証 |
| A-5 (tombstone 選別・早期 seal・floor 回避) | **real** | Δ2 seal の floor gate + abort-seal 分離 |
| A-6 (class 部分集合チャネル) | **real** | Δ3 exact-set 化 |
| A-7 (partial prepare が commitment 外) | **real** | Δ4 物理 tail を preimage へ |
| A-8 (op_id の committed 後一意性) | **real** | Δ5 |
| A-9 (read 線形化点) | **real** | Δ6 |
| A-10 (fixture seam / inode) | real-部分 (inode recheck は採用。Python 内 private 呼出は capability 境界にならない — D147 決定 (3) の「協調 caller」scope として正直に記録) | Δ7 |
| A-11 (cell key が同値関係でない) | real (観察) / **設計変更は不採用** — U-B の 4 組はユーザー明示裁定。過剰拒否は fail-closed 側で受容し、意味同値の再正準化は issuer の責務として記録 | Δ8 (記録のみ) |
| A-12 (anchor TOCTOU) / B-5 (GIT_* env) | **real** | Δ9 |
| A-13 / B-7 (pre-seal digest oracle) | **real** | Δ10 salted commitments |
| A-14 (kill 帰属不成立) | **real** | Δ13 matrix 是正 |
| B-4 (authority 自己申告・ccbench 二義化) | real-部分 | Δ8: `ccbench_commit_oid` (40hex 強制)。自己申告 digest は「git commit 済み authority = 人間レビュー経由」を信頼根拠として記録。issuer 束縛は scope 外 (U-G) |
| B-6 (下限式の恒真化) | **real** | Δ11 非退化制約 + formula_id |
| B-8 (authority version 遷移) | **real** | Δ12 単一版 fail-closed |
| B-9 (U-G 名乗りの機械強制なし) | real-部分 | Δ14。prose 意味の機械 gate 新設は不採用 (`DW-G03`: 独立 2 例なし、恒真 gate 化しやすい)。fragment は親所有で逐語を固定 |
| B: §14.6 受入 (brief の「login node」) | brief 側の誤り | brief erratum。受入は `tools/run_tests.py` の計算ノード dispatch (AGENTS.md の規律) |

## プラン v3 = plan-v2.md + 修正指示 Δ

- **Δ1 (A-4):** `batch-committed` の候補は salted commitment (`sha256(salt || candidate_bytes)`、
  salt は producer 保持) にする。`batch-sealed` で salt + candidate 平文 bytes を開示し、leaf は
  (i) commitment 一致、(ii) 平文の相互 distinct、(iii) `schema_ref` が既知
  (`izanagi-trigger-gate-ir/v1`) なら `reflux_ir` の decode で wire 正準性を検証する。未知
  `schema_ref` は authority admission で拒否 (fail-closed)。`reflux_ir` の import は同 package 内で許す
  (D147 却下案 (c) は qualification package の import を禁じたもの)
- **Δ2 (A-5):** `origin-sealed` を二分する。certifiable seal は全 floor 制約の
  `queries_used >= required_q` 充足が条件。満たさない終端は `aborted seal` とし、**公開 class は
  常に空** (選別チャネル遮断)。seal payload に batch 数・tombstone 数を記録する。refund 無しは不変
- **Δ3 (A-6):** certifiable seal の公開 class は「sealed rejected 結果の constraint digest の
  distinct 全集合」との**完全一致**を要求。`|set| > Kmax` なら certifiable seal は失敗 (abort-seal のみ可)
- **Δ4 (A-7):** state commitment preimage に head file の物理 tail 状態 (byte 長 + partial tail
  digest / null) を含める。partial prepare の truncate 修復は、request が観測 tail digest を明示宣言し
  実 tail と一致する場合だけ許す
- **Δ5 (A-8):** origin ごとに operation index を構築し、committed `operation_id` の再使用
  (別 payload・別 base・別 origin) を commit 後も常に拒否。V6 に負例を追加
- **Δ6 (A-9):** `read_origin()` / `read_sealed_batch()` は同じ flock を取得し、committed head index
  以下の event だけを可視化する。prepared 中の read は直前の committed snapshot を返す
- **Δ7 (A-10):** flock 取得後に `fstat(fd)` と `stat(path)` の inode 一致を再検査 (不一致は再取得)。
  in-process private 関数呼出しは capability 境界でないことを module docstring と D fragment に明記
- **Δ8 (A-11, B-4):** cell key は U-B の 4 組のまま (ユーザー裁定)。manifest の field 名は
  `ccbench_commit_oid` とし 40 lowercase hex を強制 (短縮値との二義化排除)。authority entry の
  信頼根拠 = git commit 済み + 人間レビュー、を docstring に明記
- **Δ9 (A-12, B-5):** anchor は `HEAD` を commit OID へ 1 回だけ解決し、以後 `<oid>:<path>` で
  `cat-file`。git subprocess は hardened env (GIT_DIR / GIT_WORK_TREE 等の scrub、
  `GIT_NO_REPLACE_OBJECTS` — `tools/dev_waves/git_state.py` の作法) で呼ぶ
- **Δ10 (A-13, B-7):** `batch-results-prepared` の outcome / result / constraint digest はすべて
  salted commitment で記録し、salt は seal で開示。pre-seal の snapshot / receipt / commitment から
  辞書攻撃で結果を復元できないことをテストで撃つ (32 状態全列挙で commitment が一意に定まらないこと)
- **Δ11 (B-6):** floor 制約に `formula_id` (固定文字列 `q-lower-bound/base+perRound*R+Emin/v1`) と
  非退化条件 (`queries_per_round >= 1`、`rounds >= 1`、`base_queries >= 0`、`evidence_min >= 0`、
  `required_q >= max(2, batch_cardinality_min)`) を課す。全ゼロ係数は admission で拒否。
  係数値そのものは authority 注入のまま (D147 決定 (4) のハードコード禁止と両立)
- **Δ12 (B-8):** runtime が束縛した `authority_blob_sha256` と現 HEAD anchor の blob が不一致なら
  fail-closed (`authority version mismatch`)。単一版 prototype であり supersede / migration は
  scope 外のまま
- **Δ13 (A-14):** V4 に決定論的 barrier / fault latch、V12 に production 経路 (symbolic HEAD 解決)
  を subprocess + temp repo で撃つ vector、V3 に cell key の正例 / 負例 (M-N2 kill 用)、
  M-N7 の帰属を V8 へ訂正
- **Δ14 (B-9):** 段 7 の fragment (親所有) に「P3 は依然 FAIL (prototype のみ)、cap-lift 上限 1
  不変、P3 充足は producer 結線 + P7 まで含めて数える (U-G)」を逐語で入れる
- **Δ15 (B-1 残余):** runtime head は git commit しない (mutable 側、共有 common-dir 配下)。
  これを U-E の「commit 主体・頻度」への回答として記録

## 変異事前登録 (B-057、`DW-M01`)

持ち越し 6 件 M-A1〜M-A6、新設 M-N1〜M-N12 (M-N7 の kill 帰属は V8 へ訂正)、追加:

| ID | 変異 | 殺す vector |
|---|---|---|
| M-N13 | floor 未充足でも certifiable seal を受理 | V14 追補 (Δ2) |
| M-N14 | 公開 class の部分集合を受理 (exact-set 検査除去) | V16 追補 (Δ3) |
| M-N15 | seal 時の salt / commitment 照合を除去 | V16 追補 (Δ1/Δ10) |
| M-N16 | read が committed index 超の event を可視化 | V9 追補 (Δ6) |
| M-N17 | committed op_id の別 payload 再使用を受理 | V6 追補 (Δ5) |
| M-N18 | git env hardening 除去 (GIT_DIR override を受理) | V12 追補 (Δ9) |

正例 (過剰拒否検出): (i) open → batch-committed → results-prepared → batch-sealed →
certifiable origin-sealed の全周が受理される、(ii) 4 組が異なる 2 cell は両方 admission される、
(iii) 正当な exact crash retry が受理される。
新規ファイルのため「手前に同じ入力を拒否する検査がない」「赤理由が 1 つ」のコード確認は
実装後・変異実走前 (`DW-O15` / `DW-M07`) に行い、確認不能な変異は登録から外して記録する。

## brief errata (brief-erratum-1.md として凍結)

1. P1 の根拠を「wave 起票の黙示解釈」から「rulings-inbox 2026-08-04 12:44 の明示裁定」へ差し替え
2. 「全 root 削除への committed-bytes anchor」→「committed authority anchor +
   missing-required-runtime fail-closed」(plan の異議と A-3 を採用。削除・rollback・整合再構築の
   区別は主張しない)
3. 受入環境「login node」→「login node から `tools/run_tests.py` で計算ノードへ dispatch」
