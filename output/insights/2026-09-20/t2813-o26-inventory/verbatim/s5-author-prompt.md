単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2813-o26-inventory

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する (射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない)。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/verbatim/s4-adjudication.md` — **親の段 4 裁定 (確定指示)。§2 が新本文の確定、§3 が変更面 v2、§4 が変異の事前登録。** 読めなければ即停止
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/verbatim/brief.md` — 段 1 brief (背景・不変条件)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2813-o26-inventory/verbatim/dw-o26-new-section.md` — **新本文の正本 (998 bytes、UTF-8、NFC)。** 見出し行 + 空行 + 本文 8 行、末尾は改行 1 つ
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2813-unit-impl/docs/dev-wave/operations.md` — 読むだけ (触らない)。HEAD `0bb4365a2` で DW-O26 節は既に新本文へ置換済み。`## DW-O26` から次の `## DW-O27` 直前までが正本 file と byte 一致することを自分で確かめる
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2813-unit-impl/tools/check_docs.py` — **編集対象** (7000 行超。全文 cat しない。`grep -n "DEV_WAVE_DW_O26_SECTION_LITERAL\|DEV_WAVE_EXACT_VISIBLE_SECTIONS\|DEV_WAVE_L2_SECTION_BYTES_MAX"` で位置を出し `sed -n` で読む。編集は `DEV_WAVE_DW_O26_SECTION_LITERAL` の本文だけ)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2813-unit-impl/orchestrator/tests/test_check_docs.py` — **編集対象** (12,800 行超。全文 cat しない。`grep -n "_SYNTHETIC_DW_O26_SECTION\|== 979\|o26_contract_weakened\|o26_heading_only\|o26_section_deleted\|静的レビューが見落とした破れを\|焦点走の consumer test 拡張\|file 集合列挙のメタテスト"` で位置を出し `sed -n` で読む)

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2813-unit-impl` とする。上記以外も repo 内を読んでよい。

## この段の仕事

`docs/dev-wave/operations.md` の DW-O26 節が新本文 (998 bytes) へ置換済みなので、その節を byte 単位で pin する exact 契約の側を追随させる (T-2292 の「契約側更新はセットで行う」)。編集するのは次の 2 file だけ:

1. `tools/check_docs.py` — `DEV_WAVE_DW_O26_SECTION_LITERAL` の本文を新本文へ置換する。literal の形 (`"""## DW-O26 — 焦点走の consumer test 拡張\n\n...最終行\n"""`) は現行と同じにし、末尾は改行 1 つで終える。`DEV_WAVE_EXACT_VISIBLE_SECTIONS` の登録や他の定数・関数は変えない。
2. `orchestrator/tests/test_check_docs.py` — (a) `_SYNTHETIC_DW_O26_SECTION` を新本文へ置換 (production literal と独立に手書きした literal であり、`check_docs` から import して代入しない)。(b) bytes assert `assert len(_SYNTHETIC_DW_O26_SECTION.encode("utf-8")) == 979` を `== 998` に更新。(c) `o26_contract_weakened` case の attack 文字列「静的レビューが見落とした破れを」は新本文にも 1 回だけ (1 行内に) 残るので不変のはずだが、`count == 1` が成り立つことを実測して確かめる。(d) 旧本文の断片 (例: 「file 集合列挙のメタテストも焦点走に含める」「この拡張を欠く」「初回実測でも」「並行投入は orphan hold で rc=16」「全走緑は file 単独緑を含意しない」) に依存する test・helper・期待メッセージが他にあれば新本文へ追随する。無ければ「無い」と報告に書く。

必ず守る点:

1. **触らない file:** `docs/**` (新本文の正本は親が commit 済み。1 byte も変えない)、`hooks/**`、`.claude/**`、`.codex/**`、`.agents/**`、他のすべての test / production file。新規 file を作らない。job dir (`/work/1/SFC/tanab/dev-wave-jobs/...`) へ書かない。
2. **絶対に `git add` / `git commit` / `git stash` / `git checkout` / `git reset` を実行しない。commit は親が行う。** 差分は working tree に残す。
3. **既存 test の期待値を変えない。** 例外は上記 2(b) の bytes assert 1 箇所と、2(d) で旧本文の断片に依存していると実測で判明した箇所だけ。既存 test の反転・緩和・skip・削除は禁止。単節予算 `DEV_WAVE_L2_SECTION_BYTES_MAX = 1_000` と `test_dev_wave_layer_budget_contract_is_literal` の `== 1_000` は不変 (新本文は 998 で予算内)。
4. **新本文は 3 箇所 (docs / production literal / 合成 fixture) で byte 一致させる。** 一致の確認は `python3 - <<EOF` の代わりに短い一時 script を repo 内 (例: `/tmp` ではなく `<repo root>/.t2813-verify.py`、終わったら削除) に書いて走らせ、`len(...encode("utf-8")) == 998` と `operations.md.count(literal) == 1` と `literal == fixture` を出力に残す。
5. **テストを甘くしない (F27):** fixture へ現行 hash を差し込まない、production literal を import して fixture に流用しない、attack 文字列を検索しやすい別語へ差し替えない。
6. **実走 (sandbox 内で走る形):** `tools/run_tests.py` と `python -m pytest` の直叩きは使わず、次を `cd <repo root>` で走らせ、**実走 nodeid・件数・結果を報告に列挙**する。
   - `PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['orchestrator/tests/test_check_docs.py','-q','-rf','-p','no:cacheprovider','-k','o26 or o18 or exact_section or normative or layer_budget or exact_visible or dw_c01 or o28 or o25']))"` (DW-O26 の pin と予算に掛かる集合。-k は実名に合わせて広げてよい)
   - 上が緑なら同 file の**全件** `pytest.main(['orchestrator/tests/test_check_docs.py','-q','-rf','-p','no:cacheprovider'])` (約 577 件、数分)。赤があれば nodeid と assertion 本文を報告し、本差分に帰属するか (旧本文断片への依存) / 環境起因 (login の /tmp、sandbox の書込不可) かを分類する。
   - `python3 tools/check_docs.py` を repo root で走らせ、rc と最終行を報告する (新本文と literal が一致すれば「違反なし」のはず。赤なら本文を直さず literal 側を見直す)。
   - 走らない (guard 拒否・環境不備) なら「実装済み・未実走」と書き、緑と書かない。子の実走は親の全走を代替しない。
7. **meta-test:** `orchestrator/tests/test_plain_runner_coverage.py` など変更 file に掛かる制約 meta-test があれば自ら洗い出して走らせる (新規 test file は作らないので新設義務は無い)。
8. **報告に所有外への波及を静的列挙:** `DEV_WAVE_DW_O26_SECTION_LITERAL` / `_SYNTHETIC_DW_O26_SECTION` の他の参照元 (`grep -rn` を `orchestrator/ tools/ hooks/ .codex/ .agents/` で)、`docs/failures.md` 等の逐語引用は歴史記録として触らないことの確認。
9. 規模の目安: check_docs.py ±8 行、test_check_docs.py ±9 行。超えるなら理由を報告に書く。
10. docs を書かない。報告は最終メッセージ本文に書く (file に書かない)。予算が尽きそうなら途中結論を出力形式どおり書いて終わる (無出力が最悪)。
11. **現行の受理・拒否挙動を scope 前に明記:** 変更前の `tools/check_docs.py` が現行 operations.md (新本文) をどう判定するか (親の実測 = 「可視 H2 節 'DW-O26 — 焦点走の consumer test 拡張' の節全体が exact 契約と不一致」1 件、rc=1) を自分でも走らせて 1 行で書く。指示外の受理集合変更をしない。

## 出力形式

- 見出しはすべて `##`。節: `## 変更の要約` (file ごと)、`## byte 一致の確認` (3 箇所の bytes・count・一致の実測)、`## 既存 test 追随の有無` (2(d) の結果)、`## 実走結果` (nodeid・件数・rc。未実走はその旨)、`## 波及` (所有外参照元)、`## 未了・懸念`、最後に `## 総括`。
