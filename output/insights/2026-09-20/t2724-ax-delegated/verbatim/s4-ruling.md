# 段 4 裁定 — [T-2724] A/X を AI が作る wave (2026-09-20 14:1x JST)

裁定 inbox 再走査 (14:0x): `rulings-inbox/` に 13:30 以後の新規 file なし。先行 job 9f2d502a は停止済み (13:43 idle)。

## 所見の裁定 (real / refuted / 採否 / scope)

| # | 判定 | 採否 | 内容 |
|---|---|---|---|
| A-1, A-2, A-3, A-5, A-13 | refuted | — | 判定式・受理幅・不変防壁・import 副作用・brief 前提は plan / brief のとおり |
| A-2 (補強) | 条件付き | 採用 | 正例に scope 無し / `role=manager` / `product=claude` の適合 1 行を parameterize し、受理幅を固定する |
| A-4 | 条件付き | 採用 | 複製文法の meta-test は pattern / flags / 予約語集合の exact 比較に加え、単一行の正負例集合で `tools.check_ai_provenance.validate_message` (check_cab=False、values 明示) と判定一致を検査する (test 側で import、runtime は複製) |
| A-6 | real | 採用 | 変異に approval diff / pointer diff / pointer parent 検査の削除 3 件を追加 (殺す test は既存 3 本 + 構造化 parameterize) |
| A-7 | real | 採用 | raw 件数検査削除を単独で殺す入力 = 本文と末尾に**同じ適合値**の AI-Agent 行 (raw 2 / parse 1)。helper 直接検査で topology と分離 |
| A-8 | 条件付き | 採用 | 「raw / parse ともに >= 1」の複合変異は構造化 2 行 case で殺す。片方だけの `>= 1` は他方が拒否を維持するので等価変異 = 登録しない |
| A-9 | real | 採用 | R3 test (`:2298-2325`) のコメントを「approval 経路は新 helper の raw byte 比較が拒否する」へ書き直し、`_is_none_commit` 直接 assert (raw `AI-Agent: none ` → False) を同 test に足して旧 helper の帰属を分ける |
| A-10 | 条件付き | 採用 | `*_with_ai_trailer_*` 3 本は改名せず docstring 冒頭に「歴史的 node 名。非構造化 `claude-opus` の拒否を検査」と明記 |
| A-11 | 条件付き | 採用 | 親は git add / commit の機械的代行に徹し、A/X の trailer は Codex author 1 行のみ。親が実質的判断を加える事態は起きない (record 内容は裁定と README §5 で確定済み) |
| A-12, B-4, B-12 | real | 採用 | brief P3 の v1 予測は撤回 (v1 gate-check は `driver:627` で active 解決前に戻る → 既知 4 拒否 exact と照合)。P2 は 5 関数 (`test_frozen_artifacts.py:251`)、runbook §2 P2 の「2 passed」は本 wave で「5 passed」へ docs 訂正 (Q4 = 同 wave) |
| B-1 | real | 採用 | 実 root consumer は driver 4 + `test_s8b_binding_driftguards.py:249,300` の 2 = 6 node。全 6 node は growth hold (`growth_test_holds.py:193,514,525-547`)。A/X 後に token 付き焦点走で実測し、新しい真値へ更新。manifest refusal の検出力は tmp repo 経路で維持 (plan Q3 の補完 test を driftguard 側にも 1 本) |
| B-2 | real | **scope 外 (次 wave、AI 手番)** | `_launch_validate` 段階 6 (`s8b_ratified_freeze.py:3493`) は result path の導入集合 == {G} を要求するが、result.json の導入は X1' `cc82edc8c` (実測 `git log --diff-filter=A`)、G の diff は世代文書 1 件のみ。V1a (G^ == frozen_at_head) と D2077 の順序 (result を commit → 候補 → G) の下では**構造的に満たせない**。A/X が生む差ではない。lineage 契約の変更は launch admission (W-5 の実走 admission、proof chain) の受理集合変更 = 規律 2 の射程で、ユーザーの scope 外 (W-4 / W-5)。本 wave では触れず、P3 の実測 (拒否 reason の exact) を新事実として insight・worklog に記録し、設計択一 (α: 段階 6 の導入集合を「{G} ∪ chain の祖先で cert C より後」へ改める / β: 世代導入 G を result と同 commit で作り直す = D2120 項 2 (b) の再裁定 / γ: measurement_closure と同様に floor_source を「導入 commit を課さない」側へ移す) を次 wave の brief 材料として残す。推奨は α (D2077 の一方向順序を保ち、cert C < 導入 < G の記録順を要求) — 決定は次 wave の 2 レンズ相談で行う |
| B-3 | 条件付き | 採用 | P3 (g1 path) の静的予測 = 段階 1〜5 通過なら段階 6 `binding-chain-mismatch` (cause `generation-introduction`)。予測は対照であって期待値ではない。実測 reason と優先順を記録 |
| B-5 | real | 採用 | P3 の判定規則: (i) A/X の schema / hash / topology / trailer / 新規 record の exact exemption 不備 → 本 wave で修正、(ii) 既存 G / 床値 / contract / lineage の不整合 → 次 wave (B-2)、P3 未達を明記、(iii) launch 成功後の独立 spec 承認拒否 → W-4。完了文言は「批准 (loader) 成功」と「P3 全 gate 受理」を分ける |
| B-6 | real | 採用 | launch memo は足さない。6 node は hold のまま (通常受入での実行状態は不変。通常受入の所要は未検証 — 段 6 RB-3 で訂正)。token 付き焦点走の所要を計時して記録 |
| B-7 | 条件付き | 採用 | pin 更新の授権は「A/X 導入の事前授権から必然の期待変更 (赤を見る前に対象 3 literal を固定)」+ 独立レビュー (段 6) + 変異 2 + 負例 3 (別 file 追加 / 1 byte 変更 / **A または X の欠落**) と書く。D2166 と「同一手続」とは書かない |
| B-8, B-9 | refuted | — | FROZEN_MANIFEST / clean scan / receipt prefix / hooks test / B-10 job fixture / dispatch 契約は A/X で新規赤にならない |
| B-10 | real | 採用 | A 作成直前と land 前に `git worktree list` の他 wave と関連 path の差分 (main...HEAD) を確認。main が進んでいれば固定 SHA の merge (DW-O23) で取り込み、A/X を rebase / cherry-pick / squash しない。統合後 HEAD で loader / P3 / pin を再検証 |
| B-11 | 条件付き | 採用 | 段 6 レビューで両 script の `"xb"`、A blob == hash 対象 bytes、各 commit の追加 1 件を現物確認 |
| Q1 | — | 複製 + meta-test (A-4 補強付き) | runtime に tools 依存を足さない。ImportError 経路は生じない |
| Q2 | — | 修正 | B-5 のとおり |
| Q3 | — | 補う | tmp repo の集約負例 (driver 側 1 + driftguard 側 1) |
| Q4 | — | 同 wave で docs 訂正 | runbook §2 P2 の件数 |

## plan v2 (確定)

実装順: S1 (checker + tests、unit `t2724-ax-s1`) → 親 commit (impl) → S2 (record 2 file + script 2 本、unit `t2724-ax-s2` = impl tip) → 親 commit A → 親 commit X → 焦点走 (token 付き 6 node + s8b_ratified_freeze 全走) → S3 (B-10 literal 3 + 実 root 6 node の真値 + tmp repo 補完 test 2 + memo docstring、unit `t2724-ax-s3` = X tip) → 親 commit (帰結) → 段 6 review 2 本 + fix + 変異 matrix → 検証 (loader / P1〜P4 / 全史監査) → 段 7 記録 → 受入 → land。

S1 の受理式 (署名): `_user_commit_trailer_problem(commit, root) -> Optional[str]` = raw 行 1 ∧ parse 値 1 ∧ raw 行 == `"AI-Agent: " + 値` ∧ (値 == `none` ∨ (`_PROVENANCE_AGENT_VALUE.fullmatch(値)` ∧ product ∉ `_PROVENANCE_RESERVED_PRODUCTS` ∧ model ≠ `none` ∧ reasoning ≠ `none`))。通る正例: `AI-Agent: product=codex; model=gpt-6-astra; reasoning=medium; role=author; scope=approval-record` の 1 行だけを持つ非 merge の A/X。

## 変異事前登録 (DW-M01、単一理由性は実装後に確認)

S1 (`orchestrator/campaign/s8b_ratified_freeze.py`)、KILLED 期待:
- m1 raw 件数検査を削除 → `test_user_commit_trailer_requires_one_raw_and_parsed_line` (本文 + 末尾同値 case、A-7)
- m2 parse 件数検査を削除 → 同 test (本文のみ case)
- m3 raw / parse ともに `== 1` → `>= 1` (先頭採用) → 同 test (構造化 2 行 case)
- m4 raw 完全一致を `strip()` 後比較へ → `test_structured_trailer_raw_form_is_exact` (末尾空白 case)
- m5 raw key を小文字化して比較 → 同 test (小文字 key case)
- m6 構造化文法検査を削除 → `test_user_commit_structured_value_must_conform` (`claude-opus` case)
- m7 予約語検査を削除 → 同 test (`product=none` 等)
- m8 model / reasoning の none 検査を削除 → 同 test
- m9 none + 構造化の混在を許可 → `test_trailer_both_none_and_structured_rejected`
- m10 merge 検査を削除 → `test_structured_user_merge_commit_rejected`
- m11 ancestry 検査を削除 → `test_non_ancestry_user_commit_rejected`
- m12 G の `generation-commit-none` 拒否を削除 → `test_generation_introduced_in_none_commit_rejected` (reason 変化で kill)
- m13 approval diff 検査を削除 → `test_approval_commit_with_extra_file_rejected`
- m14 pointer diff 検査を削除 → `test_pointer_commit_with_extra_file_rejected`
- m15 pointer parent 検査を削除 → `test_pointer_parent_must_be_selected_approval_commit`
- 登録しない: fullmatch → search 単独 (anchor 済みで等価)、片方だけの `>= 1` (他方が拒否)

S3 (B-10 pin)、KILLED 期待:
- p1 test literal 2 箇所だけ旧値 → `test_b10_freeze_tree_bytes_match_the_wave_local_gate` (+ `test_b10_pbs_payload_and_submit_wrapper_are_three_independent_jobs` の文字列側)
- p2 job 定数だけ旧値 → `test_b10_pbs_payload_and_submit_wrapper_are_three_independent_jobs`
- 負例 (独立コピーで digest 不一致を実測、変異 harness の外): 別 file 追加 / 既存 file 1 byte 変更 / A 欠落 / X 欠落

runner argv (S1): `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_s8b_ratified_freeze.py -q -rf`。
runner argv (S3): `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_backoff_extended_sweep.py orchestrator/tests/test_b10_backoff_grid_job.py orchestrator/tests/test_b10_backoff_grid_submit.py -q -rf`。
