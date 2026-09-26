# 段 6 裁定 (1 巡目) — レビュー A / B の所見

入力: codex/s6-review-a-out.md (NO-GO: 計測系列)、codex/s6-review-b-out.md (修正後 GO)。統合 commit `eb65d322f`。
焦点走 1 (tip `eb65d322f`、request 21116.nqsv、Elapse 303 秒): 変更 test file 全体 + inventory 4 群 = 716 passed / 9 skipped、赤 0。

| 所見 | 内容 | 裁定 | 扱い |
|---|---|---|---|
| A1 / B1 | B は新規 test node 1 件を持つので、probe の「A/B collection 完全一致」で全対が無効になる | real, must-fix | 計測の事前登録を訂正 (下の erratum E1)、probe を Codex fix |
| A2 | M5 の kill 理由が複数 (ignored と receipt が同時に混ざる) | 一部 real | 現物では M5 (実関数を呼ばず全件 copytree) の最初の赤は `visible_copy.call_count == 1` (0 回) で、理由は 1 つ。事前登録の「ignored file が集合に入る」という kill 理由の書き方が誤り → erratum E2 で訂正。test は変えない |
| A3 | 共通 node の shard 配置差が性能差に混ざりうる | real | erratum E1 に配置照合を入れる。配置は collection と台帳から決定的に決まるので、系列投入前に login で A/B の割付を計算して照合する |
| B2 | probe に未使用の残骸 (`Decimal`、`ESTIMATE_NOTE`、`all_rows`) | real (nit 相当) | probe fix で同時に削除 |
| B3 | 新規 test の direct との mtime 照合は重複 | refuted (残す) | direct との照合は「写し経由の mtime が現行の直接複製と同じ」という受理集合不変の証拠そのもの。M4 の kill だけの assert ではない |

実装 (test file) への fix は無し。fix 単位は probe だけ (repo に land しない)。

## 事前登録の訂正 (erratum、系列投入前・結果を見る前に固定、2026-09-23)

- **E1 (計測の事前登録 §3 の「両 tree の collection 一致」を置き換える):** 各走で login collection と 3 shard の選択を記録し、A 走どうし・B 走どうしは完全一致を要求する。A と B の間は、nodeid の多重集合差が「A にだけある = 空」かつ「B にだけある = `orchestrator/tests/test_s8b_oracle_driver.py::test_t080_shared_base_visible_output_uses_one_snapshot` の 1 件ちょうど」であることを要求する。共通 node の shard 割付は A と B で完全一致を要求する (新規 1 件がどの shard に入るかは記録するだけ)。これを満たさない走は無効 (実装由来として系列を止め、親が裁定する)。
- **E1 の前提確認:** 系列投入前に、A・B 両 tree の login collection と `tools/acceptance_shards.py` の割付を計算し、E1 を満たすことを確かめる。満たさなければ系列を投入せず、段 4 へ戻して計測形を再裁定する。
- **E2 (変異 M5 の kill 理由):** 「新規 test で ignored file が集合に入る」を「新規 test で実関数 `_copy_git_visible_output` の呼出し回数が 0 (== 1 の assert が最初に落ちる)」へ訂正する。kill node は同じ。

## E1 前提確認の結果 (完了 2026-09-23 21:02:44 JST = `alloc-precheck/rc.txt` の mtime、系列投入前)

A = `620a6bb13` (t2273lc-base-a)、B = `5c51e958e` (wave 木) で `IZANAGI_ACCEPTANCE_SHARD_PLUGIN_V1` を与えた login collect-only を 3 shard ずつ実行 (`alloc-precheck.sh`、出力 `alloc-precheck/`)。
shard-0: A 4,325 / B 4,326 件、A のみ 0、B のみ = `test_t080_shared_base_visible_output_uses_one_snapshot` の 1 件。shard-1 (10,247) と shard-2 (13,162) は A/B 完全一致。
→ E1 を満たす。B 側の rc=16 は同じ session root へ A が先に report を書いていたための create-only 衝突 (collection 完了後の後始末) で、選択の出力には影響しない。

## 焦点再レビュー 1 (codex/s6-focus-1-out.md): 修正後 GO

A1 / A3 / B1 / B2 closed、A2 は E2 で訂正、B3 は裁定どおり不変。新規所見「投入前の割付照合は親が確認」は上の前提確認で充足。
