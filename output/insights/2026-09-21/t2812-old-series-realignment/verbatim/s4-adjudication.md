# 段 4 裁定 — [T-2812] 旧系列 4 本の新 pin main への整合 (実装しない。4→7→8→9)

親の裁定。plan = `codex/s2-plan.md`、相談 A (sol、正しさ境界) = `codex/s3-consult-A.md`、相談 B (luna、既裁定整合・費用) = `codex/s3-consult-B.md`。
裁定 inbox は段 4 直前に再走査した (第 28 回 = D2200、2026-09-21 09:10 land、本件に触れる項なし)。local main は wave 開始後 11 commit 前進したが production (orchestrator / tools) の差分は 0。

## 1. 所見の裁定

| # | 出所 | 判定 | 採否 |
|---|---|---|---|
| A-1 | 「段階 4 を塞ぐのは policy だけ」が広すぎる。段階 4 の残部 (journal・共有台帳・result・床値選択) と `s8b_ratified_freeze.py:3167–3176` の**現行 contract 要求**が漏れている | real | **採用**。成果物の文面を「観測した最初の拒否は manifest 内 binary の policy 不一致。個別 12 receipt の歴史検証は成功。段階 4 の残部と段階 5 以降は未観測」に固定し、brief の N3 も「現行に縛られるのは expected_policy と contract_sha256」に訂正する |
| A-2 | READONLY の射程を誇張 (bytes 不変ではない) | real | **採用**。「3 木の porcelain 出力・submodule HEAD・観測対象 store の存在判定が前後一致」に限定して書く |
| A-3 | S' の失効保証は policy に符号化された値 (schema・pin・authority 文字列・generator / review の名前集合) に限る。実装の意味・closure・entrypoint は元から範囲外 | real | **採用**。「現行 registry を維持」を「現行の正しさ保証を全面維持」に広げない。既存保証の限界として明記 |
| A-4 | 「S' は別 pin・別 contract・失効 registry の artifact を通す」 | **refuted** | 攻撃 6 種の拒否根拠 (file:line) をパッケージに証拠として載せる。ただし「全攻撃の不存在」を主張しない |
| A-should | 保つ / 失う性質の表、規律 7 を比較の一律禁止に広げない、H の provenance は「記録される。ただし親 HEAD の通常 checkout では再現できない」 | real | **採用** (表をそのまま載せる。plan §K2 の「epoch 間の数値差を証拠にしない」は今回の pair 不成立・条件差に限定する) |
| B-1 | B-4 f1 の O 継続を不要な裁定へ返している | real | **採用**。f1 の w2 / finalize は依頼と D2184 の既定どおり submit-tree で継続する**親の確定事項**とし、裁定項から外す。新 pin の新 campaign は排他ではないので、必要が生じた時点の条件だけを返す |
| B-2 | S' の申し送りに**旧 binary の配置経路**が欠けている (`store_binaries:5825` は現行 policy を要求、W-5 は `s8b_oracle_driver.py:1043` で実体を必須にする) | real | **採用**。S' の射程を「2 入口 + 批准系列の記録済み binary を消費 checkout へ配置する経路」に広げて裁定項に書く。新しい配置機構を作れとは書かない |
| B-3 | B-4 本走は D2194 項 3 (carrier 実装・定義発効・caller 修復) に依存する | real | **採用**。依存として明記し、本 wave でも本パッケージでも重複実装しない |
| B-4 (refuted 項) | S' は D2184 の却下 4 種と同じ | **refuted** (ただし `repo_stock_pin` 依存の切離しという効果では D2184 が別裁定へ返した択と実質同じ) | **採用**: パッケージに「D2184 の却下 4 種とは違う理由」と「別裁定が要る理由」を並記する |
| B-should | 費用表 (node-hour)、scope 拡張の禁止、A-1 の N は D2096 項 5 の改訂が要る、並走 wave 後に変わる事実の区別、D2196 決定 4 の `_ACTIVATED_G1_REFUSALS` 追随 | real | **採用** (費用は B の node-hour 換算を採る) |
| A/B の nit | `s8b_floor_campaign.py:983`、`s8b_holdout_freeze` の一般化、`READMIT-STOCK` の名前が実処理より強い、択の定義を表の前に置く | real | **採用** (成果物の文面で直す) |

## 2. 系列ごとの確定 (プラン v2)

- **K2:** pin の整合は追加不要。新 main からの次巡は D1777 の手順 (gitlink 不変・submodule だけ `p3_s4_loop.PIN`) で走る。③ PIN は `511c9538…` 据え置き、② は現行 policy の新 campaign ID・新 lock (旧 lock を張り替えない)、⑤ 不要。**ただし pair の成立は claim の修復 (D2187) 待ちで、stock arm の admission は未到達・未観測。** 旧 lock は pin と別の epoch (T-2344 の closure 63 → 85) で現行 codec に拒否される。
- **A-1 sized v3:** 経路 H で境界・source は通る (実測)。**attempt-0003 は現行コードで未認可** (`paper_story_a1_paired.py:228` の認可列挙は 0002 のみ、解除できる prior は 1 件だけ)。再走の要否・prior 解除集合・予算はユーザー裁定。③ canonical は据え置き、⑤ 不要。
- **g1:** 段階 4 の観測された拒否は policy epoch。**S'** (live の期待 policy を「批准 protocol の pin + 現行 registry」で組み直す。射程 = `s8b_ratified_freeze.py:3394` / `s8b_oracle_driver.py:1003` / 記録済み binary の配置経路) を推奨候補とし、**O'** (`fec4a8187` + T-2810 の 3 commit + 候補削除 + 現行相当を主張するなら `cfab7a2f2` / `65e94a3a7` の移植) と **N** (新 pin の新世代。`s8b_ratified_freeze.py:3273` が generation 1 以外を拒否するので g2 の契約設計が別途要る) を並べる。S' の要求値は到達可能 (実測)。
- **B-4 床値:** f1 の w2 (2026-09-29T00:00Z 以降、`now + 24h ≤ 10-07T00:00Z`) と finalize は t2288 submit-tree のまま継続 = **親の確定事項、裁定不要**。新 pin の床値系列が要るときだけ ⑤ reseal (commit 後に resolver が拾う) + 再 build + 新 record + A-5 再凍結 + submitter の sha 束縛 + B-10 grid の `EXPECTED_FREEZE_TREES_SHA256` 更新を一括で裁定する。B-4 本走は D2194 項 3 の着地に依存。

## 3. 本 wave で実装しないこと (明示)

S' / O' / N のいずれの実装も、候補 file の削除も、reseal の実行も、A-1 の認可改訂も、pair の再投入も本 wave では行わない (依頼の指定)。gate・台帳・一般化の新設もしない。成果物は insight (設計 + 実測) と裁定パッケージだけ。

## 4. 変異 matrix

実装面 (D95 決定 2) の差分が 0 の wave なので **変異 matrix は免除** (DW-S04)。受入全走は免除しない。probe は repo 外 (job dir) に置き、逐語は insight に `.md` で残す。

## 5. 段 6 レビュー

docs-only だが一次資料から事実を再抽出するので、独立 read-only レビュー 1 本を残す (DW-C00)。対象 = insight 本文と実測値の照合 (probe-2.json / evidence の値、file:line、既裁定の引用、観測が支えない主張の有無)。
