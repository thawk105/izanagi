# 段 1 brief — 受入全走の高速化・効率化 (t080 fixture の成長比例費用)

## 研究前進

土台。受入全走は全 wave の land 経路であり、最遅 shard が 5 分上限 (ユーザー裁定、
`docs/decisions.md` の受入時間規律) を超えると全 wave の land が遅れる。**止めている実測:**
最遅 shard = shard-0、junit `time` 中央値 **325.5 秒** (2026-09-16 の 7 走) で上限 300 秒を
25.5 秒超過。**最小差分:** shard-0 の span を決めている t080 e2e の base 構築が git 可視
`output/` の件数に比例している構造を断つ。**完了判定:** 同一 command の A/B (受入全走の
受領証 + junit) で t080 代表 node の所要が下がり、最遅 shard の wall が下がること。

## 親が段 1 で実測した事実 (一次資料 = `/work/1/SFC/tanab/.izanagi-acceptance-shards/`)

| 事実 | 値 | 出所 |
|---|---|---|
| shard 別 junit time 中央値 | shard-0 **325.5** / shard-1 229.8 / shard-2 236.6 秒 | 直近 7 走の report.json + junit.xml |
| shard-0 の内訳 (中央値) | pre 約 65 + disp 29.6 + test span 231.0 秒 | session_timeline |
| 最長単体 node | **222.51 秒** `test_s8b_oracle_driver.py::test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]` | junit.xml |
| t080 群 | 38 node / 合計 2611.1 秒 = shard-0 の CPU の 32%、上位 10 本が 200〜222 秒 | junit.xml |
| base 構築 1 回 | 約 **144 秒** (`test_t080_shared_base_builds_real_builder_once_across_processes`) | junit.xml |
| base→テスト用 copy | 8.47 秒 (24,017 files / 661 MB) | 親 probe (login) |
| `git add -A` 24k files | 76.83 秒 | 親 probe (login) |
| 単独走でも遅い | 1 本だけを走らせても call **314.59 秒** — 222 秒は混雑でなく固有費用 | `run_tests.py` 単独走 (login) |
| **成長比例** | tracked `output/` = 1,852 件 (07-27) → 22,976 件 (09-16) の **12.4 倍**。同期間に base 構築は 15〜22 秒 (コード内 T-128 実測 comment) → 約 144 秒の **7〜9 倍** | `git ls-tree` と junit.xml |
| 日次中央値は横ばい | t080 代表 node は 09-07 223.8 → 09-16 227.8 秒 (n=103)。**9 日窓では増加を検出できていない** | junit.xml 700 走走査 |

## 変更面の実アンカー

- `orchestrator/tests/test_s8b_oracle_driver.py:827` `_copy_git_visible_output` — git 可視 output を全件複製
- 同 `:1385` `_build_t080_stub_free_e2e_repo` 内の呼び出し、`:1373` `shutil.copytree(ROOT/"orchestrator")`
- 同 `:963` `_t080_stub_free_e2e_repo` (key ごとに base 1 回、その後 `copytree(base→test)`)
- 同 `:794` `_git_visible_output_paths`、`:576` `git_visible_output_metadata_snapshot(root, ROOT)`
- 消費側: `orchestrator/campaign/t080_freeze_migration.py:37-40` は output を **4 path しか参照しない**
  (`verify_receipt` は output/ を列挙しない)

## scope

- **in:** t080 e2e の base 構築費用を下げる 1 点。件数が repo 成長に比例しない形にする。
- **out:** pre (collection 65 秒、D1728/D2046 が閉じている)、disp (prewarm barrier 29.6 秒、
  別 wave `dev-wave-t2616-prewarm-configure-node` が所有)、shard 割付の変更、受入投入頻度の制御
  (待ち行列は D662 に触れるため裁定へ返す)、テスト削除 (D747)。

## 不変条件

1. **規律 2 を緩めない。** t080 が実 production builder / verifier / gate を stub なしで通す性質、
   defect ごとの exact reason、fail-closed 分岐の検出力を落とさない。D747 (削除で速くしない)、
   D2001 (欠落検出を守る検査を毎走から外さない) を守る。
2. **受理集合を変えない。** node 集合・parametrize 数・assert を増減しない。
3. 成長保留機構 (`orchestrator/tests/growth_test_holds.py`) を迂回しない。保留の追加で閉じない
   (ユーザー裁定「保留は永遠のスルーではない」)。
4. 効果は A/B の実測でだけ主張する (ユーザー裁定 項35「次も実測で律速を選ぶ / 効果を先に測り
   未確認のまま実装しない」)。ログインノードの単独測定は外乱 28 倍を実測したので根拠にしない。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1)** base 構築 144 秒の主因は「22,976 件の物理複製 + 24k object の `git add`」であり、
  両方とも消費側が要求していない。→ 消費側が要求する集合へ限定できる。
- **(P2)** blob は実 repo に既に存在するので、`git add` の再ハッシュ・再書き込みは原理的に不要。
  既存 blob SHA を使う index 構築 (`update-index --index-info` 等) で同一 tree を作れる。
- **(P3)** 9 日窓で日次中央値が横ばいなのは、成長項が他の固定費に埋もれているためで、
  成長比例の構造自体は 07-27→09-16 の 7〜9 倍で確認できる。

## 成果物の形

コード差分 1 単位 (t080 base 構築経路)、A/B 実測 (受入受領証の shard 別 wall + junit の t080 node)、
insight (一次資料と再現手順)、worklog / decisions fragment。

## 並列分割方針

実装面は 1 単位 (`orchestrator/tests/test_s8b_oracle_driver.py` の base 構築経路) なので段 5 は
実装子 1 本。段 2 plan 1 本、段 3 は 2 レンズ (A = 検出力と受理集合の保存、B = 費用モデルと実効性)、
段 6 は敵対レビュー 2 本 + fix。
