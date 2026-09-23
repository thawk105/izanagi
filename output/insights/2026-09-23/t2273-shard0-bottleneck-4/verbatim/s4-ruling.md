# 段 4 裁定 — [T-2273] [T-2560] 受入 shard-0 律速の再同定 (第 4 回)

裁定時刻: 2026-09-23 (段 3 相談 `codex/s3-consult-out.md` 受領後)。as-of = 2026-09-23T07:42:52+09:00 (startup-gate.log)。裁定 inbox の wave 開始後の新着なし (第 31 回 4 は D2219 項 4 と同文)。

## 1. 所見の裁定 (7 件とも real・採用・scope 内)

- C1 (P1 の混同): real。T-2786 §4 が「5 本同時の copy は 30〜35 秒、伸びは開始時間帯の他 unit との干渉」を既に示している。P1 を撤回し「copy 複合区間は開始時間帯と共存処理に依存して伸びる (干渉の正体は未同定)」へ戻す。issue 一定は T-2786 の 11 走 44 key と T-2817 の 1 走の観測事実としてだけ書く。
- C2 (copy 計器が複合): real。copy span を「git 可視列挙 (`_run_git_bytes` 呼出し) / 実 copytree / その他」に分け、span ごとに CPU 時間 (self + children) を取り、1 Hz の資源標本 (CPU・iowait・run queue・Lustre client op・TMPDIR の disk) を並べる。
- C3 (P2 と対象 worker): real。P2 を撤回。主対象は各 R 走の**最大占有 worker とその依存 builder** とし、L の worker は併記する。効果見込みには短縮後に最大となる worker を含める。
- C4 (Job C): real。Job C を削除。一手の効果は R1 の後、受入と同じ 48 worker 条件の対照 1 本で測る (§3)。
- C5 (過去 A): real。A は再走しない。「過去 A の 189.98〜208.09 秒の原因は未同定。R1 の現行観測と整合するかまでを書く」と事前登録する。
- C6 (3 本同時): real。R1 を 1 本だけ先に走らせる。以降は逐次。
- C7 (TMPDIR・費用): real。probe runner は TMPDIR を上書きせず dispatch 環境から継承し (実受入と同じ)、その path と filesystem 種別を記録する。smoke は残すが実行したことと所要を記録する。費用は R1 実測後に再見積りする。

## 2. plan v2

- 段 5: Codex author 1 単位が T-2817 の replica probe 3 file (repo 外 `dev-wave-t2817-acceptance-bottleneck-3/probe/`) を出発点に、`tools/t2273_replica_runner.py` / `tools/t2273_replica_plugin.py` / `tools/t2273_replica_analyze.py` を書く (子 worktree で書き、親が job dir の `probe/` へ退避、repo には逐語 .md のみ)。
- Job R1 (1 本、計算ノード generic、walltime 00:50:00): 現行 tip の受入 shard-0 replica 1 走 + 観測。
- R1 後に段 4 追補で「対照 1 本」の形を決める (§3)。

## 3. 事前登録 (R1 を見る前に固定)

1. **律速の定義:** R1 の W_0 = O_max + F。O_max の worker の item 列を、各 item について「flock 待ち (= 依存 builder の残り構築) / 自分の構築 (copy 列挙・copytree・git・issue・その他) / base→test copytree / verify / 残り」に排他分解する。**最大の成分を律速と呼ぶ。** L の worker も同じ分解を併記する。
2. **干渉の読み方:** builder の copy 下位区間ごとに、同区間の資源標本 (CPU 使用率・iowait・run queue・Lustre op/秒) と CPU 時間/壁時間比を出す。CPU 時間/壁時間 ≥ 0.8 なら「CPU 実行が支配」、≤ 0.3 なら「待ち (IO・metadata・run queue) が支配」、間は「混在」と書く。原因の断定はしない。
3. **次の一手の選び方:** 律速成分のうち、D2068 の却下 3 案と受理集合の変更に触れずに縮めうる部分を候補とし、候補ごとに R1 の実測値から「影響を受ける worker・短縮後に最大となる worker」を書く (これは換算であり上下限ではない)。**一手を 1 つに絞り、その効果を受入と同じ 48 worker 条件の対照 1 本 (R2) で測る。** 対照は probe 内の観測 wrapper / 順序の外側で作れる形に限り、production・test・台帳を変えない。対照の形が probe 内で作れなければ、一手は「効果未測の候補」として書き、診断は律速同定までとする (完了扱いの語を分ける)。
4. **過去 A:** 再走しない。原因は未同定と書き、R1 と整合するかだけを書く。
5. **R1 の有効性:** rc 0 ∧ 受入 shard-0 と同 argv ∧ clean HEAD ∧ others=0 ∧ record-error 0 ∧ 最大占有 worker と W_0 が T-2825 B の範囲 (W_0 310〜345 秒) から大きく外れる (±30 % 超) 場合は外れと明記して読む (無効にはしない)。

## 4. 変異・受入

実装面の差分ゼロ (probe は repo 外) なので変異 matrix は免除 (DW-S04)。受入全走は記録前に 1 回。

## 追補 1 — R1 の読み (§3 を適用) と R2 の事前登録 (R2 を見る前に固定)

R1: request 18929.nqsv、bnode030、Elapse 514 秒、HEAD 3886a1fd3、clean、others=0、TMPDIR=/tmp (継承なし、local nvme xfs)、smoke rc0 66.8 秒、A rc0。集計 `analysis/r1.{md,json}` (analyzer rc=1 は Lustre llite stats 読取り不可による資源欠測だけ。mdc md_stats は取れている)。

- W_0 429.4、pre 130.2、O_max 289.0 (gw2)、L 272.1 (gw40、failed_launch)、post 10.07。§3.5 により **外れ (W が T-2825 B の範囲を 25〜38 % 超、pre が通常 62〜64 の約 2 倍) と明記して読む**。pre 倍増の原因は未分解。
- §3.1 律速: gw2 の最大成分 = flock 待ち 206.5 秒 (item rank 96 `delegated_campaign_start_rechecks_receipt[missing]` 261.7 秒 = 待ち 206.5 + base→test copytree 14.5 + verify 0.7 + 残り 40.0。後続 22.7 + 4.7)。gw40 も待ち 206.5 + 14.6 + 6.1 + 44.8。待ち先 = active_v2 key の builder (gw14) 206.5 = copy 113.4 + git 13.5 + issue 79.6。**7 key の builder が全部 t≈130 (JUnit 基準) に同時開始し、全部 206〜207 秒 (非発行 key 126.9)。**
- §3.2: builder の実 copytree (Lustre の `output/` 可視 29,885 path → /tmp) は 7 本とも 153〜243 秒の 90.1 秒、self CPU/壁 0.11 → **待ちが支配**。区間の node CPU 使用率 0.24、iowait 0.002、run queue 13、mdc close 7,362/秒。issue は children 込み 1.0 → CPU 実行が支配 (node CPU 0.37)。git は children 込み 0.99 → CPU 実行が支配。
- §3.3 候補: 律速成分のうち最大は copy (113.4、うち copytree 90.1 が待ち支配)。T-2786 の collection 中 5 本同時 copy 30〜35 秒との差 (約 80 秒) が縮めうる部分の換算 (上下限ではない)。issue 79.6 は CPU 支配で並行度に依らない (T-2786) が、縮めるには production の発行処理の変更が要り、probe 内で対照を作れない。**一手 = 「可視 output の複製元を計算ノード局所へ置く (Lustre からの 7 本同時の小 file 読みを除く)」を選び、R2 で効果を測る。** D2068 の (A) whitelist・(B) alternates・(C) 独立 index には触れない (複製する集合・object store・index は不変)。
- §3.4 過去 A: R1 では全 key が同時開始で、t≈55 秒開始の条件は観測していない。「A の 189.98〜208.09 秒は、builder が他 key の同時構築・開始直後の test 群と重ならなかったこと (T-2817 Job B の copy 64.2 / 33.0) と整合する」までを書き、原因は未同定のままとする。

### R2 の事前登録

- 形: 計算ノード 1 job・同一 node で smoke → **A2 (R1 と同一の観測のみ)** → staging → **X (複製元を局所 snapshot に差し替えた対照)** の順に 1 対。A2 を先にするのは X の staging が Lustre client cache を温めて A2 を有利にしないため (X 側が後走の warm を受ける偏りは限界として書く)。
- staging: runner が A2 の後に、実 repo から node-local (`$TMPDIR` 配下) へ `output/` の tracked file を持つ git repo を作る (実 repo の shared admin に worktree を登録しない、実 repo へ書かない)。staging の壁時間と file 数を記録する。
- X の差し替え: plugin が `_copy_git_visible_output(source_root, destination)` を、source_root が実 repo root のときだけ staged root に置き換えて**実関数を呼ぶ** (列挙・ignore・copytree の実装はそのまま)。それ以外の挙動・受理集合・順序は変えない。これは対照用の差し替えで、観測 wrapper ではないことを記録に明記する。
- 有効性: A2 と X の両方で rc 0、全 test の outcome 集合一致、可視 path 集合の digest と件数が A2 と X で一致 (不一致なら X は無効)、clean、others=0、record-error 0。
- 判定量: ΔW_0 = W_0(A2) − W_0(X)、ΔO_max、Δ(依存 builder の構築)、Δcopy、ΔL と、X での最大占有 worker と律速成分。**「効果の見込み」= ΔW_0 (1 対の観測、有意差判定ではない、D357 の 1 走比較として 10 % 未満は「変化なし」)。** staging の壁時間は別欄に書き、実装時の費用の目安とする (差し引いた値も併記)。
- 次の一手の採否: ΔW_0 ≥ 10 % かつ X の builder copy が A2 より短い → 「複製元の局所化」を次の一手として提示。そうでなければ「効果を確認できなかった」と書き、R1 の次点 (issue 79.6 秒、CPU 支配) を効果未測の候補として書く。
- 費用: R1 の Elapse 514 秒から、R2 ≈ smoke 67 + A2 431 + staging (上限 300 と仮定) + X 431 ≈ 1,230 秒 ≈ 0.34 node 時間。wave 合計 ≈ R1 0.14 + R2 0.34 + 受入 0.25 ≈ 0.73 node 時間 < 2。walltime 00:50:00。

## 追補 2 — R2 系の分類と R2'' の読み (追補 1 の事前登録を変えずに適用)

- R2 (19029.nqsv、bnode025): A2 有効。X は計算ノード /tmp のユーザー quota 超過 (`Errno 122`) で test の一時 dir が作れず無効 = **infra (probe の staged repo の置き場と前走の残骸)**。X の値は判定に使わない。fix1 (staged repo を node scratch `/scr` へ、各走前に job が作った /tmp の残骸だけを掃除、quota 記録) を Codex author に書かせた。事前登録の形・判定量・採否基準は変えていない。
- R2' (19108.nqsv、bnode005): smoke 後の clean 検査で停止。原因は**親が走行中に wave 木へ insight 下書きを書いたこと** (検査は正しく働いた)。あわせて `/scr/<user>` 不在で X を止める作りと判明し、fix2 (`/scr` が node-local で書けるなら `/scr/<user>` を作る) を書かせた。
- R2'' (19131.nqsv、bnode081、Elapse 1,046 秒): 有効性の全項目が真。ΔW_0 = 123.9 秒 (27.3 %)、X の builder copy は 7 key とも短い → **採否基準を満たす。次の一手 = 可視 output 複製元の局所化を提示**。staging 43.9 秒は別欄 (差し引き 80.0 秒)。X の最大占有 worker は gw2 のまま、最大成分は flock 待ち 104.6 秒 (builder = copy 11.1 + git 13.8 + 発行 79.3)。
- 費用の実績: R1 514 + R2 954 + R2' 84 + R2'' 1,046 = 2,598 秒 ≈ 0.72 node 時間 (受入を除く)。
