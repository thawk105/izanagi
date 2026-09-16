# 親の実測 — [T-2637] repo 外走査の収量と費用

すべて親が 2026-09-16 に測ったか、台帳の一次資料から引いた値である。
測定機は login node (Lustre: /work は /lustre/work、/home は /lustre/home)。

## 1. 抑止の実収量 — 台帳から復元した全 6 走

| 日付 | 抑止 (commit,path) 対 | 要確認 | 所要 | 備考 |
|---|---|---|---|---|
| 2026-08-09 | 2 | — | — | 導入時。条件 5 を足す前は 13 対 |
| 2026-08-25 | 7,050 | 28 | 2:16:05 | **D957 の再生成可能物除外より前** |
| 2026-08-25 (別走) | 7,051 | 28 | 56 分 | 同上 |
| 2026-08-26 | **292** | 47 | 283.27 秒 | D957 後。独立 4 走すべて同値 |
| 2026-08-26 (別走) | 記録なし | 47 | 539 秒 | 別 checkout・別混雑 |
| 2026-08-29 | 記録なし | 36 | 547.484 秒 | |
| 2026-09-15 | **0** | — | 2542.8 秒 | bytes 一致 17 file・23 対はすべて landed 参照なし |

出典: `docs/archive/worklog-phase3-0809-320-323.md` (322)、`docs/archive/worklog-phase3-0825-917-918.md`、
`docs/archive/worklog-phase3-0826-980.md` (8 行目)、`docs/archive/worklog-phase3-0826-986.md`、
`docs/archive/worklog-phase3-0829-1094-1095.md`、`docs/archive/worklog-phase3-0915-1506.md` (659 行目)。

**7,050 と 292 の差は D957 の build cache 除外である。** D957 は
`output/s8b-build-cache/` を監査対象から外し、実測で (commit,path) 対 16,395 のうち 13,488 対
(82.3%) がこの build cache だったと記録している。除外後の収量系列は **292 → (未記録) → 0**。

## 2. 探索根の規模と走査費用 (2026-09-16 実測、cold)

`/work/1/SFC/tanab/dev-wave-jobs` の全 file 列挙を C 実装の並列走査 (bfs 4.1.1 既定) で 1 回。

- 総 file **1,760,870**、file を 1 本以上持つ dir **193,880**、直下の job dir 1,188 本。
- 所要 **1583.99 秒** (user 1.57 秒 / sys 72.04 秒)。
- **CPU は wall の 4.6% しか使っていない。** 律速は Lustre の metadata 待ちである。
- 1 dir あたり 8.2 ms。
- 対照: Python 版 (`_enumerate_offrepo_candidates`) の cold 全走査は 2026-09-15 の記録で
  2429.3 秒 = 1 dir あたり 12.5 ms。**C + 並列でも 1.53 倍しか縮まない。**

この測定中、後半に `git worktree add` が 1 回走った (本 wave の作業木作成)。
順序は走査完了後なので所要には入っていない。

## 3. D985 の実測は warm だった

D985 (2026-08-26 ユーザー裁定) は「並列化は実測で否定済み (16 thread で改善 20%)」として
索引化も並列化も却下した。その根拠の測定は
`docs/archive/worklog-phase3-0826-980.md` にあり、単一 thread 157.98 秒 / 4 thread 141.83 秒 /
8 thread 132.56 秒 / 16 thread 125.80 秒 である。

同 entry は判定手順を「**warm-up 1 走を捨てた**独立 3 走の最大」と明記している (D958 が
受理条件として固定した手順)。したがって **125.80〜157.98 秒はすべて warm cache 下の値**であり、
cold の regime は当時測られていない。当時 1,299,504 inode で 157.98 秒 = 0.12 ms/file、
2026-09-15 の cold は 1.38 ms/file で、**11 倍の差は cache 状態で説明がつく**。

`/cleanup-branches` は日をまたいで散発的に走るので、実運用は cold 側である。

## 4. 候補先行方式の縮小率

抑止条件 5 (D247) は「main に land 済みの文書が、候補の絶対 path または**探索根より真に下位の
祖先 directory path** を、path 境界を満たす形で参照している」ことを要求する。
実装は `_reference_patterns()` が候補 path とその祖先 (探索根自身は除く) を pattern にしている。

したがって **抑止されうる file は、landed 参照の最小被覆部分木の中にしか存在しない。**
この集合は main だけから先に計算でき、走査前に確定する。

境界の定義 (D248) は「境界 byte を空白類・引用・括弧に限り、それ以外はすべて path を延長する」
である。よって **landed content 中で境界に挟まれた極大の非境界 byte 列**が、
そのまま「境界付き参照として成立しうる文字列の全体集合」になる。実測:

- 極大列の異なり: **7,098 件** (`git grep -h -o -P` で探索根 prefix つきのものだけ抽出)
- 最小被覆 (祖先が居れば子孫を落とす): **5,264 path**。うち 123 件は job dir を丸ごと覆う
- 被覆部分木に入る file: **278,272 (全体の 15.8%)**
- 被覆部分木に入る dir: **25,416 (全体の 13.1%)**

費用は dir 数に比例するので **7.6 倍の縮小**。cold の推定は Python 318 秒 / C 並列 208 秒。

候補集合の 68% は上位 5 dir が占める:

| file 数 | 被覆 path |
|---|---|
| 59,723 | `dev-wave-t2397-a1-attempt4` |
| 34,433 | `dev-wave-t748-pilot-path/w2-evidence/bundle` |
| 33,669 | `dev-wave-t2048-floor-budget-drift` |
| 33,602 | `dev-wave-t1434-oracle-realdata` |
| 26,807 | `dev-wave-t1431-floor-pilot-submit/mutation-source` |

被覆 path の深さ別 file 数: depth1 151,998 / depth2 88,389 / depth3 37,605 / depth4 271 / それ以深 9。

## 5. 候補先行が保つもの・縮めるもの

- **`suppressions` は厳密に不変。** 被覆部分木の外にある file は、条件 5 の pattern を
  1 つも満たせないので、現行実装でも抑止されない。
- **`unreferenced_copies` (bytes 一致だが landed 参照なしの注記) の射程は縮む。**
  2026-09-15 の 17 file・23 対はこの注記である。被覆部分木の外にある同一 bytes の控えは
  見つからなくなる。findings からは落ちないので**安全側は保たれる**が、
  D957 の「除外は沈黙させない」に従い、縮んだ射程の開示が要る。

## 6. D985 の対処は実施されていない

D985 が採った「古い wave 成果物の退避で探索根を縮める」は、後続タスク T-1810 として
持ち越されたが worklog entry 1082 (2026-08-28) を最後に台帳から消えている
(`grep -l "T-1810" docs/archive/*.md docs/worklog.md` の最大番号が 1082)。
その間に探索根は 1,299,504 inode (2026-08-26 実測) から 1,760,870 file へ増えた。
