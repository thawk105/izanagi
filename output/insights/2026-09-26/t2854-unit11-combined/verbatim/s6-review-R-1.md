## 所見表

| 重大度 | 判定 | 所見・根拠・最小修正案 |
|---|---|---|
| **must-fix** | **real** | Codex 子の合計が誤っている。[記録:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/output/insights/2026-09-26/t2854-unit11-combined/README.md:129) と [worklog:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/docs/spool/worklog/2026-09-26-dev-wave-t2854-unit11-combined-1.md:15) は **112 calls・1,483 秒**とするが、job dir の `codex/dev-wave-t2854-unit11-combined/*/receipt.json` 8 本の `actuals` を独立合算すると **116 calls・1,546.094 秒**。両箇所を修正し、集計対象を明記する。 |
| **should** | **real** | [worklog:28–32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/docs/spool/worklog/2026-09-26-dev-wave-t2854-unit11-combined-1.md:28) は旧 [entry 1852 の T-2854 本文](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/docs/archive/worklog-phase3-0923-1852.md:633) から、単位 1〜3 の変異各 6 件、単位 3 の mocc 存在違反 0 と認定の留保、単位 4・5 の実装と拒否条件などの事実を落としている。更新本文に要点を戻すか、旧本文を保持して単位 11 の差分だけ加える。 |
| **should** | **real** | [failures fragment:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/docs/spool/failures/2026-09-26-dev-wave-t2854-unit11-combined-3.md:13) は恒久対応を「実登録 artifact を入力に使う」の適用と記す。しかし修正後の [selftest.py:215](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/selftest.py:215) は `C1-preprocess.json` 由来の 21 組をコードへ転記した合成 row を使い、実 artifact 自体は入力していない。再発の発見・修正・near miss という記述は裏付けられる。末尾を「実測の 21 組を転記して代表性を改善。実 artifact を直接入力する対策は未実施」と直す。 |
| **nit** | **疑い** | [記録:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/output/insights/2026-09-26/t2854-unit11-combined/README.md:70) の圧縮 trace「計 38 MB」は、保持された 8 ファイルの実サイズ **39,437,099 byte = 約 37.61 MiB** と単位が曖昧。`約 38 MiB` に直す。 |

## 不成立の攻撃

- **主要な計算値の誤写は不成立。** `evidence/compute-1/` の JSON から、C0〜C6 は全て pass、TPC-C は silo **36,106 C / 493,700 R / 529,986 W**、mocc **34,859 C / 484,347 R / 519,376 W**、種別内訳も記録どおり。YCSB の C、verifier の reads・writes・keys・edges・certified も両 protocol で一致した。21 entry は 12 source、前処理一致 21/21、include 負例不一致 9/9、構文 rc=0 が 21/21。H-line は展開不一致 9 件・一致 12 件、include 活性一致 21 件で、4 変異の理由と KILLED も一致した。
- **系列・サイズ・時間の攻撃は不成立。** `mk-c2p.log` と `compute.json` は C→C1'→C3→C2'、新規 commit 1 件、差分 4 file を支持する。4 binary の byte 数と逆アセンブル digest、TPC-C trace byte 数、bundle **3,200,920 byte** と SHA-256、selftest **185/185** は一致。`compute-1.log:35–46` は request **29455.nqsv**、開始 **14:45:37**、終了 **14:49:36**、Elapse **243 秒**を支持する。
- **D297 合格・TPC-C certified の僭称は不成立。** [記録:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/output/insights/2026-09-26/t2854-unit11-combined/README.md:17) と「主張しないこと」は整合する。`d297-C-to-C2p.stderr` は header 差分での拒否を示し、TPC-C の B0 JSON には verifier 認定の主張がない。
- **4 択の既裁定誤写と一方的な推奨という攻撃は不成立。** [記録:104–115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-unit11-combined/output/insights/2026-09-26/t2854-unit11-combined/README.md:104) は、D297 の header 拒否、D2207 の `<set>` include の射程、D2225 決定 6 の過去の名乗り、D780 項 2 の別防壁の留保、択 3 で必要な D2225・D2230 の再裁定を区別している。択 1 の不利な点と択 2 の速さも記している。ただし択 2 の「16 文脈」への拡張だけでは、表自身が挙げる consumer TU の閉包不足は埋まらない。これを保証済みとは読まないことが条件となる。

## 判定

**NO-GO（記録の受理）。** 計算結果と受理方式の骨格は支持されるが、receipt 合計の確定的な誤りを直す必要がある。worklog の旧事実と F109 の対策表現も修正対象。

## 総括

結合確認そのものへの反証は見つからなかった。記録上の最大の問題は **Codex 実績の 112 / 1,483 が一次 receipt の 116 / 1,546.094 と一致しないこと**である。