# 親の実測 その 2 — 今日の 1 走と、収量 0 の構造的な原因

`parent-measurements.md` の続き。2026-09-16 に親が測った。

## 7. 2026-09-16 の監査 1 走 (warm)

`python3 tools/audit_dangling_commits.py --offrepo-root /work/1/SFC/tanab/dev-wave-jobs`
を main checkout で 1 走。rc=1、全体 478.123 秒、maxrss 453,988 KB。
**直前に別の全走査を通したので cache は warm である。** 走行中に本 wave の
`git worktree add` が 1 回重なった。

段別所要 (tool 自身の進捗行):

| 段 | 秒 | 内訳 |
|---|---|---|
| root 検証 | 0.015 | requested=1 accepted=1 |
| fsck | 11.453 | 到達不能 commit 1,168 本 |
| bulk log | 4.526 | changed_pairs=2,349 |
| main・tip tree | 3.013 | tips=52、finding_commits=30、finding_pairs=53 |
| blob metadata | 0.329 | candidates=53 |
| **repo 外走査の列挙** | **455.376** | **全体の 95.2%**、candidate_oids=18 |
| 候補比較 | 0.779 | matched_keys=23、external_files=17、external_matches=23 |
| landed 参照 | 2.627 | **matches=0**、patterns=25、grep_batches=1、bytes_read=50,083,944 |
| 抑止集約 | 0.000 | **suppressions=0**、findings=30 |

- **抑止 0 対。** 2026-09-15 に続き 2 走連続で 0。
- bytes 一致は 17 file・23 対で、2026-09-15 の「17 file・23 対」と件数が一致する。
- 再生成可能物として除外 0 対 (現在の到達不能集合に build cache は 1 件も無い)。
- 要確認 30 commit / 53 (commit, path) 対。
- 走査は tool 自身の計数で **238,107 dir / 1,760,870 file** を見ている
  (親の独立走査は「file を 1 本以上持つ dir」を 193,880 と数えた。差は空 dir)。

warm 455.4 秒 対 cold 2429.3 秒 = **5.3 倍**。C + 並列の 1.53 倍より cache 状態の方が効く。

## 8. 収量 0 の構造的な原因

bytes 一致した 17 file は**すべて変異 harness の出力**である
(`mutation-spec*.json` / `mutation-ledger*.json` / `mutation-out*.json`、および `s6/analyze.py` 1 件)。
所在は 7 つの job dir に分かれる。

**7 dir はすべて landed 文書から参照されている** (`git grep -l` で 1〜4 file ずつ hit する)。
それでも条件 5 が発火しないのは、**参照の書かれ方**による。

- D248 は「境界とみなす byte を空白類・引用・括弧に限り、**それ以外のすべての byte は path を
  延長するものとして扱う**」と定める。`/` は境界ではない。
- landed 文書は job dir を、ほぼ必ず**より長い path の接頭辞として**書く
  (`.../dev-wave-t1086-report-receipt/brief.md`、`.../receipt.json` など)。
  このとき祖先 dir の直後の byte は `/` なので、**祖先 dir の参照は境界条件を満たさない**。
- 実測: `dev-wave-t1086-report-receipt` が境界 byte を直後に伴って現れる landed file は **0 件**。
- さらに docs の引用慣習は `path:line` 形式 (`.../brief.md:12`) であり、`:` も境界ではないので
  **cite された file 自身への参照としても成立しない**。
- 極大の非境界 byte 列 7,098 件のうち、job dir を丸ごと覆える深さ 1 の被覆は 123 件しかない
  (job dir は 1,188 本)。**約 10% の job dir しか祖先条項の恩恵を受けられない。**

したがって **D247 条件 5 の祖先 dir 条項はほぼ恒真に不発**であり、抑止は
「たまたま cite された file 自身が、たまたま到達不能 blob と同一 bytes」の場合にしか起きない。
これが収量が 292 → 0 へ落ち、以後 0 のまま推移している構造的な理由である。

**親の候補集合の計算は監査の判定と完全に一致した。** bytes 一致 17 file のうち、
親が main だけから導いた被覆部分木 (278,272 file) に入るものは **0 件**であり、
監査の suppressions=0 と矛盾しない。候補先行方式の等価性はこの 1 点で実証されている。

## 9. 走査が本当に買っているもの

条件 5 を満たす抑止は構造的にほぼ 0 である。しかし走査は 2 つの成果物を出している。

1. **`suppressions`** (条件 1〜5 の連言) — 収量は構造的にほぼ 0。
2. **`unreferenced_copies`** (条件 1〜4 を満たし 5 を満たさない注記) — 今回 17 件。

**2 には実在の consumer がある。** D970 は到達不能 commit の破棄/救出を
「全 path 外部 = 破棄 / 一部だけ外部 = 破棄 / 外部控え皆無 = 救出」で分類すると定めており、
2026-08-27 の救出 (`docs/archive/worklog-phase3-0827-1019-1020.md`、T-1828) は
この分類で 19 件を 6 / 2 / 11 に分けた。同 file の 986 行目付近が
「既存手順の基準は監査の注記」と明記している。
**ただし同じ entry は、監査の注記が basename 一致条件のせいで不完全だったこと**
(監査が「控え無し」とした 9 path すべてに、別名の同一 bytes 実体が同じ探索根内に在った)
**も実測で記録している。**

したがって設計上の論点は、依頼の当初の枠組みとは別のところにある:

- **掃除 (`/cleanup-branches`) が走査から得ているものは実質ゼロ**である (抑止 0)。
- **救出 triage は走査の注記を使う**が、これは稀で意図的な活動であり 40 分を払える。
- 候補先行方式は `suppressions` を厳密に保つが、**`unreferenced_copies` の射程を
  被覆部分木内へ縮める** — つまり実際に価値のある方を壊す。
- 走査を既定 off にすると注記は完全に消えるが、**findings は 1 件も減らない** (安全側)。
  tool は既に未指定時に「repo 外の同一実体の探索を未実施」と開示する経路を持つ (D247 の却下欄)。

## 10. 親が測っていないこと

- cold での並列化の効き。親が測ったのは cold の C 並列 (bfs 既定) 1583.99 秒だけで、
  cold の単一 thread C 実装は測っていない。したがって「cold でも並列化は効かない」とは言えない。
  言えるのは「C + 並列でも cold 1584 秒であり、必要な 8.1 倍には届かない」までである。
- 2026-08-26 の抑止 292 対が、どの条件でどの file 群に効いていたか。
  当時の出力は repo 内に残っていない。
- 索引化・cache 案の設計費用。
