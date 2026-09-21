# [T-2830] 段 1 brief (確定、2026-09-21 13:39 JST (file mtime)、base = local main d99c556df = T-2795 land 済み)

**研究前進:** B-5 生成器対照の本走 (1,773 論理 session ≈ 251 h の node 時間) は、現行 job body では並列化しても総 wall が縮まない —
試走 4 job で wall の 59% (8.8 h) が home 共有 `~/.izanagi/bench.lock` の待ち (D2199、insight §6.3)。本 wave は本走認可の前提となる実装を置く。
完了判定 = B-5 mode の lock が node-local になり、launcher が job ごとの submit-tree で 4 job を組め、既存 3 経路の driver argv が bytes 不変、変異負例が KILLED。

**scope (実装面、Codex author):**
1. `tools/pegasus/p3_s4_loop_pegasus.sh`: B-5 mode で `IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` を export (B-10 `b10_backoff_grid.sh:280`・A-5 `a5_second_boot_backoff_sweep.sh:259` と同値)。
2. `tools/pegasus/b5_contrast_launch.py`: job ごとの submit-tree を受ける (または cache 公開競合の検査)。
3. test: 既存 3 経路の driver argv の bytes 不変、B-5 mode の driver が node-local lock path を観測すること、launcher の job ごと tree の argv exact。
4. 変異負例 (lock 行の削除・既定 home への差替え・B-5 分岐外への移動・tree 共有への戻し)。

**scope 外:** gate・検査・台帳の新設、B-5 本走の投入 (未認可)、事前登録の発効、試走結果の再解釈、`loop.py` / `p3_s4_loop.py` の編集
(85 path の contract loader closure に入る、T-2795 insight §5)。

**確定済み裁定:** D2199 (試走の運用事実、本走の job body / launcher 設計の再提示項)、D2205 (T-2795: pair mode は driver 1 起動、`--stock-control` 単独 = B-5 slot は不変)。
B-5 本走は未認可 (insight §8)。

**不変条件:** 規律 2 — lock の**所在**だけを変え、performance verify pass と bench が `bench_lock()` 下で回る構造 (`pipeline.py`) は変えない。
規律 7 — 試走の記録 (job body sha 9ef925d6… の reservation.json 4 件) を無効化しない (同一 job 内の自己整合照合で literal pin ではない)。
D2205 の認可 session・結合検査を壊さない。事前登録 v1 は未発効で §12 の bytes 固定は未成立。

**用語:** 「既存 3 経路」= job body の非 B-5 driver 起動 — (a) proposal 単独 (`--run-iteration`)、(b) proposal + pair (`IZANAGI_S4_STOCK_CONTROL=1`)、
(c) fixture (`--value`)。出典: T-2797 insight §1 の変更表「既存 3 経路は bytes 不変」、T-2795 後の分岐で数え直し。

**割れうる前提 (親の provisional・段 3 の攻撃対象):**
- (P1) 適用範囲 = **B-5 mode 限定** (B-5 分岐内、driver 起動直前)。既存 3 経路は argv だけでなく env・挙動とも不変。bench lock は driver 内部でだけ取られる
  (job body の prebuild は取らない) ので B-5 の全取得を覆う。反論面: B-10 / A-5 は job 全体で設定しており非対称、K2 手動 loop は別ノードと直列化されたまま。
- (P2) launcher = **job ごとの submit-tree**。cache root は `p3_s4_loop.py` の worktree 隔離分岐で submit-tree 内の CCBench 配下に固定され 4 job 共有、
  node-local lock で build の同時性が上がるので、検査だけでは本走が fail-closed で落ちる。tree を分ければ構造的に消える。
- (P3) tree の供給 = **親が 4 本を用意し launcher が各々を既存 `validate_submit_tree` で検査** (launcher に checkout 生成を持たせない)。

**親の実測 (段 1 追補、13:45 JST):** job body の `TMPDIR` は `/scr/$USER/p3-s4-loop-pegasus/<jobid>` なので、`$TMPDIR/bench.lock` は
node-local というより **job-local** (同一ノードの別 job とは排他しない)。成立の前提は gen_S の割当て — リクエストごとに CPU 48/48 の
logical host で、自分の request どうしが同じノードの CPU を分け合わない (`docs/pegasus-runbook.md` §1・§7、`qstat -Qf gen_S` 実測)。
ただし `Exclusive submit = OFF` で専有はスケジューラ保証外。B-10 / A-5 も同じ前提。単独性 (他 process との並走) の確認は bench lock ではなく
計算ノード上の probe の役割であり、本 wave はそれを変えない (F3 [計測汚染] は攻撃面として段 3 に渡す)。

**段 4 直前の裁定 inbox 再走査 (追補 2):** wave 開始 (08:20) 後の 09:10 に land した **D2200 項 1** (第 28 回、ユーザー「推奨通り」) が
T-2830 の範囲を「job body の node-local `IZANAGI_BENCH_LOCK` と job ごとの submit-tree」と定め、(2) の 6 で「本走の launcher は job ごとに
submit-tree を分ける (D2199)」と確定した。→ **(P2) は provisional でなく確定済み裁定** (cache 公開競合の検査だけの案は採らない)。
(P1) (B-5 mode 限定 / job 全体) と (P3) は裁定が定めていないので provisional のまま。同項の「全 arm 同一の job walltime (§3.3)」・Tier0・
§12 の各項目は T-2830 と別の AI 手番として列挙されており、本 wave の scope 外 (依頼「本題だけ」)。

**成果物:** コード + test + 変異 spec / 結果 + insight (`output/insights/2026-09-21/t2830-b5-node-local-lock/`) + worklog / decisions fragment。
**分割:** 段 5 author 2 本 — A1 = job body + `test_p3_s4_loop_job_contract.py`、A2 = launcher + `test_b5_contrast_launch.py` (所有 file は重ならない)。
**受入・実測:** 受入全走は `tools/dev_wave_wait.py acceptance`、焦点走は計算ノード dispatch。実機 job は投入しない。
