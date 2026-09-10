# 段 6 fix 裁定 — [T-2408]

段 6 の敵対レビュー 2 本 (sol = 受理集合と fail-closed 性、luna = 実効性と波及) の所見を裁定した。
親は sol の real 1〜4、luna の real 1〜3 の中心的主張を現物で確認済みである
(`space_version` は stem しか比較していない、`_require_binary_path_policy()` は report 分岐より前、
`formal_runtime()` は report 分岐の中で呼ばれている)。

## F1 (最重、sol real 1・2・4 と luna real 1 / sol real 3 をまとめて閉じる)

**成果物影響:** 現状では、3 つの現物 lock を土台に calibration の値、`space_version` と `trial` の対、
別系列の実在 authority、未検査の `search_config` key を書き換えて再 canonical 化した lock が受理され、
report が偽の測定 identity・偽の calibration 値を発行できる。

**採る直し方 — 系列ごとに lock 全体の SHA-256 を production 側の literal として exact 比較する。**

- 新しい module literal 3 本 (系列名 → digest):
  - write-heavy: `0a32c22b8afedd6b5542d0ec1da6cba713e55d77fd83cc878d173e568ee91674`
  - balanced: `087e46dfc825b4db6b1fba585e339f989ea94b8e68c14bbb9cb7088fa7ad86b9`
  - read-heavy: `5abdfe110ac418b9d98a541ce7bfc3b4aa8975a97fbd6e82b5570f76330180b7`
  (親が現物と worktree の fixture の双方で `sha256sum` により実測した値である)
- これは D1597 が名指しした形そのものである — 「系列ごとの有限な内容 digest 集合へ exact に閉じる」。
- 検査位置は歴史 decoder を通す**前**とし、bytes を読んだ直後に照合する。不一致は `resume-binding` で拒否する。

**この裁定に伴い、新しい構造比較は足さない。** calibration の値 literal、`search_config` の 23 key exact 集合、
authority commit と系列の対応比較は、いずれも上記 digest 照合に含意されるので**追加しない**
(裁定 N1 の「恒真な述語を足さない」と同じ理由)。既に書かれている比較 (binding literal、spec digest、
workload、path、`search_tag`、`ccbench_commit`、`spec_content`) は値の取り出し口として残す。

## F2 (sol real 3 / luna real 1 の残り、上とは別に直す)

**成果物影響:** 攻撃者が与えた入力から期待値を組み立てる形が残る。

`space_version` は歴史値 `b10-backoff-shape/v2` と **exact 比較**する。stem 比較をやめる。
`expected_trial` は locked epoch からではなく、その固定値と固定 spec digest から導出する。
現行 module の `SPACE_VERSION` / `TRIAL` を期待値の源にしない (現行値は v3 であり歴史値と異なる)。
到達不能になった `separator != "/"` の枝は削除する。

## F3 (luna real 2)

**成果物影響:** 3 lock と 135 record がすべて正しくても、現在の runtime contract の `clocks_per_us` が
歴史 calibration の値から変われば report が発行できない。歴史成果物の読み取りに、現在の計測サイトの
成立と claim directory の作成可能性を要求している。

report では `formal_runtime()` を呼ばない。`resolve_campaign_output_root("official")` だけを使う。

- `pipeline._require_measurement_site` / `p2_2.resolve_site_runtime` / contract の
  `env_tag`・`attestation_mode` 検査 / `_prepare_official_output` の claim 作成は report 経路から外す。
- **代わりに、locked calibration と locked spec の整合は残す** — `calibration.env_tag == ENV_TAG`、
  `calibration.threads == spec.threads`、および locked `clocks_per_us` による
  `validate_runtime_physical_residual`。current contract とは比較しない。
- 到達 test の site / runtime stub は、この経路を通らなくなったぶんだけ減らす。

## F4 (luna real 3)

**成果物影響:** `B10_BINARY_PATH_POLICY_ENV` が設定されていないだけで、有効な歴史成果物からの report が
`binary-path-policy` で発行できない。これは formal build の前提であって report の前提ではない。

`_require_binary_path_policy()` を report の return より後 (非 report 経路の先頭) へ移す。
到達 test からその事前設定を外し、**policy 未設定でも report が通る正例**を 1 件足す。

## F5 (変異事前登録の訂正、sol の nit と実装子の自己申告を踏まえる)

段 4 の変異表を次のとおり訂正する。単独赤を厳密要件にせず「主診断 test」を明記する。

| # | 変異 | 主診断 test | 単独赤か |
|---|---|---|---|
| M1 | report 入口の歴史 decoder を通常 decoder へ戻す | 現物 fixture の系列別正例 | いいえ (統合正例も赤。主診断で数える) |
| M2 | authority の 24 blob 照合呼び出しを削除 | false-authority 負例 | はい |
| M3 | binding の module literal 比較を削除 | analysis-code drift 負例 | いいえ (系列交換負例も赤) |
| M4 | **collector の `expected_binding` callsite** で write-heavy へ balanced literal を渡す | collector 正例 | いいえ (sol の指摘どおり、系列交換負例は collector を通らない) |
| M5 | locked calibration の復元をやめ live へ戻す | orchestration 正例 | はい |
| M6 | report 分岐で `load_preregistration()` を呼び直す | orchestration 正例 | はい |
| M7 | locked spec digest の検査を削除 | locked-spec-drift 負例 | はい |
| **M8 (新規)** | **F1 の lock 全体 digest 照合を削除** | **F1 で足す偽造 lock 負例** | **はい** (他層は lock 全体の bytes を見ない) |

## F6 (収載)

fixture 3 本は untracked だった。親が `git add -N` 済みで、以後の差分と commit に含める。

## 不採用 / refuted

- sol の nit「系列間の spec / `ccbench_commit` / formula / patch 比較は実質恒真」— そのとおり。
  **削除はしない** (診断価値がある) が、**変異防壁として数えない**。
- sol の nit「campaign ID 比較は production では恒真」— 同上。受理集合は collector と record validator が固定している。
- luna の R5 に関する指摘 (到達 test が writer を stub する) — 実 writer は別 test が直接通すので独立の real とは数えない。
- luna の R6 に関する指摘 (fixture を一度 `write_text` してから decoder へ渡す) — 現物 3 本は UTF-8 で値は変わらない。nit。
- 135 record digest literal と 3 つの digest 集合比較は**両レビューとも無変更を確認**した。

## fix 子への不変条件 (段 5 の実装子契約を全文継承する)

1. **既存テストの期待値を変更しない。** 反転・緩和・skip・削除を禁じる。赤なら実装側が誤りとする。
   期待値そのものが誤りだと判断したら、実装を変えずに報告して止める。
2. 135 個の record digest literal と 3 つの digest 集合比較を 1 byte も変えない。
3. 系列別 literal の分離を保つ。
4. 通常 decoder (`campaign_lock.py`) を変更しない。
5. 凍結成果物 (現物 lock / block record / receipt) の bytes を書き換えない。
6. 並行 wave の領域 (`_verification_source_disclosure` 本体、`_collect_report_inputs` 内のその呼出しと
   戻り値の受け 2 行、test file の 2850 行以降) に触れない。
7. `_collect_report_inputs` は module 直下の FunctionDef のまま、3 validator を Name 呼び出しのまま、
   `expected_record_digests` を keyword で渡さない (AST pin)。
8. commit・branch 操作・push・docs 編集をしない。
