単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-local-copy

作業木 (あなたが編集してよい唯一の木): /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273lc-probe
所有 path (これ以外を作成・編集しない): `tools/t2273lc_run_series.sh`、`tools/t2273lc_run_measure.sh`、`tools/t2273lc_run_warm.sh`、`tools/t2273lc_ab_analyze.py`、`tools/t2273lc_gate.conf`
これらは**使い捨ての計測 probe** で repo には land しない (親が実行前に repo 外の job dir へ退避する)。docs は編集しない。commit しない (起動器が終端で記録する)。

必読事項の射影 (読めなければ即停止し、読めなかった path を書いて終われ):
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/s4-ruling.md — 親の段 4 裁定。**「計測の事前登録」1〜8 が仕様の正本。**
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/probe/ — 前回 wave の probe 一式 (run-series.sh、run-measure.sh、run-warm.sh、t2825_ab_analyze.py、gate.conf、SHA256SUMS.txt)。これを改作元にする。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273lc-probe/output/insights/2026-09-21/t2825-ledger-refresh-ab/README.md — 前回の測定形 (§2、§5 系列、§6 走表・判定)。
- 前回の実データ (回帰確認用、読み取りのみ): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/runs/、submissions.log、measurement-tips.json、warm-A.json、warm-B.json。

## 目的

自分たちの受入 test 基盤の高速化 wave で、固定 2 tree (A = 測定時 local main の clean worktree、B = wave tip) の実受入を隣接 3 対 (`01 A 1` `02 B 1` `03 B 2` `04 A 2` `05 A 3` `06 B 3`、すなわち A,B / B,A / A,B) で逐次投入し、shard-0 の W_0 の対差で効果を判定する。前回 T-2825 の probe を最小の改作で再利用する。

## 改作の要点 (最小に)

1. job dir・slug を `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy` と `dev-wave-t2273-shard0-local-copy` に替える (ハードコードは 1 箇所の変数へ寄せてよい)。`measurement-tips.json` の形式 (A/B の worktree 絶対 path と 40 桁 sha) は前回と同じ。
2. 投入の門番 (他 session の受入 leader ≤ 1 ∧ load1 ≤ 60、周期・jitter)、flock による直列化、投入台帳 `submissions.log` との突合、HEAD・clean の前後照合、無効走の扱い (対全体を同順序で取り直す)、温め (両 tree 同じ手順) は前回のまま使う。前回の温め前提 (`warm_errors()` 等) は本 wave の job dir の `warm-A.json` / `warm-B.json` を要求する形のまま保つ (親が `t2273lc_run_warm.sh` で作る)。
3. 集計器 `tools/t2273lc_ab_analyze.py`: 台帳固有の量 (台帳 sha、台帳予測負荷、未登録件数、shard 間移動、旧 L 候補の固定 node、selected 集合の同一性を台帳由来で判定する部分) を外す。残す・出すもの: 走ごとの W_0・W_1・W_2・W_max (argmax)・shard-0 の O_max (worker・item 数)・L (worker・nodeid)・O_max − L・pre・post、最大占有 worker の item 列。対ごとの Δi = W_0(Ai) − W_0(Bi)、ri = Δi / W_0(Ai)。対差の中央値と対率の中央値を別々に。**land 条件の判定** (有効 3 対すべて Δi > 0 かつ対率中央値 ≥ 10 % → `land_condition: met`、それ以外 → `not-met` と理由、有効対 < 3 → `undetermined`)。**5 分目標の別判定** (B の W_max 3 走の中央値 ≤ 300 秒)。3 shard の collection / 選択 node 集合が A と B で一致するかの照合 (前回の collection 照合の仕組みを流用)。出力は JSON と markdown 表。
4. 判定式・閾値は s4-ruling.md「計測の事前登録」を正本とし、prompt のこの要約と食い違えば ruling に従う。

## 検査と報告

- 集計器を前回の実データ (T-2825 の runs/ と submissions.log) に当て、W_0 と対差が前回 README §6 の走表と一致することを確かめる (台帳を外した後も抽出が壊れていない回帰確認)。一致しなければ理由を書く。前回データは読み取りだけで、書き換えない。回帰確認の出力はファイルに書かず標準出力へ出す (所有 path 外にファイルを残さない)。
- シェル script は `bash -n` を通す。実受入の投入・dispatch・qsub はしない (親が行う)。
- 前回から変えた点を差分の要旨で列挙し、変えていない門番・台帳突合・温め前提を明記する。

## 出力形式

- `## 変更` (file ごとの要旨、前回からの差分)
- `## 実走` (回帰確認のコマンドと結果、`bash -n` の結果)
- `## 使い方` (親が叩く手順: warm → series → analyze、引数と出力 path)
- `## 総括` (3〜6 行)
