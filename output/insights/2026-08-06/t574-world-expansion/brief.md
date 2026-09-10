# 段 1 brief — [T-574] 残余 (production consumer への world 拡大分)

branch `worktree-dev-wave-t574-world`。前 wave は (262) / `output/insights/2026-08-06_t574-historical-resolver/`。

## scope

依頼は「read-only 再検証への配線は済み、残る production consumer への拡大分」。
親が実測した結果、**残る「配線」は 0 件で、残余は裁定済み 3 項の消化と閉包の明示**である (下記 P1)。

- **A [T-588]**: `s8b_oracle_report._receipt_expectations` が、`run_contract` を Mapping として
  宣言しているのに `env_tag` / `contract_sha256` が欠落・空・非文字列のとき `None` を返し
  receipt 検査を課さない fail-open を、manifest-global error へ変える (受理集合の縮小は裁定済み)。
  真の legacy (`run_contract` field 自体が無い) は従来どおり受理する。
- **B [T-587]**: 契約世代を跨いだ campaign resume を失うことを**正式仕様**とし、回帰試験で固定する。
- **C [T-586]**: silo `verify-result` の binding 層を **current 互換検査**と明示し、
  「全 certified 成果物を再検証可能」という主張範囲から除外する (資料側のみ)。
- **D [T-574 閉包]**: 記録 `contract_sha256` を current registry と比較する全 site を列挙し、
  each を「配線済み」「live admission (D202 により current 据置)」「裁定により据置 (T-586/T-587)」
  へ分類して、D196 (3) の前提が満たされたことを明示する。→ [T-529] の blocker を外す。

**scope 外**: R1 (記録 hash を世代選択の権威にしてよいか) は [T-529] 本体の前提であり本 wave では触らない。
R4 / R5 / R6 は起票されていない (前 wave 裁定)。silo `verify-result` の赤自体の修理も対象外。

## 確定済みユーザー裁定

- D205 (プロトタイプ基準): 防御的堅牢化は既定で見送り、研究前進に直接効くものだけ採る。規律 1〜6 は不変。
- [T-588] (a) 受理集合の縮小を承認、専用 wave は立てず同面 wave へ同梱。
- [T-587] (a) current-only resume を正式仕様とし availability loss を受容、回帰試験で固定。
- [T-586] (b) current 互換検査と明示、resolver 配線はしない。
- D202 / D203: live admission は current 束縛のまま。`versioned predicate dispatch` の語を使わない。

## 親が実測した事実 (資料の引き写しではない)

1. `_receipt_expectations` (`s8b_oracle_report.py:1197-1224`) は `run_contract` が Mapping でも
   `env_tag` / `contract_sha256` が空・欠落・非文字列なら `return None` する。呼び出し側
   (同 1626-1634) は `receipt_expectations_error` を別変数で受ける構造を既に持つ。
2. 既存テストで `run_contract` 系を壊すものは `reps` 破損 (`test_run_contract_reps_declaration_is_fail_closed`)
   と `run_contract` 非 object のみ。`env_tag` を空・削除して legacy 受理を pin するテストは 0 件
   (`pop("run_contract")` = 真の legacy を pin するものだけが 4 件)。よって A は**純増検出力**であり、
   既存の受理正例と衝突しない見込み。
3. resume 経路 (`s8b_floor_campaign._load_resume_manifest` 以下) は contract を一切束縛せず、
   resume は `_run_campaign_core` の `validate_protocol(protocol)` (同 2750) と
   `_env_contract.lookup(protocol["env_tag"])` (同 2755) を通る。どちらも **current** registry。
4. `env_contract.GENERATIONS` は `MappingProxyType` で封じられ、注入経路は構造的に塞がれている
   (同 343-348)。よって B の回帰試験は registry への 2 世代目注入を使えない。
5. 記録 hash を current と比較する production site は、grep 全走 (`env_contract.lookup(` /
   `contract_sha256_lookup`) で `s8b_floor_campaign` (311/412/1874/2755)、`s8b_oracle_driver:770`、
   `silo_ladder_rung1` (1936/3534/3752/4433)、`t126_driver` (496/868)、`pipeline:535` に限られる。
   resolver 経由は `s8b_ratified_freeze._validate_published_protocol` と
   `s8b_oracle_report._receipt_expectations` の 2 箇所のみ。
6. **`run_contract` を宣言した publish 済み artifact は現時点で 0 件**である
   (`grep -rl run_contract output --include=*.json` が insights 以外で hit なし)。field は v2 manifest の
   schema にあり、live driver (`s8b_oracle_driver.py:762-786`) が実走時に `env_tag` /
   `contract_sha256` の非空一致を既に要求する。したがって A は**既存 artifact の受理を 1 件も変えず**、
   将来の v2 manifest に対してのみ発火する検証側の締め (DW-O13 / DW-G04 の入力実在はこの形で満たす)。

## 攻撃対象の provisional 裁定

- **(P1)** 「read-only 再検証で resolver を配線すべき production consumer は**残っていない**」。
  根拠は実測 5 の列挙と、各 site の分類 — `s8b_floor_campaign` は live campaign runner (D202)、
  `s8b_oracle_driver:770` は実走 admission、`silo_ladder_rung1:3534` は T-586 で据置裁定、
  `t126_driver` は資格判定で別面 (T-541)、`pipeline:535` は合成 pipeline。
  **この分類が誤りなら wave の骨格が変わる。** 前 wave では親の同種分類が段 3 で覆っている (F142)。
- **(P2)** A の fail-closed 化は `run_contract` が Mapping の枝だけに入れる。非 Mapping は既存の
  manifest issue が拾うため二重にしない。
- **(P3)** B の回帰試験は、registry 注入ではなく「current registry に存在しない `contract_sha256` を
  記録した protocol での resume が fail-closed する」形で世代跨ぎを模す。
  **模擬と実の差**: 真の 2 世代目 (registry に旧世代が残る) ではなく未登録 hash を使うため、
  「旧世代が登録されたまま current でなくなった」状態は模していない。この差を試験の docstring に書く。
- **(P4)** C の行き先は decisions への新 D + 本 wave insights。過去 wave の insights と D196 本文は書き換えない。

## 不変条件

- live 実走 admission の受理集合を 1 bit も変えない (D202)。
- `versioned predicate dispatch` の語を成果物で使わない (D203)。
- 真の legacy manifest (`run_contract` field 不在) の受理を変えない。
- 凍結成果物の bytes を変えない。`output/s8b-freeze/` は触らない。
- 検証を弱める方向の変更を入れない (規律 2)。

## 成果物影響 (DW-G05)

- A: 未実装なら、contract / calibration / execution receipt の束縛なしに row が `completed` へ
  到達しうる manifest が oracle report で受理され続け、certified 選択結果の proof chain に穴が残る。
- B: 値は変わらない。未実装なら「世代跨ぎ resume 不可」が仕様か欠陥か不明のまま残り、較正再取得時に
  resume 失敗を bug と誤診して admission を緩める改修を招く。
- C: 成果物の値は不変。未実装なら台帳に「全 certified 成果物を再検証可能」の過大主張が残る。
- D: 未実装なら [T-529] が「前提が済んだか不明」のまま止まる。

## 成果物の形

- コード: `orchestrator/campaign/s8b_oracle_report.py` (A)。
- テスト: `orchestrator/tests/test_s8b_oracle_report.py` (A)、`orchestrator/tests/test_s8b_floor_campaign.py` (B)。
- docs: decisions fragment (C・D)、worklog fragment、本 insights ディレクトリ。
- 受入: repo root で `python3 tools/run_tests.py` 全走。性能計測は無し。環境は login node。

## 分割方針

実装面は Codex `role=author` 1 本 (A + B は同一 face だが別 file 所有: A=oracle_report + その test、
B=floor_campaign の test のみ)。docs (C・D) は親が書く。
受理集合が変わるため軽量版にせず、段 2 プラン起草・段 3 敵対 2 レンズ・段 6 敵対レビュー 2 本を置く。
