単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s4-adjudication.md` — 親の段 4 裁定。**4 節 (plan v2 — C1a) と変異事前登録 M1〜M12 が受入基準の正本**。3 節の契約 v2 は次 wave の対象で、本 wave で実装されていないのが正しい
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/prompt-s5-launcher.md` — 実装子へ渡した契約 (所有 path、禁止事項、実装項目)
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s5-launcher.md` — 実装子の完了報告。**自己申告であり検証対象**
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s5-launcher.patch` — 実装差分の全文
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/artifacts/t1851-unit-c/s3-lens-a.md` と `s3-lens-b.md` — 段 3 の所見。裁定で「採用 (C1a)」とされた A2 / B2 (authority)、A9 (skip 分岐)、B4 (v2 早期 gate)、B9 (fake の契約) の (d) が反映されているか
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/refs/decisions-verbatim.md` — 確定裁定の逐語 (特に D1113 / D1522)

**統合後のコードは `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` にある (未 commit の作業 tree)。所見はここの現物で裏を取れ。**

## 依頼

あなたはレビュー A である。**正しさ境界と契約遵守**を検査する。実装子の報告を信じず、現物とつき合わせろ。

## 検査の軸

1. **裁定 4 節 1〜8 との逐条照合。** (a) 副作用前の検査が genesis / reserve / subprocess のどれよりも前に走るか (例外経路も含む)、(b) v2 早期 gate が `profile.schema is S8B_V2_SCHEMA_PROFILE` または marker 非 None で副作用ゼロのまま拒否するか、v1 + None の正例が通るか、(c) 分類 authority が launcher 定数から導出され public API に caller 経路が残っていないか (`_launch_floor_attempt_for_test` の注入は許可)、(d) 流れが `reserve → probe_before → (skip | sink → capture → probe_after) → classify → open → snapshot → build → seal → observe → terminal` か、post-probe が capture 例外時も走るか、(e) `_pre_observation_failure_reason` の precedence (competing → launch → None) と `probe_before.competing` の扱い、(f) `_external_evidence_sha256` の payload が両 probe と capture failure を含み schema が v2 か、(g) `_post_probe` の exact 4 key、(h) `OpenedFloorAttempt` の field 集合と frozen、`open_error` / `post_probe` の残骸が無いか。
2. **受理集合。** 変わってよいのは裁定「受理・拒否の現状と変わる点」だけ。`_CERTIFIED_MEASUREMENT_KEYWORDS` 不変、caller の `rep_observations` 拒否が残る、`_owned_post_probe` の argv / timeout / 関数名不変 (spawn-site pin `test_ccbench_spawn_sites.py:212`)、`FloorPostProbeCapability` の封印検査不変、adapter / core / profile 無変更 (所有外 0 byte)。
3. **恒真化・fail-open の形。** 「例外を握りつぶして observed へ」「protocol digest 検査を skip できる引数」「mode を検査しない経路」「sink snapshot を open 前に取る」「marker を検査せず渡す」が 1 本でも無いか。`_contains_callable` が protocol / receipt / marker に掛かっているか。
4. **D1113。** `expected_use_perf` が receipt からだけ導出され capture kwargs `use_perf` と等値要求されるか。`reps` が protocol からだけ来るか。分類 authority の id / policy digest が caller から来ないか。
5. **D1522。** 上流が拒否する形でも下層の実体 (`_checked_reservation_policy` 等の副作用前検査、`_post_probe`、`_pre_observation_failure_reason`、`_external_evidence_sha256`) を直接呼ぶ test があり、正例対照が同じ test にあるか。
6. **変異 M1〜M12 の観測 node。** 裁定表の node 名が実在し、各 node が「他の入力は valid で対象 gate だけを踏む」形か。冗長 gate に遮られる node を列挙せよ。
7. **段 3 の採用所見 (A2 / B2、A9、B4、B9) の closed / partial / missing 表。**
8. **実装子の報告の自己申告**のうち、現物と食い違う点 (行数、node 数、「不変」の主張、実走の有無) を全件列挙せよ。

## 出力形式

所見ごとに `所見 N` の見出しを付け、(a) 何が問題か、(b) 現物の file:line、(c) real なら放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか 1 行、(d) 修正案 (所有 file を明記)、を書け。各主張に [実測] / [推測] を付けろ。**blocker / must-fix / nit** を分けろ。

## 制約

- 読取専用である。pytest の実走は要求しない。静的検査でよい。実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、blocker / must-fix / nit の件数と、GO / NO-GO の判定を 10 行以内で書け。
