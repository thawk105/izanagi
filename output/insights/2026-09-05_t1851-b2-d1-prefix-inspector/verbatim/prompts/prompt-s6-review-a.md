単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s4-adjudication.md` — 親の段 4 裁定。**plan v2 節・変異事前登録・不変 pin 表が受入基準の正本**
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/prompt-s5-unit1.md` と `prompt-s5-unit2.md` — 実装子 2 本へ渡した契約 (所有 path、禁止事項、実装項目)
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s5-unit1.md` と `s5-unit2.md` — 実装子の完了報告。**自己申告であり検証対象**
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s5-integrated.patch` — 統合後の実装差分の全文 (unit1 + unit2)
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/artifacts/t1851-b2-d1/s3-lens-a.md` — 段 3 レンズ A (blocker 4 件の (d) 修正案が実装に反映されているか)
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/decisions-verbatim.md` — 確定裁定の逐語

**統合後のコードは `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` にある (未 commit の作業 tree)。所見はここの現物で裏を取れ。**

## 依頼

あなたはレビュー A である。**正しさ境界と契約遵守**を検査する。実装子の報告を信じず、現物とつき合わせろ。

## 検査の軸

1. **裁定 plan v2 節 1〜7 との逐条照合。** 特に (a) root が `shared_admission_root` だけで解決され provisioning / `_entry_paths` / `admission._locked` / fsync を呼ばないか、
   (b) 兄弟世代を列挙せず exact 2 段 path だけを読むか、(c) v2 schema guard → binding 照合 → 全行 replay → `len(rows) >= N` → `rows[N-1]` 比較の順か、`rows[-1]` を inspection に使っていないか、
   (d) proof validator が `schema` と `registry_schema` を両方 exact literal にし、bool を除く正整数、zero head 拒否を持つか、
   (e) pure verifier が v5 で `proof.freeze == artifact.freeze_sha256`、`proof.protocol == artifact.protocol_sha256` を検査し、expected と 7 field 等値を取り、v4 で expected 非 None を拒否するか、
   (f) live wrapper が外部引数だけから binding を作り、reported proof の binding を path 選択にも expected にも使わないか。
2. **受理集合の不変。** v4 artifact の受理集合が 1 bit も変わっていないか。v3 の error 文字列が保存されているか。`RESULT_SCHEMA` の値が v4 のままか。
   既存 `read_attempt_registry` / v1 reader / writer / recovery 経路 / v2 terminal の二層拒否 (S5 / S6) が無変更か。不変 pin 表の node が 1 行も変わっていないか。
3. **恒真化・fail-open の形。** 「reported が無ければ skip」「例外を握りつぶして受理」「validator を通さず値を流用」「expected を reported から作る」が 1 本でも無いか。
   例外の写し (`FloorHoldoutEvidenceError` の category / reason) が拒否を受理へ変えていないか。`_replay_current_v2_attempt_registry` の except 節の広さが、本来 `mismatch` であるべき失敗を `unverifiable` に丸めていないか (その逆も)。
4. **protocol digest の整合。** wrapper が `canonical_protocol_sha256(protocol)` で作る binding が、writer 側 (admission / registry の genesis) が書く `protocol_sha256` と同じ導出か。
   `s8b_holdout_freeze.py:1405,1678` の呼び手と、genesis の binding の出所を現物で追え。不一致なら実台帳では常に `attempt-registry-binding-mismatch` になり、fake inspector の test では見えない。
5. **schedule digest の整合。** wrapper の `sha256(canonical_json_bytes(list(schedule)))` が admission (`s8b_holdout_admission.py:5612-5617`) の `_canonical_bytes(list(state.schedule))` と同じ入力・同じ正規化か。`schedule` の要素の型 (Mapping か dataclass か) が両者で同じか。
6. **D1522。** 上流が拒否する形でも下層 (core validator、replay helper、`result_keys_for_mode` の各集合、pure verifier の等値比較) を直接名指しする test があり、差し替えが実際に呼ばれたことを assert し、正例対照を同じ test に置いているか。
7. **段 3 レンズ A の blocker 1〜3 と must-fix 5〜7 の (d) 修正案**が実装に反映されているか、所見ごとに closed / partial / missing で判定せよ。
8. **実装子の報告の自己申告**のうち、現物と食い違う点 (行数、node 数、「不変」の主張) を全件列挙せよ。

## 出力形式

所見ごとに `所見 N` の見出しを付け、(a) 何が問題か、(b) 現物の file:line、(c) real なら放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか 1 行、(d) 修正案 (所有 file を明記)、を書け。各主張に [実測] / [推測] を付けろ。**blocker / must-fix / nit** を分けろ。段 3 レンズ A の所見ごとの closed / partial / missing 表を別節に置け。

## 制約

- 読取専用である。pytest の実走は要求しない。静的検査でよい。実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 出力の最後に `## 総括` 節を置き、blocker / must-fix / nit の件数と、GO / NO-GO の判定を 10 行以内で書け。
