# 段 1 brief — [T-499] 凍結・承認手番 (A)(B)

## scope

第 5 束で AI へ委任された 2 手番の**実施可否を実測で確定し、実施するか裁定へ返すかを決める**。
(C) は worklog 486 で解消済み。

## 確定済みユーザー裁定 (逐語で確認済み)

- 第 5 束 (authority: user、2026-08-12): 「T-499 の凍結・承認手番 (oracle 仕様の承認 SHA 記入・
  freeze v2 pointer 設置) は AI へ委任。実施は仕分けの『使う機構』確定後、freeze v2 側は
  D328 (凍結検証保留) との整合を先に確認。」
- [T-803] (2026-08-11、(a)): pinned literal を恒久形として承認。**承認者 = ユーザー、
  記入時点 = 将来の実凍結手番**。未承認のあいだ機構全体が fail-closed で止まる性質は維持。
- D328 (2026-08-12、第 4 束): 実装↔測定の同一性検証を保留。解除は**ユーザーの明示命令のみ**。

## brief 前の前提実測 (`DW-S01` の「人間手番待ちを git と成果物で照合」)

手番リストは (A) を「未承認のあいだ機構全体が fail-closed で止まっており、これを解除する」と
書くが、実測は「**承認対象の bytes がまだ生成されていない**」であり、前提が異なる。

| # | 主張 | 実測 |
|---|---|---|
| A-1 | canonical path に candidate spec がある | `output/s8b-oracle-spec/` **不在**、candidates dir も不在 |
| A-2 | spec を作る経路がある | production **ゼロ**。書き手は `orchestrator/tests/s8b_oracle_spec_fixture.py` のみ |
| A-3 | 設置すれば緑になる | tracked test `test_s8b_oracle_manifest_contract.py::test_schema_v1_has_no_durable_manifest_candidate_or_reviewed_spec` が同 dir のファイル数ゼロを要求 → **設置は即赤** |
| B-1 | approval/pointer だけ置ける | 世代 record `holdout_freeze.v2.g<N>.json` **不在**。`s8b_ratified_freeze.py` の `pointer-generation` 検査が世代実在を必須にする |
| B-2 | AI が commit してよい | `s8b_ratified_freeze.py:526-534` `_is_human_commit` が逐語 `AI-Agent: none` ちょうど 1 本を byte 単位で要求 (C1-6) |
| B-3 | D328 と両立する | (B) は `reverify_published_freeze` の production 到達性を作る。保留 check_id 21 件は `s8b-holdout.*` / `s8b-oracle.known-axes-*` を含む |

## 不変条件 (攻撃されても曲げない)

- 規律 2: 正しさゲートを緩める方向の変異を採用しない。**承認機構を通すために検査を外す・
  期待値を変える・fail-closed を fail-open にするのは全面禁止**。
- 承認の意味論: 「human-reviewed spec」の bytes を AI が創作して AI が承認すれば、
  review の実体が消える。委任は「レビュー済みのものへ hash を書く手」の委任であって、
  「レビュー対象を創作してよい」ではない。
- D328 の解除条件は「ユーザーの明示命令のみ」。第 5 束の委任は D328 の解除を含まない
  (逐語は「整合を先に確認」であり、解除の命令ではない)。
- 凍結 bytes は書き換えない。

## 親の provisional 裁定 (攻撃対象)

- **(P1) (A) は実施せず裁定へ返す。** 根拠 = A-1〜A-3 + spec 内容が 8b 本走の事前登録
  (未確定の研究上の設計) であること。`DW-G04`「発火条件を満たす既存 artifact path を
  書けなければ設計メモに留める」に該当。
- **(P2) (B) は実施せず裁定へ返す。** 根拠 = B-1 (構造的に不能) が単独で決定的。
  B-2 (provenance の構造的衝突)、B-3 (D328 射程) が独立に補強する。
- **(P3) 本 wave の成果物は docs のみ**とし、実装面 diff をゼロにする。
  → Codex author (D95) は不要、変異 matrix も不要。
- **(P4) 手番リスト自身の誤りを正す。** 「fail-closed で止まっている、解除せよ」ではなく
  「承認対象が未生成、生成側タスクの完了が先」と記録し、**いつ実行可能になるかの発火条件**を
  機械可読な形で残す。

## 成果物の形

- worklog fragment 1 本 (事実 + (P1)〜(P4))、裁定パッケージ 1 本 (repo 外 inbox にも控え)。
- decisions fragment は**書かない** (新しい設計判断ではなく、既裁定の前提が未成立という事実報告)。
  ただし段 4 で「発火条件の明文化は D 相当」と判定したら追加する。

## `DW-G05` 成果物影響

- (P1)(P2) を採らず誤って承認した場合: certified 選択の proof chain が「人間がレビューした spec」
  という主張を持ちながら実体は AI 創作 bytes になり、**承認 record の意味が虚偽になる**。
  受理集合は緩む方向へ変わる。
- (P1)(P2) を採った場合の放置リスク: fail-closed 機構は止まったままだが、**そもそも通す対象が
  無い**ため成果物の値・受理集合は変わらない。止まっていること自体が正しい状態である。

## 分割方針

段 2 = 実施可能性の道筋を codex に起草させ、私の「不在」主張へ反証の機会を与える。
段 3 = 敵対 2 本 (レンズ A = 見落とした生成経路・実施経路の探索、レンズ B = 承認の意味論と
D328 射程の攻撃)。段 4 で再裁定。実装しないと確定したら `4→7→8→9`。

## 環境

docs-only 想定のため計測なし。受入要否は段 7 で `docs/` 限定を `git diff --name-only` で
判定し、証拠を worklog へ 1 行残す (memory `record-acceptance-exemption-evidence`)。
