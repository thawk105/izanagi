# 段 1 brief — [T-1798] 床値 SWO oracle の依存 manifest を production で成立させる

## scope
production の床値経路で `sort_swo_oracle` の依存検証が PASS するようにする。**oracle 側の検証器と
pin は一切変更しない** (`sort_swo_oracle.py` の `_verify_dependency_root` /
`_parse_dependency_manifest` / `_prepare_verified_dependency` / `DEPENDENCY_MANIFEST_SHA256`)。
変えるのは「production が oracle へ渡す依存 root をどう用意するか」だけである。

## 確定済みユーザー裁定
- 引数: 「生成器を作るのか宣言側を実在へ合わせるのかを含め、oracle の受理集合を広げずに解くこと
  (絶対規律 2)」。Codex author = D95。着手直前の local main から fresh worktree。
- base main = 9463bcbc。worktree = .claude/worktrees/dev-wave-t1798-floor-oracle-manifest。

## 親が段 1 前に実測した事実 (アンカー表)
| 事実 | 実測値 | アンカー |
|---|---|---|
| oracle の依存 gate | root 再帰の全 regular file 集合 == manifest 宣言集合 (exact)、symlink/非 regular が 1 件で REJECT | `orchestrator/campaign/sort_swo_oracle.py:1796` `_verify_dependency_root` |
| manifest 本体 pin | `source.manifest_sha256 != DEPENDENCY_MANIFEST_SHA256` で hard 比較 | 同 `:1901` `_prepare_verified_dependency` |
| pin 値 | `8d0151cfaa0b86d1a2753e69f514633ec2fe6ee1077caed819fd3a426b501875` | 同 `:81` |
| production 依存 root | git top-level であること・HEAD == 共有 policy pin・`config.h` と `libkohler_masstree_json.a` の実在を要求 | `orchestrator/campaign/s8b_floor_campaign.py:2812`-`2919` |
| 実体 | `/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree`、HEAD `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38` (pin 一致) | 同上 |
| oracle へ渡す経路 | `oracle_dependency_root=_dependency.source_root` | 同 `:3946` → `s1_direct_comparison.py:685` |
| build 境界の検証 | 同じ `_verify_dependency_root` を使う | `orchestrator/campaign/buildcache.py:948` |
| fixture 宣言 | 101 path (`PIN` と `config.h` を含む、`.git` を含まない) | `orchestrator/tests/fixtures/sort_swo_masstree/SHA256SUMS` |
| production 実在 | 196 regular file、symlink 0 | 実測 |
| 差分 | fixture のみ = `PIN` 1 件。production のみ = 95 件 (`.git/` 26、`.deps/` 26、`autom4te.cache/` 7、`*.o`、`libjson.a`、`libkohler_masstree_json.a`、`configure`、`config.h.in`、`config.log`、`config.status`、`GNUmakefile`、`stamp-h`、`mtd`/`mttest`/`mtclient`/`test_atomics`) | 実測 |
| 共通 100 path の bytes | `config.h` を含め全一致 (mismatch 0 / missing 0) | 実測 |
| 生死確認 (DW-G01) | production から宣言 101 path 分だけを複製し `PIN` = HEAD、`SHA256SUMS` を `LC_ALL=C sort` + `sha256sum` 形式で生成した結果、**fixture の manifest と byte-identical、hash が pin と完全一致** | repo 外 driver `probe_canonical.sh`、job tmp |
| oracle の E2E | fixture root を dependency root にした compile+execute E2E が PASS 済み | `orchestrator/tests/test_sort_swo_oracle.py:295`, `:311` |

**帰結**: canonical root は fixture と全 101 file が bytes 一致するので、oracle から見て両者は
区別不能である。production 側で canonical root を組み立てられれば、受理集合を 1 bit も広げずに
床値経路が開く。「宣言側を実在へ合わせる」(pin を production の 196 file へ広げる) 案は、
`.git/` の可変内容を宣言に含めることになり安定しないうえ受理集合を広げるので採らない。

## 不変条件
1. `sort_swo_oracle.py` の検証器・pin・受理集合を変更しない (絶対規律 2)。
2. `orchestrator/tests/fixtures/sort_swo_masstree/` の bytes を変更しない (pin 閉包が全て不変であること)。
3. oracle が判定した材料と build・bench された材料の因果束縛 (T-1749 / D953) を切らない。
4. canonical root は production の実 source から導出し、fixture を production の材料にしない。
5. fail-closed。canonical root を作れない・pin と一致しない場合は PASS でなく停止する。

## 親の provisional 裁定 (攻撃対象)
- **(P1)** canonical root の**宣言集合は規則で導出する** — production source_root の git tracked file
  全部 + `config.h` + 生成する `PIN`。fixture の SHA256SUMS を production が読む形にはしない
  (test fixture への production 依存を作らないため)。規則が誤れば生成 manifest の hash が pin と
  一致せず fail-closed するので、pin 自体が規則の検査になる。
- **(P2)** materialize は floor campaign の依存 preflight (`s8b_floor_campaign.py` の
  `_FloorOracleDependencyBinding` を作る所) が行い、oracle へは canonical root を渡す。
  実 source_root は従来どおり build・bench に使う。
- **(P3)** build 境界 (`buildcache.py:948`) が見る root も canonical root へ揃える。
  T-1749 が揃えた「oracle と build が同じ検証器を見る」形を壊さない。
- **(P4)** canonical root は job 一意の private directory へ materialize し、複製後に実 source を
  再検証して不変を確かめる (`_prepare_verified_dependency` と同じ二重確認の思想)。

## 成果物の形
- production 側の canonical dependency root 生成器 (実装子が書く)。
- floor campaign の preflight から生成器を呼び、oracle と build 境界の両方へ canonical root を渡す配線。
- 生成器と配線のテスト。実 production root を読む real-repo テストは段 7 の記録前に親が実走する。
- worklog / decisions / failures fragment、insights。

## 成果物影響 (DW-G05)
実装しない場合、床値 arm は `sort_best` cell が build へ到達せず論文 §8 の A-4 (新しい床値 protocol に
よる実測) の計測到達セルが 0 のままで、certified 選択集合に床値 arm が 1 本も入らない。

## 分割方針
設計択一が (P1)〜(P4) の 4 点で割れうるうえ、正しさ防壁 (oracle の受理集合と因果束縛) に直接触る。
DW-C00 により軽量版にせず、段 2 plan 1 本 + 段 3 敵対 2 レンズ + 段 5 実装子 + 段 6 敵対レビュー 2 本を回す。
段 3 のレンズは (a) 因果束縛と受理集合 (規律 2/3、reward hack)、(b) fail-open 経路と恒真な保証
(F624/F625 の型 — gate はあるが成功経路が空、条件が偽になると禁止が黙って消える) に分ける。
