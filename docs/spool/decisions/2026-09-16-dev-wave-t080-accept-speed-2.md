---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t080-accept-speed
seq: 2
---

## {{D:t080-fixture-session-proto}}. t080 e2e fixture の session 1 回 proto 化は実装・検証済みだが、受入 wall の中央値 −5.7% では採用せず branch に保存する

**決定:** `orchestrator/tests/test_s8b_oracle_driver.py` の t080 stub-free e2e fixture を次の形へ変える実装 (commit `bdfa49950`、
branch `impl-dev-wave-t080-accept-speed`) は、bytes 同一・変異 9/9 KILLED・レビュー must-fix 0・受入緑まで済んだが、
**同時刻ペア 3 組の最遅 shard wall が −10.7% / −1.9% / −5.7% (中央値 −5.7%) で D357 (差 10% 未満は変化なし) と D1260
(paired K=3 中央値 10% 未満なら採用しない) の基準の内側であるため、main へは取り込まない。** 実装は branch に保存し、
採用 (D1260 とは別の明示裁定「共有資源削減を別目的として採用」または「10% 基準の緩和」) はユーザー裁定に委ねる。

実装の形: key 非依存の準備
(git init / `orchestrator/` と git 可視 `output/` の複製 / basis file / submodule add・pin checkout) を xdist session parent に
1 回だけ組む proto とし、4 要素 key ごとの base は proto の `.git` 込み `copytree(symlinks=True)` から
現行の key 側処理 (distinct の descriptor 変更 → `git add -A` → basis commit → 発行) で派生させる。
descriptor 変更を submodule add の後へ移す順序交換は最終 `add -A` の前で tree を変えない。
proto は exclusive lock (build 中のみ) + 完成 marker (pending→rename) で管理し、marker 不在は残骸削除して再構築、
marker 有りの JSON 破損・root 欠損は例外伝播 (黙って再構築しない)。lock 順序は key → proto。
単独走 (process memo 経路)・runtime source の key ごと複製・production scan は変えない。

**bytes 同一 (I1) の定義:** 同一の source snapshot・key・Git 設定・commit metadata の下で、working tree の
path/種類/bytes/mode/link target、basis tree OID、basis commit OID、receipt raw/document、発行後 HEAD tree OID が一致する。
除外は index stat・reflog・`.git` 内部 timestamp・活性化 commit OID。実 corpus の probe (旧 module を base commit から exec し、
両経路の commit metadata を固定) で default / distinct の両 key について全項目一致を実測した。

**session snapshot:** proto は xdist session (= 1 shard の pytest run) の最初の要求時点の実 repo を写し、以後の key は
その snapshot を使う。現行の「key ごとに実 repo を読み直す」性質は捨てる。session 中に実 repo の可視集合が変わっても
後発 key には反映されないが、fixture の検出責任は「構築時点の可視集合」であり、session 中の実 repo 変化の検出は
実 repo を直接 scan する検査の責務である。

**理由:**
- 計算ノード実測 (直列 1 process) で base 構築 118.2 秒の内訳は、実 repo (lustre) → node の `output/` 複製 52.9 秒 (45%)、
  発行 subprocess 53.3 秒 (45%)、git 操作 11 回 9.5 秒 (8%)。複製は 5 key 分で延べ 190 秒 (5 走平均 38 秒) かかり、
  温 cache でも同じ桁だった。session 1 回化は実 repo からの全件取得 4 回を省く。
- 発行 subprocess は key 依存 (13 scan) で不変。非競合の critical path は縮まらない (同一 node の xdist `-n 12` 焦点走で
  旧 136.7 / 136.3 秒・新 133.3 / 133.1 / 150.2 秒)。受入の同時刻ペアでは、通常負荷で最遅 shard 332.0 → 296.5 秒 (−10.7%、
  e2e 10 node は各 −36 秒)、lustre 飽和下 (両側に F945 型赤) では 474.4 → 465.5 秒 (差なし)。一次資料は
  `output/insights/2026-09-16/accept-speed-t080-session-copy/README.md` §5。
- 変異 matrix は負例 9 件すべて KILLED (期待 node 完全一致)、等価変異 1 件 SURVIVED。実 corpus の probe で bytes 同一を実測。
- 実装面は test file のみ、受理集合は「構築期間を通じて同一 source である場合」に不変で、production builder / verifier /
  gate は stub しない。
- 同時刻ペア 4 組目は 326.7 → 308.1 秒 (−5.7%)。3 ペアとも同方向で退行は無いが、D357 は node 秒を wall の代理としない。
  基準は wave 開始時 (段 4 裁定 §6) に凍結しており、結果を見てから動かさない。

**却下した選択肢:**
- 中央値 −5.7% のまま land する — 凍結した採否基準 (D1260 の 10%) を結果を見てから緩めることになる。
- 実装を捨てる — 検証済みの成果物であり、branch と一次資料を保存して裁定に委ねる。
- process 内 proto memo (単独走にも proto を入れる) — 受入の critical path に無関係で、memo・失敗回復・cleanup が増える。
- copy 中の shared lock — 完成 proto は不変で削除主体が無く、不要な状態遷移を増やす。
- runtime source の session 1 回化 — 数 file の複製で性能上の根拠が無く、「どの世代の実装か」を変えうる。
- 複製自体の高速化 (`is_file()` 検査の削除・copytree の並列化) — 前者は index と実体の不一致検査で削れず、
  後者は lustre 律速なら悪化しうる。上限 28 秒級のモデルであり別件とする。
- 第 2 proto (発行済み・未活性化を 3 key で共有) — 「production 発行を key ごとに走らせる」性質を変えるので裁定候補に留める。

## {{D:d2068-erratum-index-fast-path-no-effect}}. D2068 の訂正 — 案 C (index 化) の効果は「効かない」で確定し、git 操作は build の 8% に過ぎない

**決定:** D2068 の「(C) は効果の符号が未確認である」を次のとおり訂正する。
案 C (既存 blob OID の `update-index --index-info` による index 化) は 2026-09-16 のユーザーの対比較 (温 cache、同一 tree 内で
方式を交互に測り、現行 `git add -A` 9.66 秒に対し 9.55 秒) で**効かない**と確定した。同日の計算ノード実測でも
git 操作 11 回 (init / config / submodule add / checkout / add -A / commit) の合計は base 構築 118.2 秒の 8% (9.5 秒) で、
index 化は支配項に当たらない。D2068 の案 A / B の不採用理由と「圧縮設定は時間効果が確認できない」は変えない。

**理由:**
- D2068 が根拠にした login node の `git add -A` 79〜191 秒は冷 cache・外乱下の値で、温 cache では 10 秒弱である。
  index 化の下限 0.6 秒との差は build 全体の 8% を超えない。
- 支配項は実 repo からの `output/` 複製 (45%) と発行 subprocess (45%) であり、前者は {{D:t080-fixture-session-proto}} で扱う。

**却下した選択肢:**
- D2068 を丸ごと差し替える — A / B の不採用理由と圧縮設定の観測は本日の実測と矛盾しない。訂正は C の符号だけに限る。
