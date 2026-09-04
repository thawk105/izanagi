# 段 6 裁定 — レビュー A (実装) / B (docs・図) の所見 (2026-09-04、親 = Claude)

入力: `verbatim/s6-review-a.md` (must-fix 4、nit 1)、`verbatim/s6-review-b.md` (must-fix 2、nit 2)、親の実測 1 件。
焦点走 1 回目 (計算ノード request 977106.nqsv): 97 passed、rc=0、81 s。

## レンズ A (実装) — fix 子へ

| # | 所見 | 裁定 | DW-G05 (放置時の成果物影響) | 実装 |
|---|---|---|---|---|
| A-1 | raw `performance.build_attempt_id` と `variant` が照合されない | real / **採用** | 別 build の標本を図・provenance へ載せうる | `_validate_raw_cell` に `raw.performance.build_attempt_id == raw.build_attempt_id` を足す。負例を nested build id / variant に分ける。変異 M4b (top-level build id) / M4c (variant) / M4d (nested build id) の一置換に分割 |
| A-2 | landed closure が provenance 不在で無条件 skip | real / **採用 (部分)** | 不完全な図 bundle を見逃す | fig5 の 3 file のいずれか、または figures/README に `fig5_a2_certification_reject` の文字列が存在すれば、3 file と provenance closure を必須にする。3 file と README 言及のすべてが無いときだけ skip |
| A-3 | provenance v1 の必須 field が検査されない | real / **採用 (最小)** | proof chain の欠落を見逃す | fresh CLI 出力に対して: 必須 key の exact set、tracked 2、external 6、cells 4、artist_series 20、outputs の sha256 が実 file と一致、`measurement_conditions` に `izanagi_source_commit` と `ccbench_pin` が分離して在る。landed validator は external rows を raw-manifest の plan (path と sha256) と照合する。generator hash の現行 source 照合は fresh 生成 test に限る |
| A-4 | M11 / M12 が API 経由で実 CLI 経路でない | real / **採用** | 既定 hash 配線の破れを見逃す | whitespace 変更 copy を `subprocess` で実 script (`sys.executable tools/plotting/plot_a2_certification.py`) へ渡し、rc != 0、成果物ゼロ、stderr に `canonical SHA-256 mismatch` を確認する。durable root は `--measurement-root` に tmp の空 dir を渡し、hash gate が root より先に当たることを診断文字列で固定 |
| A-5 (nit) | M1 の kill 理由は選択件数 gate | real / **採用** | 変異台帳の説明が不正確 | `_bench_done_rows` を直接呼び、返る row が全部 `bench_done` で件数 2 であることを assert する test を足す。M1 の登録理由を「stage 述語の除去は返り値の stage 集合で検出」に訂正 |
| 親-1 | provenance `reproduction.argv` が worktree 絶対 path を含む | real / **採用** | 凍結物に wave の path が漏れ、`cwd: repository-root` と矛盾、main checkout で再現不能 | cert / manifest / out_prefix が repo 内なら repo-relative に、`--measurement-root` は絶対のまま。`_display_path` を流用 |

## レンズ B (docs・図) — 親が処理済み

| # | 所見 | 裁定 | 処理 |
|---|---|---|---|
| B-1 | README の results 系列節が「D12 の材料レポート」と書き自己矛盾 | real / 採用 | README 171 行目を「一次資料に束縛した執筆者向け統制稿。D12 の機械射影ではない」へ統一 (済) |
| B-2 | 決定 fragment に確定 D 番号 (D12 / D1013) が残る | **refuted** | `docs/spool/decisions/README.md` は「既存の D を参照するときは実番号で書く」と定める。禁じられるのは新規 D の番号と有効な `[T-数字]` の例示だけ。変更しない |
| B-3 (nit) | 「成果物自身は信頼区間を持たない」の先行詞が曖昧 | real / 採用 | 「`certification.json` 自身は」へ (済) |
| B-4 (nit) | 「新しい測定は行っていない」「1 回検算した」が執筆者の証言 | real / 採用 | 前者を「入力は既存 attempt の権威 bytes・raw manifest・WAL だけ (provenance の field)」へ、後者を作業記録への参照へ (済) |

B1〜B10 (段 3) の実装判定: closed 9、partial 1 (B8、上記 B-1 で closed へ)。表 1 の 42 数値、caption の byte 一致、provenance / certification の SHA-256 はレビュー B が独立に照合し一致。

## 変異登録の改訂 (DW-M01 / M07)

M4b を 3 件へ分割 (M4b: top-level build id 照合、M4c: variant 照合、M4d: nested `performance.build_attempt_id` 照合)。
M1 の期待理由を訂正。M11 / M12 の対 test を subprocess 経路へ。合計 KILLED 期待 14 + diagnostic 1 (M7)。
anchor は fix 後の統合 commit で再検証し、probe を全件 SURVIVED 期待で走らせて観測 node を本登録する。

## 受入 1 回目の赤 (段 6 の追記)

受入全走 1 回目 (tip A、post-claim merge 後) は `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` の 1 件だけ赤。
新 test file に自走 harness (`__main__` + `pytest.main`) が無い。本変更に帰属 (実装子の F42 洗い出しが plotting 一覧 pin の meta-test しか見ていなかった)。
fix 子 2 本目に `__main__` ブロック 4 行だけを足させた (統合 commit C `6a9c4d080`)。**変異の再走は不要**: 被変異 file は commit A と C で byte 同一、
test 関数本体も不変で、各変異の失敗 node 集合は変わらない。anchor は commit C で再検証し 16 件一意 (DW-M07)。

## fix 子の契約

段 5 実装子契約 (DW-S05-A/B/C) を全文継承。所有 path は同じ 3 本。既存テストの期待値変更・xfail・skip・削除で緑にしない。
親 docs・fig5 三成果物・凍結物に触れない。commit しない。
