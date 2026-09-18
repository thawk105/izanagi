# 段 1 brief — [T-2489] A-2 認証系列の scheduler.nodes=5 判断材料の実測

## 研究前進

論文の A 群 (A-2 = rr5 / rr50 の同一 workload certification) は、現行 policy (nodes=1) で 1 attempt
約 50 分・2 request が並走する。D1910 項 2 は「A-2 を 5 ノードにするか」を実測が揃うまで裁定しない
と定めた。本 wave はその実測 — A-2 固有の 5 ノード実走 1 本 — を取り、出力同値性・所要短縮・
queue 費用を現行と比較して insight に構造化する。完了判定は「nodes=5 の A-2 attempt が 1 本
(rr5 / rr50 の 2 request) 走り、WAL 時刻差・NQSV 会計・fan-out result が現行 attempt と並べて
記録できたこと」。indeterminate で止まった場合もその実機事実を同じ価値の成果とする。

## scope

**in:** 使い捨て submit-tree (job dir、main tip d2ebef7a4 から detached) の A-2 policy の
`scheduler.nodes` だけを 1→5 にした使い捨て commit から attempt `t2489-20260918a` を投入し完走
させる。所要 (Elapse・WAL 工程別)・queue 待ち・node 秒・出力 (verdict / certified / commits / rep 数 /
fan-out result の MAC 照合) を現行 attempt `t2364-20260907b` と比較する。insight 1 本 + worklog
fragment。裁定パッケージとして索引へ戻す。

**out:** wave branch での policy 変更 (実装差分ゼロ)、`collect` (materialize)、job body の変更、
gate・検査・台帳・一般化の新設、A-2 の科学的結論の更新、A-6 結果の A-2 への一般化。

## 確定済みユーザー裁定

- D1910 項 2: A-2 の nodes=5 は実測後に索引へ戻す。本 wave は裁定しない。
- D1810: fan-out 機構 (単一 multi-node request、head が rep 0、兄弟が rep 1〜、HMAC 権威)。
  A-2 job body は A-6 と同一 file (`tools/pegasus/paper_story_a2_certification.sh`) で
  rank>0 gate (T-2457 で修正済み) を含む。
- 規律 1・2・4 不変。規律 7: 現行 attempt の記録は無効化しない。追加であって置換でない。
- 実装面 (機械設定 JSON) は Codex `role=author` が書く。親は直接編集しない (submit-tree 内の
  使い捨て編集も同じ扱い)。

## 段 1 で判明した新事実 (段 4 で扱う)

**現行 A-2 の 50 分は、rr5 / rr50 の 2 request が別ノードで走りながら `~/.izanagi/bench.lock`
(共有 Lustre home) で performance 検査 pass と bench を cluster 越しに直列化した結果である。**
`orchestrator/campaign/lock.py:default_lock_path` は `IZANAGI_BENCH_LOCK` 未設定なら
`~/.izanagi/bench.lock` を使い、A-2 job body は設定しない (b10 / a5 の job body は `$TMPDIR/bench.lock`
に逃がしている)。t2364-20260907b の WAL 時刻は秒単位で整合する (handoff 参照)。
含意: (i) nodes=5 でも 2 head は同じ lock で直列化する。(ii) 所要短縮の帰属は「検査の並列化」
と「lock 待ちの短縮」に分けて書く。(iii) lock を node-local にする案は job body 変更 = scope 外、
静的見積りとして裁定パッケージに添える。

## (P1) 割れうる前提 — 親の provisional 裁定・攻撃対象

- (P1) 使い捨て submit-tree の 1 key 編集 + 使い捨て commit で、`submit_paper_story_a2_certification.sh`
  の clean-tree / canonical policy / qsub argv (`-b 5`) の検査を迂回せず通る。protocol_sha256 は
  不変 (scheduler は preimage 外、D1810 と T-2457 の実測)。
- (P2) A-2 の 2 request × 5 node は同時に queue に入れてよい (計 10 node)。queue 待ちも実測対象。
- (P3) 出力同値性は「verdict / certified / anomalies / rep 数 / WAL stage 列 / protocol_sha256」の
  一致で判定し、tps は同値性の対象にしない (確率的)。

## 不変条件

1. 規律 1: trace-enabled と trace-disabled は別ビルド・別 run。job body 不変。
2. 規律 2: 遠隔結果の欠落・不一致は `verify-remote-unavailable` (indeterminate)。pass に読み替えない。
3. 規律 7: t2364-20260907b の記録値を無効化しない。
4. wave branch の tracked 実装差分ゼロ。submit-tree の使い捨て commit は wave branch に入れない。

## 成果物

- `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md`
- `docs/spool/worklog/<seq>-t2489-*.md` (decisions fragment は新しい設計判断が無ければ無し)

## 既存被覆 (性質で検索、純増だけ)

T-2429 = 機構 + 生死確認、T-2457 = A-6 (rr95、1 workload) の 5 ノード実走 17 分 37 秒、
T-2486 = ssh session の cgroup 同値性。**A-2 (2 workload、write-heavy / balanced) の 5 ノード実走は
無い。** bench.lock の cluster 越し直列化は decisions / worklog / failures / runbook のどこにも無い。
純増 = A-2 の 5 ノード実測値と、直列化の事実。

## 変更面 (実アンカー)

| # | anchor | 変更 | 実装面 |
|---|---|---|---|
| 1 | `output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md` | 新規 | 否 |
| 2 | `docs/spool/worklog/<seq>-t2489-a2-nodes5-probe.md` | 新規 | 否 |
| 3 | (submit-tree のみ) `orchestrator/campaign/paper_story_a2_certification.v2.json` `scheduler.nodes` 1→5 | 使い捨て commit | 是 (Codex author、wave branch 外) |

## 実測・受入環境

- 実測: Pegasus `gen_S`、`-b 5` × 2 request、walltime 06:00:00 (policy 不変)。投入元
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-a2-nodes5-probe/submit-tree`。
- 受入: `tools/dev_wave_wait.py acceptance` 経路 (docs-only でも免除しない)。変異 matrix は
  wave branch の実装面差分ゼロにつき免除 (DW-S04)。

## 分割方針

軽量版。子は (a) submit-tree の policy 編集を行う Codex author 1 本、(b) 投入前の read-only
敵対相談 1 本 (indeterminate に落ちる経路と lock 直列化の読みを攻撃させる)。段 6 review 子は省略。
