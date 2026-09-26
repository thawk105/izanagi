## 対応表

| 所見 | 判定 | 根拠 file:line |
|---|---|---|
| A1 | closed | [集計器:198](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:198) は A のみ空、B のみ指定 node 1 件を多重集合で照合する。不一致の対は [集計器:465](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:465) で無効となり、[集計器:493](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:493) の有効 3 対に入らない。 |
| A2 | 裁定で一部 refuted・E2 で訂正済み | M5 の最初の失敗は [test:1179](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1179) の実関数呼出し回数 assert。理由は [E2:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s6-ruling.md:20) と一致する。 |
| A3 | closed | 共通 node の各 shard 割付を多重集合で照合し、差を拒否する。[集計器:208](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:208) |
| B1 | closed | A1 と同じ。A 同士・B 同士の collection と 3 shard selected も完全照合する。[集計器:393](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:393) |
| B2 | closed | 差分で `Decimal`、`ESTIMATE_NOTE`、`all_rows` の削除を確認。[修正前後の差分](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.v1.py.txt) |
| B3 | 裁定で refuted・不変 | direct との mtime 照合は受理集合の証拠として残す裁定。[裁定:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s6-ruling.md:12)、[test:1190](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy/orchestrator/tests/test_s8b_oracle_driver.py:1190) |

## 新規所見

E1 の**系列投入前の確認**は集計器だけでは保証されない。B の事前 collection ファイルが無い場合、B 走自身の collection を基準にできる。[集計器:383](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:383) 親は投入前に A/B の collection と割付を照合した記録を確認する必要がある。[裁定:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s6-ruling.md:19)

## 総括

**修正後 GO。** E1 の走・対の判定は指定差分だけを許し、無効対を land 条件から除外する。前後差分上、判定式、10%・300 秒の閾値、順序、門番、5 分別判定は不変。[集計器:425](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:425)、[集計器:493](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/probe/t2273lc_ab_analyze.py:493)  
変異 spec の M1〜M5 の置換元は実装に一致し、最初の失敗箇所も登録理由と E2 に静的に一致する。[変異 spec](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/mutation-spec-probe.json:22)  
系列投入前確認の成立は親が確認する。実測テストは行っていない。