単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md` — 親の段 4 裁定。**変異事前登録 (M1〜M18、M7 除外) と不変 pin 表が本レビューの基準**
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/prompt-s5-unit1.md` と `prompt-s5-unit2.md` — 実装子 2 本へ渡した契約
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s5-unit1.md` と `s5-unit2.md` — 実装子の完了報告。**自己申告であり検証対象**
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s5-integrated.patch` — 統合後の実装差分の全文 (unit1 + unit2)
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s3-lens-b.md` — 段 3 レンズ B (所見 5〜9 の (d) 修正案)
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/decisions-verbatim.md` — 確定裁定の逐語 (D1522 / D1337)

**統合後のコードは `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` にある (未 commit の作業 tree)。所見はここの現物で裏を取れ。**

## 依頼

あなたはレビュー B である。**テストの実効性・変異の帰属・所有範囲・波及**を検査する。実装子の報告を信じず、現物とつき合わせろ。

## 検査の軸

1. **変異事前登録 M1〜M18 (M7 除外) の帰属。** 各変異について、(i) 置換対象が統合後のコードに一箇所で実在するか (old 逐語を示せ)、(ii) 登録された観測 node が現物に実在するか (nodeid を示せ)、
   (iii) その node が「他の gate に遮られず、対象 gate を消したときだけ赤になる」か。遮られる候補は、遮る層と再照準案を書け。**この表が本レビューの主成果物である。**
2. **負例の単一理由性。** 各負例 test の fixture が、対象 gate 以外では拒否されない形か (valid な path / shape / binding を維持しているか)。過剰決定なら名指しせよ。
   特に `test_attempt_registry_prefix_rejects_reported_head_tamper` が「改変後に N 以後まで全 hash を再計算した入力」になっているか (未再計算なら `_assert_chain` に遮られる)。
3. **正例の到達可能性と実体。** unit1 の正例が N=1 / 3 / 4 / 5 を production adapter 経由 (`_v2_registry_capability_case` / `_reserve_v2` / classify / observation-start) で組んでいるか。
   stub や手書き行で組んでいないか。valid append test が「N=3 の proof → classification 追加 → inspection 受理」の形か。
4. **read-only の検査。** tripwire test が `provision_shared_admission_root` / `_entry_paths` / `admission._locked` を実際に呼ばれたら失敗する形か (monkeypatch の対象 module 属性が実際の呼出し経路と一致するか)。
   bytes / inode 不変 test が root 配下の全 file を見ているか。
5. **unit2 の fake inspector test。** monkeypatch の対象 (`s8b_attempt_registry.inspect_attempt_registry_prefix`) が wrapper の局所 import 経路と一致し、実際に差し替わるか。
   `raising=False` で属性不在を隠していないか (統合後は実在するので `raising=True` 相当で通るべき)。fake が受け取った `expected_binding` を外部引数から独立に再導出して比較しているか。
6. **既存テストの弱体化。** 統合 patch が既存 assertion を削除・反転・緩和・skip していないか。不変 pin 表の node (`test_s8b_floor_contract.py:180`、`test_s8b_floor_stats.py:596,1321-1325`、
   `test_attempt_registry_core_s8b_profile.py:2206,2251-2294`、`test_s8b_attempt_registry.py:3000-3104`) が 1 行も変わっていないか。
7. **所有範囲と波及。** 変更 file が 8 file (production 4 / test 4) だけか。所有外 caller (`s8b_holdout_freeze.py:1429,1620`、`s8b_ratified_freeze.py:2360,3281`、`s8b_floor_campaign.py:6684`) と
   共有 fixture (`s8b_v2_freeze_fixture.py:340`、`test_s8b_ratified_verify.py:460`、`test_s8b_floor_campaign.py:6552`) が統合後も既存挙動のまま通るか静的に判定せよ。
   `test_official_perf_closure.py::test_official_perf_surface_inventory_is_exact` が `result_keys_for_mode` の signature 変更で赤にならないか。
8. **制約 meta-test。** `test_s8b_attempt_registry.py:1729-1775` (direct import 禁止)、file 列挙 meta-test、`test_check_docs` 系、`acceptance_duration_ledger.json` の file 束縛に、
   本 patch が触れるものが無いか。新規 test file を作っていないか。
9. **段 3 レンズ B の所見 5〜9 の (d) 修正案**が反映されているか、所見ごとに closed / partial / missing で判定せよ。

## 出力形式

所見ごとに `所見 N` の見出しを付け、(a) 何が問題か、(b) 現物の file:line、(c) real なら放置時に成果物の値・受理集合・参照がどう変わるか 1 行、(d) 修正案 (所有 file を明記)、を書け。
各主張に [実測] / [推測] を付けろ。**blocker / must-fix / nit** を分けろ。変異 M1〜M18 の帰属表 (ID / old 逐語の所在 file:line / 観測 nodeid / 帰属成立 or 遮る層 / 再照準) を別節に置け。

## 制約

- 読取専用である。pytest の実走は要求しない。静的検査でよい。実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、blocker / must-fix / nit の件数、帰属が成立する変異の件数、GO / NO-GO の判定を 10 行以内で書け。
