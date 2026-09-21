---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: worktree-t2812-old-series-realignment
seq: 1
title: [T-2812] 新 pin main から旧系列 4 本を再開・再投入するための整合を系列ごとに実測して分けた — 塞がっているのは g1 の live launch だけで、K2 と A-1 は D1777 の手順で通り、B-4 床値 f1 は submit-tree 継続、g1 は S' / O' / N の裁定パッケージにした (insight + 裁定パッケージ、実装 0 行、branch worktree-t2812-old-series-realignment)
---

## 本文

- 依頼 (逐語は insight `verbatim/origin.md`) は「設計と login の read-only 実測が本体、実装は裁定後の別 wave、gate・台帳・一般化の追加は scope 外、旧系列は固定 checkout から走るを変えない」。9 段のうち実装段を持たず 4→7→8→9 で処理した。一次資料は `output/insights/2026-09-21/t2812-old-series-realignment/README.md`、設計判断は {{D:old-series-realignment-measured}}。専用 handoff は repo 外 job dir、wave artifact dir は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2812-old-series-realignment/`。
- **read-only probe は Codex author + fix1 が書き、親が login pegasus02 で 2 回実走した** (job dir 配置、逐語は insight `verbatim/probe-script.md`)。probe は production の読取り検査関数だけを呼び、書込み経路 (reseal / store / place / produce / submit / claim) を 1 つも呼んでいない。前後で 3 木の porcelain 出力・submodule HEAD・観測対象 store の存在判定が一致した (bytes 全体の不変は主張しない)。
- **4 系列の現状の拒否 (新 main 5efd69367、gitlink = submodule = e9e477ca):** K2 と A-1 sized v3 は pin 照合・CCBench 境界・source 契約で拒否されるが、D1777 の手順 (gitlink を変えず submodule だけ系列の PIN へ checkout) では通る。g1 は段階 4 の binary admission policy 不一致で 12 cell とも拒否 (記録値の policy で照合すると 12/12 通る)。B-4 床値は floor protocol が一意に解決できず (候補 2・head exact 0)、旧 binary の配置は現行 policy 不一致で拒否 (書込み 0)。
- **S' (live の期待 policy を「批准 protocol の pin + 現行 registry」で組み直す) の要求値は到達可能。** 現行 preimage の stock pin だけを系列 pin に差し替え production の正規化で sha を取ると、g1 の 12 receipt・B-4 の portable record・A-1 の campaign identity preimage のいずれとも一致した。対照 (現行 pin) は現行 policy sha になる。
- **新事実 (pin 以外の epoch):** K2 pair の campaign.lock は現行 codec が decode を拒否し (enforcement source closure の 63 → 85 前進)、歴史 codec でだけ読める。旧 campaign の live な再開は pin 以外の理由でも塞がる。
- **AI reseal の帰結:** successor protocol は `output/s8b-freeze/floor-protocols/` に 1 file 増え、B-10 grid 投入 script が pin する凍結木 sha を変える。commit 前は resolver が拾わない。新しい床値系列を始めるときに一括で扱う。
- 段 2 plan (codex read-only) は親 brief を 7 点訂正し、段 3 の敵対相談 2 本 (正しさ境界 / 既裁定整合・費用) が real の must-fix を 6 件出した (段階 4 の範囲を広げすぎ、READONLY の射程、S' の失効保証の限界、B-4 を不要に裁定へ返している、S' の binary 配置経路の欠落、B-4 本走の別 wave 依存)。すべて採用して成果物に反映した。S' が別 pin・別 contract・失効 registry の artifact を通すという攻撃は refuted で、拒否根拠を insight に残した。
- 独立 read-only レビュー 1 本 (docs-only で一次資料から事実を再抽出するため DW-C00 で必須) を insight 本文に対して回した。
- **言わないこと:** launch は成功していない。S' は未実装で、適用後に段階 4 の残部や段階 5 以降で別の拒否が出ないことは観測していない。候補文書の削除・W-4 の spec 承認・held checks・W-5 の予算はいずれも別に残る。記録済みの判定・測定・凍結 bytes は 1 つも変えていない。
- 工数: codex 子 6 本 (probe author 1・probe fix 1・plan 1・相談 2・独立レビュー 1)、親の login 実走 5 回 (既存 CLI 3 + probe 2)、計算ノード job 0。実装面の差分が 0 なので変異 matrix は免除 (DW-S04)、受入全走は実施。

## 次の一手差分

### 更新

- [T-2812] **P2・ユーザー裁定待ち**: 新 pin main からの旧系列の再開・再投入について、(1) 凍結 v2 g1 の live launch を S' (期待 policy を批准 protocol の pin + 現行 registry で組み直す。射程 = launch 段階 4 / W-5 の store 消費 / 記録済み binary の配置経路) / O' (pin 前進直前 main + launch validator 修正の移植) / N (新 pin の新世代。世代契約の設計が別途要る) のどれで解くか、(2) K2 の次巡を D1777 手順の新 campaign で走らせる可否と pair 1 job + 4 巡目 1 job の予算、(3) A-1 sized v3 の 3 本目を走らせるか (走らせるなら認可列挙の追加と解除する prior 集合)、(4) N を選ぶ場合の追加契約と費用を裁定する。材料は `output/insights/2026-09-21/t2812-old-series-realignment/README.md` §5。B-4 床値 f1 の submit-tree 継続は裁定に返さない親の確定事項。
  base: 2a62f2e7f286a4d1c0aa146f9b96b45f14daa5b273cef3c89dc57cdc0da3b1e3
