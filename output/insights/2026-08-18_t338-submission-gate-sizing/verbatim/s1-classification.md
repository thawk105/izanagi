# 親の独立 A/B 階級分類 (段 2 子の回答を見る前に確定。2026-08-18 13:10 JST)

判定基準 = D205 の逐語「絶対規律 (規律 1〜6) と科学的妥当性 (測定・検証・台帳の正しさ) に
直接効くものだけを採り、それ以外の防御的堅牢化 (多層防御、自己防衛型の supply-chain 対策、
監査完全性の完備、プロセス規約の網羅的明文化) は既定で見送る」。
および D320 の逐語「対象外 (不変): 絶対規律 1〜3、正しさゲート (verifier / admission / 変異検査)、
測定の公正」と、見送り列挙「凍結 pin の保全、承認への署名と外部 trust root、commit への束縛、
公表台帳の原子性・予約 writer、bytes 同一性の恒久証明」。

## §6 (箇条 41 件)

| 節 | 判定 | 根拠 |
|---|---|---|
| 6.1 ID 一意・dangling 禁止・自 stage 閉包 | A | 台帳の正しさ |
| 6.1 `attempts[]` が durable intent の全 attempt を exact 被覆 / qsub 失敗 row の省略禁止 | **A** | 試行欠落の防止。D229 決定 (8) の必須 kill 1 件目と同じ攻撃面 |
| 6.1 `allocations[]` に verification ちょうど 1 件 | A | 台帳の正しさ |
| 6.2 36 run 完全双射 / 失敗は厳密 prefix / 後補い禁止 / slot ごと completed 高々 1 | A | 測定の完全性 |
| 6.3 trace-perf 分離の 3 者照合 | **A** | **絶対規律 1 そのもの** |
| 6.4 argv exact 比較 / adaptive wait 禁止 / `#FLAGS_`・ShowOptParameters の exact map | A | 測定の公正 |
| 6.5 観測窓ちょうど 36 個 / 窓長 10.000±0.100 / `cpu_busy` の raw 再計算 | A | 外乱の検知 (failures F3 の恒久対策) = 測定の公正 |
| 6.6 schedule の canonical bytes 再導出 | A | 実 TPS・乱数を入力にしない = 順序を結果で選べない |
| 6.7 脚 5 JSONL duplicate-key 拒否 + canonical bytes + 末尾 LF | A | parse の正しさ。既存 `load_json_strict` で無料 |
| 6.7 脚 6 `(family_root, ordinal)` の全履歴一意性・`k = 1`・解放/tombstone 不在 | **A** | **累積有意水準のリセット防止 = 科学的妥当性** |
| 6.7 脚 1 shallow/replace/graft 拒否 | **B** | bytes 同一性の恒久証明 |
| 6.7 脚 2 `--full-history --reverse` の全世代走査 | **B** | 同上 |
| 6.7 脚 3 導入 exact 1 回・mode 100644 | **B** | 同上 |
| 6.7 脚 4 各世代 blob の byte-prefix 性 (削除・truncate・編集・並べ替え・rename/copy 拒否) | **B** | 同上 (D320 の「bytes 同一性の恒久証明」の逐語に一致) |
| 6.7 脚 7 `reservation_commit` (初出 commit) の再導出 | **B** | commit への束縛 |
| 6.7 脚 8 3 consumer が独立に全履歴を再走 | **B** | 監査完全性の完備 (D205 の見送り列挙に逐語で一致) |
| 6.8 pilot は `[1..8]` exact / main_run は 1..13 の部分集合で `|J|` / 予備 2 本を母数に入れない | A | 母数を結果を見て選べない |
| 6.9 phase cap・直列総和・`internal_deadline_s`・monotonic 単調 | A | 測定の公正、cap 超過の検知 |
| 6.10 writer 認可 (`PreregBinding` 必須 keyword-only・別経路 writer 禁止) | **A** | **gate の目的そのもの。正しさゲート = D320 対象外** |
| 6.10 pointer 実在・size 一致・sha256 一致 | A | §6.3 脚 2 の再読が成立する前提 |
| 6.10 単一 fd / snapshot・`O_NOFOLLOW`・symlink 拒否 | A | 既存 `read_regular_file_with_identity` で無料。見送る理由がない |

## §7.1 (20 項目)

A = (1)(2)(3)(4)(5)(6)(7)(8)(9)(10)(11)(12)(13)(14)(15)(16)(18)(20) の 18 件。
(17) は §6.7 と同じ混合 (脚 6 = A、脚 1/2/3/4/7/8 = B)。
(19) `receipt_schema.sha256` が approval manifest の pin と一致 — **A へ訂正**。
D282 の既 land payload が `receipt_schema` role の sha256 を既に持っているので、
新しい pin 機構の**新設ではなく既存 pin の読取 1 行**である。D320 の見送りは「新設・維持」に
かかるので該当しない。

## §7 conformance vector の digest を approval manifest が pin する

**A へ訂正。** manifest はどのみち本 wave が発行する。vector index の sha256 を 1 field 足すのは
新設機構ではない。ただし T-139 V1 の ウ が求めた「有効な approval payload 側に三つ組を置く」
(= manifest の外に trust edge を作る) は **B** であり見送る。manifest 自身の pin で足りるとし、
その限界 (manifest と vector index を同時に差し替える攻撃は止まらない) を保証境界へ逐語で書く。

## 結論 — 見送るのは 2 つだけ

1. **§6.7 / §7.1(17) の脚 1・2・3・4・7・8** (git 全履歴の byte-prefix 証明)。
   述語 (脚 6 の全履歴一意性と `k = 1`) は (P2) の粗い機構で保存する。
2. **T-139 V1 の イ (新 exact-byte approval payload `F_r*`) と ウ (manifest 外の trust edge)。**
   イは (P3) が B1 を bytes 不変で閉じることで不要になる。

**(P1) の自己訂正:** brief は §6.10 の hardening 脚と §7.1(19) と conformance vector digest pin を
B 級として見送る案だったが、いずれも既存実装の呼び出しか既 land pin の読取であり、
**「新設」に当たらないので見送らない**。段 4 でこの訂正を採る。

**正直な帰結:** 切り直しが取り除くのは主に **V1 の D320 衝突 (= 閂)** であって、行数の大半ではない。
A 級の固定 semantic validator (§6 の 41 箇条のうち 35 箇条 + §7.1 の 18 項目) は
D205 が「採る」と定めた階級そのものであり、圧縮すると受理述語の弱化になる。
見積り production は 1,500〜3,000 行 (既存再利用で下方修正) で、なお D220 の 645〜816 行を超える。
**この事実は最終報告でユーザーへ明示する。**
