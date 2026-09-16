# 段 4 裁定 — [T-2228] screening 関門の生死確認 (2026-09-17 01:20 JST)

入力: `s1-brief.md`、`artifacts/.../s2-plan.md`、`s3-lensA.md` (正規入口・環境等価性)、`s3-lensB.md` (証拠の恒真性・規律 2/7)。
裁定 inbox の再走査: T-2228 関連の更新なし (01:00 JST)。

## 裁定 0 — 所見の分類

| ID | 分類 | 採否 | scope |
|---|---|---|---|
| A1 / R6 (CLI が投入元 submodule へ一時 patch、親の不変条件と衝突) | real | **採用 — 不変条件側を改める** (裁定 1) | 内 |
| A2 / R7 (`_assert_single_tenant` は ycsb pgrep だけ、単独性の証明でない) | real | 採用 — launcher で観測を加える (裁定 2) | 内 |
| A3 (prefix の記録先は `completion.preimage.dependency_prefix`、roots field は空) | real | 採用 — brief 前提 4 を訂正 | 内 |
| A4 / R5 (同版 prefix ≠ A-5 と同じ binary、最小 screening ≠ 全点 family) | real | 採用 — README の限定 | 内 |
| A5 (直接 DNS 失敗 ≠ proxy 経路の不通、前回の取得成功は継承 proxy の推定) | real | 採用 — README に推定と明記 | 内 |
| A6 / P5 (prepare 3 回・build 4 回、90 分は予算であって上限でない) | real | 採用 — brief 訂正 | 内 |
| A7 / R1 / R2 (baseline meaning は unestablished、成功 reason は識別不能) | real | 採用 — 緑の定義を限定 (裁定 3) | 内 |
| A8 (rc=16 は未実行を意味しない、再投入は実行有無で決める) | real | 採用 (裁定 4) | 内 |
| R3 (赤の detail は driver/screening 境界で落ちる) | real | 採用 — README の記録粒度の約束を限定 | 内 |
| R4 (環境供給は到達性を変える、「受理結果も不変」と書かない) | real | 採用 — README の規律 2 の説明 | 内 |
| R8 (赤分類表に source identity / perf preflight を追加) | real | 採用 | 内 |
| A9 (A-5 改修が必須) / A10 (`-I` が env を消す) / A11 (bench lock 固有化が必須) / A12 (`TMPDIR=/scr` が関門を変える) | refuted | — | — |
| F1〜F5 (空 request・force・stock checkout 握り潰し・空 preprocess・既存成果物の更新) | refuted | — | — |
| レンズ A should-fix: `completion.json` 回収、実行 python・lock path・A-5 差の記載、launcher bytes の保存 | real | 採用 (成果物) | 内 |
| レンズ B nit: tracer / strace 採用、arm record 永続化の横展開 | — | 不採用 (仮想リスク向け追加、D1912 が DW-G03 で保留) | 外 (裁定パッケージ候補) |
| execution receipt の永続化先が無い (段 2) | real | 記録のみ (限界) | 外 |

## 裁定 1 — (P1) 投入形: generic dispatch + job dir の最小 launcher (Codex author) + 正規 CLI `main`

- 依頼文の「正規入口 (CLI の screening_fixed_us、tools/pegasus の投入 script)」は、**現行 `backoff_sweep.main` を
  `tools/pegasus/dispatch_compute.py --task generic` から起動する形**で満たす (レンズ A A9: A-5 改修は不要で、
  A-5 は `--screening` を持たず finalize が 8 genome を要求し submitter が 2 workload 固定)。README は
  「既存 A-5 投入 script を使用した」と書かず「既存 generic dispatcher から現行 screening CLI を実行した」と書く。
- **親の不変条件「投入中の worktree へ output/ 配下以外を書かない」は取り下げる。** これは A-5 型 job の
  `source_identity` 検査に由来する親の provisional であり、ユーザー裁定ではない。CLI が投入元 submodule へ
  `patchharness.applied` (pinned-clean 検査 → `git apply` → revert) を行い、stock checkout を一時 worktree として
  登録・撤去するのは **CLI の正規挙動**であり、独立 clone で隔離する (前回 probe / A-5 の形) のは launcher を
  100 行超に膨らませ clone 所要と失敗面を増やす。置き換える不変条件は次の 3 つ:
  (i) 投入から終了まで親は wave worktree に対して git 操作・test 実走・編集を一切行わない (worktree は lock 済み)、
  (ii) launcher は起動前に worktree HEAD = `1042a1bc9`・submodule HEAD = `511c9538…`・両者の tracked-clean を検査し、
  CLI 終了後に両者の `git status --porcelain --untracked-files=no` と submodule の `worktree list` を stdout に出す、
  (iii) 終了後に親が同じ検査を login で再実測し、dirty なら復旧 (`git -C external/ccbench checkout -- .`、`worktree prune`) を記録する。
- **launcher は job dir の bash script 1 本 (≤ 130 行)。Codex `role=author` が書く (D95、凍結境界)。** repo へは
  実行体として置かず (D1786)、証拠として `.txt` の写しだけを insight に入れる。launcher の責務は
  (a) 前提検査、(b) 単独性の観測と拒否 (裁定 2)、(c) A-5 と同じ env 供給、(d) 正規 CLI を 1 回だけ起動、
  (e) 終了後の tree 状態の出力、に限る。clone・build・関門への介入・監視機構の追加は禁止。
- 子 interpreter は `python3.10` を候補 (`python3.10` / `/usr/bin/python3.10` / `/bin/python3.10`) から実在検査して
  realpath を記録 (段 2 と probe PBS の形)。PATH は A-5 と同じ固定値。`-I -B` を維持。

## 裁定 2 — 単独性の確認は「割当ノード上・CLI 起動前」で行い、観測を stdout に残す

- batch では割当前の確認は不可能 (runbook §1/§7)。依頼の「単独性を確認してから投入」は「同じ job 内で、CLI 起動前に
  割当ノードを観測し、競合があれば計測を開始しない」で満たす (レンズ A)。
- 観測 (stdout へ): hostname、`/proc/loadavg`、`nproc`、`ps -eo user,pid,pcpu,pmem,etime,comm --sort=-pcpu` 上位 25 行、
  `pgrep -af 'ycsb_.*\.exe'`、他ユーザー (`$USER` と root 以外) の process 一覧。
- 拒否 (rc=3、CLI 未起動): (1) `ycsb_.*\.exe` が 1 件でもある (production の一次ゲート F3 と同じ述語、到達可能な正例 = 0 件)、
  (2) 他ユーザーの process に `%CPU >= 50` がある (別 job の同居)。load average は DW-O13 (実測分布なし) により
  拒否条件にせず記録のみ。拒否は「本題未実行」なので再投入を許す (裁定 4)。

## 裁定 3 — (P2) 緑の定義と README の限定 (レンズ B の 6 点 + 主張表を採用)

「screening 関門が緑になった」と名乗る条件 (すべて満たす):
1. 未使用 official root と今回の dispatch request が対応する。
2. `campaign.lock` が `write-heavy`・`screening_fixed_us=2`・実行契約を示す。
3. baseline の `build-start.payload.genome` が `BACK_OFF=0, BACKOFF_FIXED=-1`。
4. 同じ variant・同じ `build_attempt_id` に新規 `bench-done` と後続 `commit` があり、`build-done` (toolchain / binary hash / argv) も保存。
5. dispatch `result.stage=child`・`child_rc=0`、receipt `outcome.kind=child`・`rc=0`・会計照合済み。
6. stdout の campaign ID・結果と WAL が一致し、production 4 file + dispatcher + launcher の sha256 を記録。

限定 (README に必ず書く): arm record は未保存 (間接証拠)、baseline meaning は `unestablished/meaning-witness-undeclared`
(declaration は非負値のみ)、成功 reason (`identical` / `root-location-only`) は識別不能、rc=0 は候補の
`screen-slower-than-floor` と両立、1 workload・2 genome・1 走、A-5 と等価でない (依存 binary・実行証跡)、
全点 family・他 driver・将来 HEAD・adaptive の実行時動作を保証しない。候補段で赤でも baseline の関門通過は否定しないが
「CLI 全体正常終了」の完了条件は未達とする。

## 裁定 4 — 「本題の 1 走」の解釈 (レンズ A の表を採用)

| 状況 | 扱い |
|---|---|
| 投入前失敗・launcher の拒否 (rc=3)・未開始と証明された queue timeout | 本題未実行。記録して原因解消後に投入してよい |
| rc=16 で child の実行有無が不明 | 再投入しない。receipt / result / stdout / WAL を先に照合 |
| CLI 起動後の proxy 不通・prepare 失敗・link 失敗・関門赤 | 今回の赤として終了。直すなら Codex author、緑が出るまで再投入しない |
| bench/commit 後の会計・log・receipt 障害 | 証拠回収。再測定で置き換えない |

## 裁定 5 — brief の訂正

- 前提 4: prefix の永続記録は `completion.json` の `preimage.dependency_prefix` (build identity に入る)。
  `compiler_input_dependency_prefix_roots` は本経路で空。
- 前提 7: 「関門は無条件に走る」→「今回の baseline は request 非空 (`BACKOFF_FIXED=-1`、stock 比較) かつ `force=True` なので
  関門を経る」。候補には terminal skip がある。
- 前提 8: pgrep は競合 bench の不在しか示さない。00:33 の queue 数は投入時の観測値に過ぎない。
- P5: prepare 3 回 (driver・baseline・候補)、完全 build 4 回 (trace/perf × 2 genome)、通常 10〜30 分、walltime 90 分は予算。
  overall timeout = `submitted_at + 5400 + 3600`、RUN 観測後に再設定。
- 研究前進の「sweep driver で新規測定を再開できる」→「最小 screening 経路の生死確認。全点 family は別」。
  「screening が赤のまま」→「最後に観測した screening は赤 (2026-09-07)、供給実装後は未測定」。
- 成果物に `completion.json`・`build-done` payload・launcher bytes (`.txt`)・実行 python realpath・lock path を加える。

## 変異 matrix

実装面 (repo) の差分ゼロにつき免除 (DW-S04)。launcher は repo 外の一回限りの投入 script で、敵対レビュー
(段 6 相当の静的レビュー 1 本を launcher に対して行う) だけを守りとする (D1786 の「残る限界」)。受入全走は免除しない。

## 段 5 の子

- author 1 本 (`sandbox=workspace-write`、`--reasoning` なし、`--max-attempts 1`): launcher を
  `output/insights/2026-09-17/t2228-screening-gate-liveness/launcher/run_screening_liveness.sh` に書く。親が job dir へ移し、
  投入後に `.txt` で insight へ戻す。
- 段 6: launcher への静的レビュー 1 本 (read-only)。must-fix があれば fix 子。
