# 段 4 裁定 — [T-866]+[T-867] slice 2 (wave: dev-wave-t810-harness, 2026-08-12)

段 2 プラン (s2-plan.md) に対する段 3 レンズ A (16 所見)・レンズ B (13 所見) を親が独立に裁定した。
判定は両レンズとも NO-GO。**プランの骨格 (共有 schema 先行・新規 t810_* module 群・既存変更は
registry 1 行) は維持し、下記の plan v2 差分を適用して実装へ進む。**

## 1. 所見の裁定 (real/refuted・採否)

| # | 出所 | 裁定 | 採否と処置 |
|---|---|---|---|
| 1 | A-1 相互 digest 構成不能 | **real** | 採用。`t810-launch-intent/v1` を最初に確定し、guard/budget receipt は intent digest を、最終 manifest は両 receipt の digest を束縛する片方向 DAG にする |
| 2 | A-2 release token 偽造 | **real** | 採用。manifest に release-token commitment (sha256(nonce)) を凍結。coordinator は ack の `release_marker_sha256` を自分の発行 marker と exact 照合。同一 UID 書込みは排除不能 → 新 policy の limitations に宣言 ([T-868] 連動) |
| 3 | A-3 seal の import 迂回 | **real** | 部分採用。effect を持つ全経路 (scheduler adapter・qdel・benchmark exec) の**入口ごと**に `run_authorized` を再検査する。in-process Python caller の内部関数直呼びは能力遮断でない → limitations に宣言。「effect adapter を置かない」案は不採用 — (c) の実 mediation 点が (b) と同一 wave という確定裁定に反する |
| 4 | A-4 (d2) 非構造 | **real** | 採用 + 裁定へ。検査型 (d2) (package repo-free・全 root repo 外・`.git` ancestor 拒否・PBS workdir 検査) を実装し、**共有 mount 上の repo 到達性は検査で消えない**事実を limitations に宣言。namespace 隔離を要するかは裁定パッケージ 5 |
| 5 | A-5 開始ばらつきが実開始を拘束しない | **real** | 採用。**start-permit 相を廃止** (プランの発明で protocol に無い)。ack = 測定開始応答とし、wrapper は cancel 再確認 → ack 書込み → 即測定開始。spread = max(ack 受領) − release 発行 (coordinator 単一時計、per-job latency も記録)。>5s は attempt を `post_release_pre_measurement_invalid` に倒す (測定は走ってよい、結果は捨てる)。これは疑義 2 (max−release vs max−min) の裁定でもある: protocol :186-190 の逐語は release→受領の差であり max−release を採る |
| 6 | A-6 / B-6 予算台帳リセット | **real** | 採用。policy に `budget.status` を置き **`unratified` の間 admission は常時 deny**。数値 (総枠・見積り・genesis) はユーザー裁定後に ratify。ledger は genesis record の digest を policy に束縛し、chain 不一致・欠落は deny。trust root 不在の残余は limitations ([T-868]) |
| 7 | A-7 / B-11 mediation 注入 | **real** | 採用。production `run_allowed_measurement()` は固定 subprocess runner + 入口 seal 検査。fixture seam は内部関数のみ。統合 tripwire test で wrapper/coordinator/guard module に policy module 外の subprocess 使用が無いことを AST 検査 |
| 8 | A-8 guard TOCTOU | **real** | 部分採用。snapshot→release 間の原子性は単側では構成不能。release 直前再 snapshot を実装し、残余 race を limitations に宣言。A/B 共通 lease は裁定パッケージ 1 |
| 9 | A-9 検査 phase の前倒し | **real** | 採用。状態は (境界, reason) の凍結表で決める。wrapper 自己 preflight の赤 = state 1 (ready 不成立)。release 後の再検証不一致 (依存 manifest・module list・trace・NUMA) = state 2。reason code ごとの許容 phase を exact 検証 |
| 10 | A-10 terminal_reduced 潰れ | **real** | 採用。state 3 は「完了 ≤ N−2、または完了 job 自身の欠損/integrity 違反」に限定。state 4 は脱落 1 job を整合性評価から除外 (protocol :356-357 の逐語どおり) |
| 11 | A-11 retry ordinal | **real** | 採用。`attempt_ordinal ∈ {1,2}` exact、`retry_allowed = (state==pre_release_invalid) AND (ordinal==1)` |
| 12 | A-12 / B-2 自己申告 boolean | **real** | 採用。coordinator は wrapper の `passed` を信じず raw evidence (quiet_samples 数値・hostname 等価・hash 等価) から再計算する。`approved_hostnames` は admission policy の ratifiable field (unratified → deny)。`prereg_approval_id` は caller 文字列でなく loader の ApprovalReceipt から取る (未承認なら manifest 生成不能) |
| 13 | A-13 他 UID の競合 process | **real** | 採用。可視の全 process を対象、affinity/UID を読めない対象は fail-closed 拒否、測定直前に再走査 |
| 14 | A-14 凍結 presence matrix 未結線 | **real** | 採用。子 A は prereg `artifacts`/`terminal` の期待ファイル集合へ exact に直列化する表を実装前に確定し、control marker は work_root (output exact set 外)。validator への入力 projection を定義 |
| 15 | A-15 限界宣言と完了主張 | **real** | 採用。slice 1 validator は不変更のまま。新 module 群は admission policy の `limitations` に自らの能力限界を機械可読で宣言し、「§9.1 充足」を主張する出力を作らない |
| 16 | A-16 brief の過一般化 | **real** | 採用。素材は「字句/設計 pattern」に格下げ、`qsub_argv`/`build_argv` は prereg 上 **unfrozen_procedures** であることを実装前提に明記 (brief の該当行はこの裁定で訂正されたものとして扱う) |
| 17 | B-1 qsub 凍結値不在 | **real** | 採用。project/queue/run kind 別 walltime を admission policy の ratifiable field に置く。unratified → canonical qsub argv を生成不能 (deny)。prereg bytes は不変更 |
| 18 | B-3 T-139 識別 | **real** | 採用 (プランどおり)。`unresolved` → 常時 deny。規約確定は裁定パッケージ 1 |
| 19 | B-4 logical/PBS ID 境界 | **real** | 採用。二 field を明示分離。§3.3 item 1「全 request ID を先に書き出す」は「全 N 件の PBS ID を束縛した submission receipt が ready barrier 評価より前に完成していること」で充足すると解釈 (親裁定。裁定パッケージ 4 で確認に出す) |
| 20 | B-5 qstat -f / -Q 混同 | **real** | 採用。`qstat -f <id>` と `qstat -Q` を別 transcript schema・別 parser に固定 |
| 21 | B-7 見積りと N の束縛 | **real** | 採用。`jobs_per_attempt == len(slots) == prereg node_count` を run kind ごとに cross-check |
| 22 | B-8 予約 race/idempotency | **real** | 採用。flock 内 read→validate→check→append、`(group_id, run_kind, attempt)` 一意、finalize replay 拒否 |
| 23 | B-9 精算表不在 | **real** | 採用。遷移表を固定: scheduler 到達不明 = `consumed` (保守側)、投入前中止 = `released`、qdel 確認済み取り消し (開始前) = `released`、未使用 retry 枠は witness つき finalize で一度だけ `released` |
| 24 | B-10 nested exact / 重複 key | **real** | 採用。raw parse は duplicate-key 拒否 (object_pairs_hook)、全 nested schema の exact field 表、unknown/missing 双方向 fixture |
| 25 | B-11 本番経路未検査 | **real** | 採用 (7 と併合)。テストは (i) dormant 経路 (CLI が seal で停止) と (ii) authorized 経路 (テスト発行 receipt + fake scheduler を内部 seam へ注入し、guard→budget→manifest→barrier の production orchestration を通す) の両方を持つ |
| 26 | B-12 所有の素集合性 | **real** | 採用。共有単位 S (schema + transcript fixture) を**単独の先行実装子**に割り当てて凍結し、A/B/C は S 完了後に並列。fixture は子別ファイルに分割 |
| 27 | B-13 変異帰属 | **real** | 採用。変異走は authorized fixture 経由で各 gate を単独 load-bearing にする。事前登録は §3 |

refuted: なし。両レンズの全所見を real と裁定した。

## 2. plan v2 差分 (s2-plan.md への上書き指示)

1. artifact DAG: `launch-intent/v1` (group 構成・slot 計画・policy digest) → guard receipt / budget
   receipt (intent digest 束縛) → `group-manifest/v1` (両 receipt digest + release-token commitment を
   束縛、create-only) → submission receipt (PBS ID 束縛、**ready barrier 評価前に完成必須**) →
   release marker (nonce は commitment の preimage) → ack (release marker sha 照合) → terminal。
2. start-permit 相は作らない。ack = 測定開始応答。wrapper は cancel 再確認 → ack → 即測定。
3. 状態分類は (境界, reason) の凍結表。ordinal ∈ {1,2}。state 3/4 の条件は裁定 10。
4. admission policy `t810_admission_v1.json` に追加: `qsub` (project/queue/walltime、ratifiable)、
   `approved_hostnames` (ratifiable)、`budget.status`/`genesis_sha256`、`limitations`。
   **unratified な値に依存する判定はすべて deny。**
5. coordinator は raw evidence から全 gate を再計算。effect 入口ごとに seal 再検査。
6. 実装順: 子 S (schema+fixtures、単独先行) → 子 A / 子 B / 子 C 並列 → 親統合。
7. 規模上限: 子 S ≤900 行、子 A ≤1400 行、子 B ≤1900 行、子 C ≤1900 行 (test 込み、超過は分割相談)。

## 3. 変異事前登録 (DW-M01。実装後に単一理由性をコードで確認して spec 化、確認不能は再照準)

| # | 位置 | 変異 | 期待 |
|---:|---|---|---|
| M1 | barrier | hostname 異なり数検査を除去 (重複許容) | 重複 host fixture の test が KILLED |
| M2 | barrier | binary copy hash 不一致を許容 | copy 改竄 fixture が KILLED |
| M3 | spread gate | >5s を valid のまま通す | 5s+1ns 境界 test が KILLED |
| M4 | wrapper | 測定直前の cancel 再確認を除去 | release 後 cancel fixture が KILLED |
| M5 | verifier | 完了 12 件を `valid` と判定 | 状態表 test が KILLED |
| M6 | verifier | 完了 12 件+完了側欠損を `terminal_reduced` と判定 | 欠損 fixture が KILLED |
| M7 | retry | state 2 からの retry を許可 | retry 表 test が KILLED |
| M8 | retry | ordinal 2 の再投入を許可 | ordinal 境界 test が KILLED |
| M9 | quiet gate | 3 連続を 1 回に緩和 | 非連続 fixture が KILLED |
| M10 | argv 照合 | exact を部分集合一致に緩和 | 追加引数 fixture が KILLED |
| M11 | runner policy | allowlist を prefix 一致に緩和 | 変形 argv fixture が KILLED |
| M12 | runner policy | 実行入口の seal 再検査を除去 | 未承認実行 test が KILLED |
| M13 | (d2) | `.git` ancestor 検査を除去 | repo 実在 fixture が KILLED |
| M14 | guard | 未知 job_state を無害と分類 | 未知 state deny test が KILLED |
| M15 | guard | identity `unresolved` でも許可 | unresolved deny test が KILLED |
| M16 | budget | `status: unratified` を ratified と同扱い | unratified deny test が KILLED |
| M17 | budget | ledger genesis 照合を除去 | 別 ledger fixture が KILLED |
| M18 | 正例 | 正規 authorized transcript + 正規 group | **SURVIVED** (過剰拒否なしの正例) |

## 4. ユーザーへ返す裁定パッケージ候補 (実装は上記 fail-closed 既定で先行)

1. T-139 pilot/本走の anchored `Job_Name` 規約と所有者、および A/B 共通 priority lease の要否。
2. 予算の承認値: `total_node_seconds`、builder/liveness/main の walltime・jobs、ledger genesis。
3. qsub の承認値: project / queue / run kind 別 walltime (policy ratification の形)。
4. §3.3「request ID」解釈の確認 (裁定 19 の親解釈でよいか)。
5. (d2) の充足形 — 検査型 + limitations 宣言で §9.1 を満たすか、namespace 隔離を要するか。
6. approved hostnames の権威の置き場所。
7. prereg の unfrozen_procedures (qsub/build) を補助 policy 承認で閉じる方式の可否
   (slice 1 の裁定パッケージ「§9.1 item 2 列挙訂正」と連動)。
