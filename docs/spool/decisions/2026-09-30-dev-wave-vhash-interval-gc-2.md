---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-vhash-interval-gc
seq: 2
---

## {{D:igc-prototype-design}}. Cicada の区間 GC 試作は「外すが走行中は再利用しない」変種を計測し、install は tuple lock の下で行う

**決定:** VHash 論文 md_18 の区間 GC 試作 (`patches/cicada-interval-gc-variant.patch`) について、次のように決めた。

1. 保護点 (各 thread の wts・wts−1・rts、MinWts−1、MinRts) の採取は leader が `gc_inter_us` ごとに行い、GC flag の全員待ちとは独立に回す。
   閾値は H = (T<<8)−1 とし、begin の途中の thread があればその回は採取しない。
2. 剪定は書き込み時に行う (Steam §4.3 と同じ契機)。条件は (a) committed、(b) どの保護点も可視区間に入らない、(c) wts(次) ≤ H、
   (d′) 各保護点について wts ≤ p の最初の鎖上の節点 (状態を問わない) の直上でない、(e) MinRts の可視版より新しい、の全部とする。
3. blind write の install は tuple の `gc_lock_` の下で `latest_` から挿入位置を探し直す (lock を使わない削除と挿入の競合を閉じる)。
4. 計測と正しさ検査の変種は `--cicada_igc_debug_mode=1` (鎖から外すが走行中は再利用しない) を既定とする。
   mode 0 (再利用) は、安全でないことが実測で分かっている実験用とする。
5. 全ての分岐を単独の `#if MACRO` 行にし、macro は 0/1 の 4 つ (`CICADA_INTERVAL_GC`・`_GC_GENERAL`・`_COUNT`・`_LONGTX`) とする (条件 gate の観測能力に合わせる)。

**理由:**
- 長い tx の thread は tx 中に GC flag を上げないので、flag 待ちの後ろに採取を置くと長い tx の間は保護点が更新されない (util.cc の leader)。
- 当初の (d) (committed の可視版の直上を残す) は、blind write の足場 `later_ver_` が他 writer の pending 版の上にあるとき足場を外しうる (smoke3 の一般形 SIGSEGV)。
- 補正 4 の退役列 + epoch と A13 の修正の後も、mode 0 は smoke9 / 9b で SIGSEGV・停止した。mode 1 は smoke6〜10 の全走行で正常だった。
- 安全な解放条件 (外した時点で走っていた全 tx の終了) は長い tx 自身が塞ぐので、正しく実装できても bytes は長い tx の終了まで返らない (Steam も解放を所有 tx の解放まで遅らせる)。

**却下した選択肢:**
- 外した版を stock の pop (wts < MinRts) で再利用する当初の S5 — read set に生ポインタを持つ tx の反例がある。段 2 plan と段 3 相談が推奨した「外した時点で走っていた全 tx の終了待ち」が正しかった。
- `wts < MinWts` の版だけを外す — 長い update tx の間は、区間 GC が狙う区間そのものを外せなくなる。
- 条件 gate の受理述語を複合条件へ広げる — gate の新設に当たる (DW-O13)。patch を gate の形に合わせた。

## {{D:igc-s8-positive-not-substituted}}. 区間 GC の壊し正例は事前登録の cell (ronly_wait) だけで数え、他 cell の検出は補助として別に数える

**決定:** md_18 の正しさ集計 (`orchestrator/campaign/vhash_interval_gc.py` の `aggregate_verification`) は、次のとおりにする。

- 壊し patch の正例は、段 4 裁定 S8 が事前登録した ronly_wait cell と帰属規則 (長い read-only tx を含む辺) だけで数える。
- K・R (長い tx の無い cell で末尾 worker を代役にした帰属) と wait_after_reads (帰属 0 の巡回) の検出は、事前登録外の補助として別の欄・別の件数で出す。
- status は passed / normal_arms_passed_s8_positive_unmet / failed の 3 値とする。
- 正常 3 腕の失格 (巡回・integrity・C 行・verdict・read-WTS 不一致) は fail-closed のまま aggregate を止める。

**理由:**
- 本計測では ronly_wait の壊し patch が発火 0 だった (試作が read-only 長 tx の下で一度も剪定しない)。
- 段 5 の B1-11 指示で、親が S8 を「どこか 1 cell で検出すれば成立」と言い換え、集計が `passed` を出していた。段 6 の敵対レビュー 2 本 (R1・B-01) が独立に指摘した。
- 事後に正例の cell を差し替えるのは、正しさシグナルの後付けに当たる (規律 3・7)。

**却下した選択肢:**
- 正例の cell を K・R へ付け替える裁定の補正 — 結果を見た後の条件変更である。
- S8 正例不成立で aggregate を止める — 正常腕の検査結果と計測値の記録まで失う。性能値は元々「未検証の診断値」であり、不成立は status と一次資料で明示すれば足りる。
