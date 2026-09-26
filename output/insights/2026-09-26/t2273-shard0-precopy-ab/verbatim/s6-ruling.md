# 段 6 裁定 — probe レビュー 2 本 (commit 2ebf25e24)

レビュー `codex/s6-review-a-out.md` (計測の正しさ、修正後 GO)、`codex/s6-review-b-out.md` (過剰・削除、修正後 GO)。両方 check_codex_output rc=0。fix 前の統合 snapshot = `author-t2273pc-probe` の `2ebf25e24`。

| 所見 | 裁定 | 成果物影響 (放置時) | fix |
|---|---|---|---|
| RA1 = RB1 | real・must-fix (親が runner:650–654 / analyzer:895–896 で実在確認) | 全対が `intervention_env` 偽で無効 → 判定不能 | P の child env の `T2273_PRECOPY` を run.json に記録、`T2273_LOCAL_OUTPUT_SOURCE` は未設定なら None に戻す |
| RA2 | real・must-fix (親の検収でも指摘) | P だけ controller の同期 import 分 pre と Δ が歪む | import と写し生成を thread 内へ。hook は identity 計算と thread 起動だけ |
| RA3 | real・must-fix (親の検収でも指摘) | dir size 差で有効対が恒偽になりうる | digest は regular file の path・size・mode・mtime_ns、dir は path 集合を別 digest |
| RB2 | real・must-fix | P 側 digest 欠落の key を飛ばして恒真 | 全 builder key に A/P 各 1 件の digest を要求 |
| RA5 = RB3 | real・must-fix | 測定失敗を効果不足と読み (b) を誤って名指し | 集計は有効対に限定。有効 3 対未満は「判定保留 (取り直し)」で (b) を名指ししない |
| RA4 | real・should | 必須観測の欠落を有効扱い | `analyze()` の missing を有効性に入れる。P で構造上生じる欠測 (例 `copy.list`) だけ明示的に除外 |
| RA6 = RB4 | real・should | memo 超過を取りこぼし件数が過少 | 早期 memo 待ち超過は conftest が実際に出す例外文・rc (実文を conftest から引く) か plugin の構造化 event で判定 |
| RB5 | real・should | (b) の対象を総和で誤名指し | phase は有効対の key 別・条件別の中央値で出し、選定根拠 (key・値) を併記 |

## 追補 — 焦点再レビュー 1 (`codex/s6-focus1-out.md`、修正後 GO、fix 後 commit `2a1b83339`)

- closed 6 件 (RA1=RB1、RA3、RB2、RA4、RA5=RB3、RB5)。
- RA6 = partial (子は memo module を射影外で照合できず) → **親が実測で closed**: analyzer の接頭辞と理由 `publication-timeout` は `orchestrator/tests/real_repo_receipt_memo.py:69, 689, 698` と `orchestrator/tests/sort_swo_oracle_receipt_memo.py:51, 742, 751` の実出力と一致。前回 wave 02-A の実例も同じ理由 (memo publication timeout)。
- RA2 = partial / FN1 (写しの dir 作成自体の失敗時に marker が置けず worker が 180 秒待つ) → real・nit。放置しても P は例外で無効になり fallback しないので判定の向きは変わらない (無駄は最大 180 秒)。fix しない。
- FN2 (出力に基準式・pre 外れの説明文がない) → real・nit。判定結果と `pre_outside_55_80_s` は機械出力にあり、説明は親が insight に書く。fix しない。
- 以上で段 6 を閉じる (fix 1 巡)。本走に使う probe = `2a1b83339` の 3 file。

## erratum E1 — job 1 の集計で判明した analyzer の登録外れ (2026-09-26 21:05 JST 頃、job 2 投入前)

job 1 (29983.nqsv、rc 0、Elapse 931 秒) の `--ab-dir` は有効性「偽」を返した。落ちた 4 項目の原因を生データで確かめた:

1. `builder_keys_equal`・`stat_digest_equal`・`visible_digest_equal`: analyzer が builder を「key + その key を最初に要求した test の nodeid」で突き合わせている。key `["AI-Agent: none", false, true, false, false]` を最初に要求した test は A と P で違った (同じ test 関数の別 parametrize、xdist の割付による)。**A・P の 8 builder は全部 file digest `fe6adb54c72e…`・dir digest `805f2c49317f…`・可視集合 `465e155982d8…` (30,707 件) で一致している。** s4-ruling §3.1 の登録は「builder の key ごと」なので analyzer が登録から外れていた。→ 比較は key だけで行い、nodeid は記録だけにする。
2. `required_observations`: 欠けているのは資源標本の `lustre: no readable llite/*/stats` だけ (A・P とも)。第 4 回 README §3 の既知の欠測 (「analyzer の rc=1 はこの資源欠測だけによる」、mdc md_stats は取れている) で、s4-ruling §3.1 の有効性項目にも入っていない。→ llite stats の読取り不能だけによる資源標本の不完全は必須観測から外し、出力に除外理由を明記する。他の欠測は従来どおり無効。

判定基準 (§3.3 の式、閾値) と有効性の項目は変えない。生データの再取得は不要 (analyzer を再実行するだけ)。この修正は job 1 の Δ を見た後に行うが、変更は登録文言への回復だけで、効果の値によって向きが変わる余地はない。runner・plugin は変えないので job 2 は同じ probe で並行して投入した。analyzer は Codex fix2 (branch `author-t2273pc-probe-fix2`、基点 `2a1b83339`) で直し、job dir `probe-fix2/` に置く (走行中の `probe/` は触らない)。

scope 内・全採用。一枚岩 (3 file が同じ run.json / span 契約を共有) なので fix は Codex 1 単位 (同じ子 worktree、branch `author-t2273pc-probe-fix1`)。fix 後に焦点再レビュー 1 本 (DW-S06-C / DW-O16、所見ごとの closed / partial / regressed 表)。
