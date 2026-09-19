---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-verify-phase-adopted-backoff
seq: 2
---

## {{D:verify-phase-adopted-backoff-authorization}}. 採用候補 2 genome の検証相は S-1 (iv 付属) の規則を準用した追加検証とし、extime は候補共通 3 s、校正確定値の記録先は decisions・insight・results 稿とする

**決定 (ユーザー裁定 2026-09-19 の実装形。裁定文の逐語は `rulings-inbox` 控え `2026-09-19-verify-phase-adopted-backoff-authorization.md` と wave の段 4 裁定 `s4-ruling.md` (job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff/`) にある):**

1. **位置づけ (準用)。** 本検証相は `docs/phase3-main-experiment.md` 層 1 (iv 付属) の充足ではない。同節の対象は系側 gate 構成 (g_rl / g_rt) である。ユーザー裁定により対象を採用候補 2 genome — fixed-5 (`silo`、`BACK_OFF=1, BACKOFF_FIXED=5` + 共通 `NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0`、= T-1998 事前登録 v1 の target = A-2 rr50 採用値) と fixed-10 (`BACKOFF_FIXED=10`、A-2 rr5 採用値) — へ変え、同節の反復数 (N_verify = 8 独立反復 × 3 workload = 24 verify)、校正規則 (trace-enabled build で extime {3, 6, 10} s を昇順に各 1 回実測し verifier wall ≤ 600 s の最大値、下限 3 s)、判定規則 (全件 anomaly ゼロで pass、1 件でも anomaly で失格、N_verify は削らない、形式的信頼度 1−εⁿ は主張しない) を**準用**した追加検証として扱う。報告では「S-1 の検証相を通した」と書かず、「2026-09-19 裁定により対象を変え、S-1 (iv 付属) の規則を準用した」と書く。
2. **identity。** 候補は現行 pin `511c9538` + 現行 `patches/silo-backoff-fixed.patch` (改訂 `91a5bfca3` 後) の下で build し、`source_digest.resolve_evidence(genome, pin, cxx="g++")` の `src_token` と `source_bytes_sha256` の両方が build 前後で期待値と一致することを起動条件にする。期待値 = fixed-5 `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12` (T-1998 v1 target と bytes 一致)、fixed-10 `16c299355ba7d786534b320e99eb2a566622a3a3f9fee59c6b0886519a1a479d`。A-2 attempt `t2364-20260907b` の `src_token` (rr50-fixed5 `21def77c944b…`、rr5-fixed10 `955b452a332d…`) は改訂前 patch の値で不一致となるため期待値にせず、履歴上の対応として併記する (改訂の差分は生値 ≥ 3000 の復号分岐のみで、5 / 10 µs が選ぶ分岐は不変)。A-2 当時の source で建て直す案は採らない (規律 7: 当時の記録はそのまま保持し、本検証は現行 source の新しい事実として足す)。
3. **extime と予算。** 候補ごとに 1 値とし、3 workload すべての適格集合 (bench 完走 ∧ verifier 完走 ∧ `serializable` ∧ certified ∧ anomaly 0 ∧ verifier wall ≤ 600 s) の共通部分の最大値を採る。空なら 3 s へ丸めず「候補なし」。「≤ 4 時間/候補」は本走 24 verify の job 実消費 (dispatch Elapse の和) に束縛し、校正は別欄で報告する。本走の見込み (Σ 8 × (bench+数え直し+verifier) + Σ 8 × 保全 + 6 × 固定費) が 14400 s を超えるときは 1 段下げ、3 s でも超えるなら本走を投入しない。投入後の超過は途中で止めず、判定と別欄に「計画拘束の不充足」として書く。
4. **校正の確定値 (2026-09-19〜20、Pegasus gen_S、Codex author 作の runner sha256 `91bbf85d…82a7`)。** 適格集合は両候補とも write-heavy {3, 6}、balanced {3, 6}、read-heavy {3} → 共通部分 {3} → **extime = 3 s** (fixed-5・fixed-10 とも)。read-heavy 6 s は完走 (verifier wall 864.3 / 807.8 s、主 process maxrss 85.6 / 80.2 GiB) したが 600 s 超で不適格、read-heavy 10 s は規則により未実走。balanced 10 s は verifier が SIGKILL (2 node で再現、`killed_unknown`)、write-heavy 10 s は hard timeout 3600 s で未完走。校正で完走した 12 verdict はすべて certified・anomaly 0。本走見込み B̂(3) = 6346.5 s (fixed-5) / 5999.0 s (fixed-10)。
5. **未完走の扱い (07-16 校正器の「timeout = 校正全体の失敗」からの意図的変更)。** 校正 verifier の未完走 (hard timeout / kill / rc=2 / JSON 破損) は `indeterminate (operational)` として記録し、その extime 以上を打ち切り、完走 prefix から extime を決める。判定集合 = 本走 24 枠 ∪ 校正で完走した verdict とし、pass は「判定集合に anomaly 0 かつ 24 枠すべて完走・保全済み・identity 一致」で、未完走の校正走は件数と保全先を必ず開示する (「全走 anomaly ゼロ」とは書かない)。本走 verifier の未完走は同一の保全済み trace に対する再検証を 1 回だけ許し (bench は再生成しない)、それでも未完走なら当該枠は indeterminate のまま候補は未確定。verifier が anomaly を出せば再実行せず失格 (規律 2)。
6. **記録先と繰延べ。** `docs/phase3-main-experiment.md` は編集しない。同文書は `output/s1-freeze/known_axes_freeze.json` の source sha256 として凍結され `verify_document` が照合する (1 行追記の模擬で `FreezeError: source sha256 不一致`、2026-09-19 実測)。凍結文書の raw sha は `t080_freeze_migration.KNOWN_AXES_RAW_SHA256` に pin され、`IZANAGI_FREEZE_HOLD` の解除はユーザー明示命令だけである。よって (iv 付属) の「確定値は本節へ日付付き追記」は**未履行の繰延べ**であり、本 wave の校正確定値は本決定、記録 insight (`output/insights/2026-09-20/verify-phase-adopted-backoff/README.md`)、results 系列稿 (`docs/paper-story/results/2026-09-20-verify-phase-adopted-backoff.md`) に日付付きで置く。phase doc への追記は、凍結束縛の解除 (ユーザー明示命令) または source 束縛の移設の裁定の後に別 wave で行う。凍結文書の再発行・hold 解除は本 wave では行わない。
7. **その他の不変条件。** trace-enabled build の bench throughput は診断生値として保存し、性能値・比較・優劣に使わない (規律 1)。verifier CLI (`python3 -m orchestrator.verifier`) の verdict をそのまま採り、受理集合・引数意味論に触れない。runner は repo 外 (job dir) に保全し commit しない。新 protocol・追加 gate・certification の昇格・pipeline の capability 認証への接続は scope 外。

**理由:**
- 事前登録の対象を裁定で変えた以上、「充足」と書くと旧 gate 候補の検証完了を意味してしまう (段 3 レンズ A)。準用と明記すれば、反復数・校正・判定の規則を借りつつ何が新しい事実かが残る。
- identity は事前照合で既知の不一致が出ており、A-2 の旧 token を期待値にすると意図した候補が起動しない。現行 source の全桁を起動条件に固定すれば、観測後に期待値を動かす余地が無くなる。
- Pegasus gen_S の DRAM 上限 (約 115 GiB) は資源事実であって正しさシグナルではない。旧規則を機械的に適用すると、balanced 10 s の kill (原因は `killed_unknown` のまま未確定) の時点で今回の校正は未確定になり、本走を投入できない。未完走を開示付きで記録し、完走 prefix から extime を決める形は、規律 2 (anomaly 即 reject) と規律 3 (信号を後付けにしない) のどちらも緩めない。
- 凍結文書の source 束縛を本 wave で動かすと、`t080` の raw sha pin と hold に連鎖し、受入が赤になる。繰延べを未履行として明記する方が、無断の再発行より正直である。

**却下した選択肢:**
- workload 別 extime — 条件が 3 値になり比較・会計が複雑になる。候補共通値の規則を校正前に固定した以上、校正結果を見て切り替えない。
- A-2 当時の patch で fixed-10 を建て直す — 当時のバイナリ同一性まで保証せず、別 build の校正・identity 確認が要る。
- 校正未完走で停止 (07-16 校正器の規則) — 上記のとおり今回の校正が未確定になり本走へ進めない。未完走の原因が資源上限だと確定したわけではない。
- phase doc への追記と凍結文書の同時再発行 — hold の解除権限は人間にある。
- 校正込みで 4 h に束縛 — 校正は phase doc の内訳でも別項目で、拘束数値の文言は本走 24 verify を指す。校正の実消費は別欄で全部報告する。

**研究状態への影響:** certified 選択・レポート・台帳の値は変えない。変わるのは、採用候補 2 genome について「独立 8 反復 × 3 workload (extime 3 s) の trace 検証で anomaly が出たか」という操作的事実が results 系列に 1 本足されることである。
