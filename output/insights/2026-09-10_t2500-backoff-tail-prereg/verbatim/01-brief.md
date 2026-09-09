# [T-2500] 段 1 brief — 静的 backoff 右側の本格格子と停止基準の事前登録

**研究前進。** 論文 `docs/paper-story/2026-08-26.md` の残件 B-10「機序説明の帯域外への拡張」のうち
**過抑制域**。正式格子 `EXTENDED_SWEEP_US` の上端は 1000 µs で、その右側は正式系列に 1 点も無い。
D1813 第 1 段の探索 ([T-2418]) は 2000 / 4000 / 9999 µs で abort 率が単調に下がり続け、飽和を示さなかった。
**本 wave の完了判定** = 「(1000, 9999] の本格格子・反復数・停止基準 (飽和判定)・失敗条件を、本走の結果を
見る前に固定した事前登録が、凍結された commit として repo に存在すること」。本走の投入は次 wave。

**確定済みユーザー裁定。** D1813 (2 段構成 / 探索値を正式標本へ混ぜない / 本格格子は探索後・投入前に凍結)、
D1848 (探索走は凍結格子へ点を足さず RUN_KIND と campaign identity を分ける)、D95 (実装面は Codex author)。

**scope (放置時の成果物影響つき)。**
1. 新規 `docs/b10-backoff-static-tail-preregistration.md` — 格子・反復数・停止基準・失敗条件・開示・
   束縛・主張範囲。無いと本走が事後選択の格子で走り、tail の記述が事前登録なしの主張になる。
2. `docs/README.md` の地図へ 1 項追加 (§ 事前登録の並び、`b10-backoff-shape-preregistration.md` の隣)。
3. 段 7 の spool fragment (worklog / decisions)。

**scope 外。** 本走 driver・第 4 の RUN_KIND・campaign identity・report schema・PBS 投入 (すべて次 wave)。
正値 `BACKOFF_FIXED` の pointwise meaning witness gate の新設 ([T-2501]、ユーザー裁定待ち)。
既存正式系列 (`extended` / `t2266-tail`) の受理集合・凍結格子・test の変更。仮想リスク向けの gate・台帳。

**不変条件。**
- 規律 2 — 本走に要求する correctness gate と静的 amount ごとの binary 相異検査の完全性は、先例
  (t2266 / t2418) と同じ強さで書く。探索だから緩める、は採らない。
- 探索 3 点の**測定値**は正式推定へ混ぜない。
- 表現上限は 9999 µs (`STATIC_BACKOFF_MAX_US`)。格子はこれを超えない。
- `EXTENDED_SWEEP_US` (0..1000、上端が test に pin) を 1 byte も変えない。
- 凍結後の改訂は erratum だけで行い、結果 commit より後に書いた変更は事前登録に数えない。

**(P1) 親の provisional 裁定 — 段 3 の攻撃対象。**
- (P1-a) 本 wave は **docs-only**。driver / RUN_KIND を書かない。→ consumer の無い事前登録が恒真でないか。
- (P1-b) 格子の abscissa として探索 3 点 (2000 / 4000 / 9999) を再利用してよい。禁じられるのは測定値の混入。
- (P1-c) 反復数と動作点は既存枠と同じ `REPS=5` / `EXTIME=3` / `RECORDS=1_000_000` / `THREADS=48` を、
  共有定数への参照ではなく **literal** で固定する (D1848 の理由と同じ)。
- (P1-d) 停止基準は「表現域内で飽和しない」を正当な結末として前向きに含む。
- (P1-e) 対象 workload は探索と同じ 3 つ (write-heavy / balanced / read-heavy)。

**成果物の形。** 先例 `docs/b10-backoff-shape-preregistration.md` に倣い、散文の規則 + HTML comment で
区切った機械可読 JSON spec ブロックを持つ 1 file。spec が判定規則の正本で、後続 wave の driver が
コード定数の代わりに parse する。§ 構成もその先例に合わせる (効力と限界 / 何を主張しないか / 開示した事実 /
前向きに固定した規則 / 機械可読 spec / 検出力について主張しないこと / 失敗条件 / 発効と束縛)。

**既存被覆の検索結果 (純増の確認)。** `docs/` に静的 tail の事前登録は無い。`b10-backoff-shape-*` は
形 (待ち方) の登録で量の tail を持たない。`backoff-counterfactual-*` は adaptive の反実仮想。
`git grep b10-backoff-static-tail` は 0 件 (新規 path の pin 閉包は空)。**純増 = 右側 tail の本格格子・
停止基準・失敗条件の前向き固定**だけ。

**変更面 (実アンカー)。**

| path | 変更 |
|---|---|
| `docs/b10-backoff-static-tail-preregistration.md` | 新規 (本体) |
| `docs/README.md` L25〜L28 の直後 | 1 項 (3〜4 行) 追加 |
| `docs/spool/worklog/`, `docs/spool/decisions/` | 段 7 の fragment |

**並列分割。** docs-only なので段 5 の実装単位は無い (親が docs 本文を書く)。段 2 plan 1 本、段 3 敵対相談
2 本 (レンズ A = 事前登録としての前向き性・恒真性・規律 2、レンズ B = 数値設計と既存系列・時間予算との整合)、
段 6 レビュー 2 本。実装面の差分が 0 なら変異 matrix は DW-S04 により免除、受入全走は免除しない。

**受入・実測環境。** 受入全走は login node の受入形 (`tools/dev_wave_wait.py acceptance`)。
本 wave は計測を行わない。機体固有情報は `docs/pegasus-runbook.md`。
