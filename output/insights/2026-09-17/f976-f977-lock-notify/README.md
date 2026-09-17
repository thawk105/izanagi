# F976 / F977 — 実 repo ロックの writer 優先 gate と land 巻き戻し通知 kind (D2104 項 33 / 34)

authority: none / default_effect: no-state-change (プロセス監査・逐語凍結。可変状態の正本は worklog 末尾と現行 phase doc)

- wave branch: `worktree-dev-wave-f976-f977-lock-notify`
- 基準 commit: `b4631a92e` (local main、wave 開始時に ff-only で取り込んだ。裁定 fragment の land を含む)
- docs commit: `b869861a5` (親、入口 項 9 +12 bytes・runbook・tests README)
- 実装 commit: `df2da88ee` (Codex `role=author` ×2 + 親の docs / integrator、7 file、+709/−49)
- 裁定: D2104 項 33 (writer 飢餓は局所修正で防ぐ) / 項 34 (巻き戻しは維持し通知を既存経路で足す)
- 一次資料: F976 / F977 (`docs/failures.md`)、D1594 / D1618 (read/write lock 設計)
- 設計判断: 本 wave の decisions fragment (slug `real-repo-writer-gate-and-rolled-back-notice`、D 番号は land の fold が付ける)
- job dir (prompt・log・patch・変異 sidecar の原本): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-f976-f977-lock-notify/`

## 何をしたか

**(1) writer 優先 gate (`orchestrator/tests/conftest.py`)。** 実 repo ロックは 1 file の `LOCK_SH` / `LOCK_EX` を
`LOCK_NB` で polling する形で、別 process の reader が途切れず重なると writer が 245 秒の deadline まで取れなかった
(F976、受入 44 走中 7 走、2026-09-16 再発)。各 key (legacy / common) に同名の `.gate` flock を足し、
writer は fresh の EX 取得と SH→EX の昇格の両方で gate を EX 保持したまま main を待ち、main 取得直後に gate を閉じる。
昇格は gate を開いてから自分の SH を `LOCK_UN` で明示解放する。process が実 repo lock を 1 つも持たない fresh reader
は、main を取る前に要求する全 key の gate を SH で試して即解放し、writer が gate を保持する間はそこで (何も持たずに)
待つ。既に lock を持つ process の reader と降格は gate を見ない。deadline 245 秒は gate と main で共有し、fork 後の
reset は gate fd も閉じる。定数・SH-EX の意味論・key の順序は不変。

**(2) 巻き戻し通知 kind (`tools/wave_land_window.py`)。** fold 失敗で land の merge 前まで main を戻す契約
(`_rollback_fold`、`rollback_ref=locked_main`) は維持し、`message --kind rolled-back` を足した。受理述語は
`status == "fold-failed"` ∧ `main_after` が SHA ∧ `wave_tip` が SHA ∧ `main_after != wave_tip`。固定文 2 行 (661 bytes)。
送信義務は runbook の land 手順と command 入口 項 9 (「land 成功時と巻戻し時に」、exact pin を checker と fixture に揃えた)。

## 段 1 brief から段 4 裁定までに覆った前提

- **plan v1 の「昇格は gate を通さない」は F976 の一方の経路を直さない** (親の追加検算)。F976 の当該 node
  (`test_repository_candidate_uses_real_s8c_budget_module`) の writer は `repository_candidate_commit` fixture の
  parent EX で、同 module の module 寿命 SH fixture (`current_commit_snapshot`) が生きた worker では既存 fd 上の昇格になる。
  裁定で昇格も gate を通す形に変えた。
- **段 3 レンズ A の三者循環は real。** plan v1 では reader が legacy main を握ったまま common gate で待つため、
  入れ子昇格 + 別 worktree の writer と `A → B → W → A` の循環を新しく作る。裁定で「reader は何も持たないときだけ
  gate を見る」に変え、gate 辺を通る循環が現行の main 間 hold-and-wait と同じ族に閉じるようにした。
  段 6 レビュー A が v2 で同反例が消えたことを wait-for graph で確認した (refuted)。
- **brief の P3 (`main_before == main_after`) は recovery 経路の本物の巻き戻しを拒否する** (段 3 レンズ A の経路表:
  shape A は before = wave tip、after = rollback_ref)。裁定で条件を落とした。
- **brief の P1「process 内層は不要」は `condition.wait` が RLock を手放す経路には成り立たない** (両レンズ)。
  「kernel flock 待ち中は RLock が新規進入を止める、xdist worker は単 thread」に限定し、process 内層は変えない。
- **brief の「DW-O23 は L2 1,000 bytes で満杯」は誤り** (レンズ B: DW-O23 は段 9 の無条件参照で L1、1,036 bytes)。
  触らない理由を「通知手順は runbook に集約する」へ訂正した。
- **レンズ B が `test_check_docs.py:2524` の `== 9_507` pin を見つけた** (brief と plan の見落とし)。author (2) が 9_519 へ更新。
- **author に docs を持たせる plan の所有割当は実装子契約に反する** (レンズ B)。親が docs を先に commit し、
  author worktree を ff してから投入した。

## 段 6 レビューと fix

- レビュー A (正しさ境界): must-fix 1 = 昇格時に `LOCK_UN` が gate open より先で、open 拒否 (owner / mode 検査) で
  外側 reader の SH を失う新しい経路。レビュー B (検出力・帰属): 同 must-fix + P2 の「実時間 2 秒未満」assert
  (高負荷で偽赤)。nit 3 (README 文言、`_gate_actor` の pipe close、`with` 行の空白)。
- fix 子: gate open → UN → gate EX → main EX の順へ入替え、負例 `test_real_repo_gate_open_rejection_preserves_outer_reader
  [legacy|common]` を追加 (旧順序で `DID NOT RAISE BlockingIOError` の赤を確認)、P2 の実時間 assert を除去し
  watchdog 30 秒へ。再レビュー 1 本 = GO (README nit 1 は親が段 7 で反映)。

## 親の実走 (計算ノード dispatch)

- 焦点走 f1 (統合前、10 file: serialization / wave_land_window / check_docs / dev_wave_wait / dev_wave_land /
  resume_gate / s8c predicates / s8c invariant / campaign_import / run_tests_shards): **1945 passed / 16 skipped
  (growth hold 15 + flaky hold 1) / rc=0 / 101 秒** (request 2843.nqsv)。F976 の当該 node (実 repo の parent EX fixture)
  を含む real-repo node が実走して緑。`test_protocol_builder_repo_tree_guard_is_wired_to_real_root` は growth hold
  (ユーザー明示解除専用) で skip。
- 焦点走 f2 (fix 統合後、7 file): **1544 passed / 10 skipped / rc=0 / 99 秒** (request 2923.nqsv)。
- 受入全走: **child-green、24541 passed / 67 skipped / rc=0** (attempt 2、tested main `48e3ff9e5`、
  tested tip `be21eb0b5` = 統合 commit + wrapper の post-claim merge 2 回、receipt `acceptance-receipt-2.json`、
  `red_nodeids` / `flake_nodeids` とも空)。attempt 1 は post-claim merge (main `9ce3a59` → wave `f99a9642d`) の直後に
  main が進み `postcheck` rc=70 で無走行 (merge は実装面 6 file を変えていない)。投入は門番 (他 session の受入 leader
  ≤ 3 かつ `/proc/loadavg` の 1 分 < 5 分) 経由。

## 変異 matrix (container worktree `.codex/worktrees/f976-f977-mutcontainer`、commit df2da88ee)

spec `mutation-spec-final.json` (sha256 `45285d80…`、12 件、`timeout_seconds` 2700)、ledger `mutation-ledger-final.json`。
runner = `python3 tools/run_tests.py test_real_repo_serialization.py test_wave_land_window.py test_p3_s4_loop.py -q -rf --force-dispatch`
(計算ノード dispatch、`--detached`)。probe 走 (`mutation-spec-probe.json`、全件 SURVIVED 登録) で観測 node の完全集合を
採ってから本走。**本走: baseline PASSED (95.5 秒)、負例 11 件 (M1〜M11) すべて KILLED で期待 node と観測 node が完全一致、
等価 M0 (comment のみ) SURVIVED、MISMATCH 0。** 各変異の所要 84〜96 秒 (M4 のみ 280 秒: deadline の再起算で reader 検査が
実 timeout まで待つ)。

| ID | 変異 (file:anchor) | 殺した node (完全集合) |
|---|---|---|
| M0 | conftest gate 実装の comment 1 行 | 等価、SURVIVED |
| M1 | fresh reader の gate 検査を省く (`if not _REAL_REPO_PROCESS_LOCKS:` → `if False:`) | 7: writer / upgrade-writer drains ×[legacy,common]、gate_open_rejection ×2、share_deadline[reader] |
| M2 | fresh writer が gate を取らない (`and not created`) | 8: writer drains ×2、priority_order 模擬、gate_timeout_closes_fds ×3、fork_reset、share_deadline[writer] |
| M3 | 昇格が gate を通らず現行変換に戻る (`and created`) | 5: upgrade-writer drains ×2、gate_open_rejection ×2、current_snapshot_reader_upgrades (P2) |
| M4 | main 待ちで deadline を再起算 | 2: share_deadline ×[writer,reader] |
| M5 | 失敗経路で gate fd を閉じない (`finally` → `except: raise / else:`) | 2: gate_timeout_closes_fds ×[gate-timeout,main-timeout] |
| M6 | 何か持っていても gate を検査する (`if True:`) | 1: current_snapshot_reader_upgrades (入れ子 reader が第三者 gate で止まる) |
| M7 | `rolled-back` の `main_after == wave_tip` 拒否を外す | 1: rejects_invalid_result[tip-equals-main] |
| M8 | `rolled-back` が `fold-rollback-failed` も受理 | 1: [rollback-incomplete] |
| M9 | `rolled-back` の tip SHA 検査を `is None` に緩める | 5: [tip-invalid, -39, -41, -number, -uppercase] |
| M10 | 巻き戻し用固定文 1 文字変更 | 2: success_is_exact_fixed_text ×[normal,recovery] |
| M11 | `_SUCCESS_STATUSES` に `fold-rollback-failed` を足す | 1: landed rejects…[fold-rollback-failed] |

専属 killer: M6 → P2 の入れ子 reader 検査 1 node、M7 / M8 / M11 → 各 1 node。M1 が gate_open_rejection を殺すのは、
同 test の外側 reader が fresh 取得で gate を検査する経路を含むため。初回 probe (2 file 選択) は F982 を踏み baseline が
`test_real_repo_writers_do_not_materialize_oracle_environment_candidates` で赤 (`mutation-ledger-probe-attempt1-erratum-f982.json`)。

## 残存限界・scope 外 (記録のみ、裁定パッケージは decisions fragment)

- gate は NB polling で待機順を持たない。保証は「writer が gate を保持する間、その gate の事前検査を行う fresh
  reader を待たせる」で、待機開始からの厳密な優先ではない。reader の gate 保持は瞬間なので実効的には retry 間隔の
  数倍で writer が gate を取る。
- 既に lock を持つ process の fresh reader (入れ子・2 つ目の資源) は gate を見ない。
- 昇格の変換失敗 (deadline) 後、外側 reader は SH を失ったまま `mode=read` を信じる (gate 導入前からの穴)。
- gate 検査のために common-dir を main 取得前に解決する (`git rev-parse` の読取)。本体の key は従来どおり
  legacy 取得後に解決する。
- 旧 code の session (gate を知らない) と混在する移行期は、旧 reader に対する飢餓防止は効かない (排他は不変)。
- `rolled-back` は merge 前の失敗 (main 不動) でも通る。文面は両方の場合に真で、巻き戻しの実行履歴は主張しない。
- 変異 probe の初回 baseline は F982 (狭い file 選択で wrapper test が決定的な偽赤) を踏んだ。`test_p3_s4_loop.py` を
  runner 選択へ足して投げ直した。初回 sidecar は job dir `erratum/`。

## 逐語の行末空白の可逆正規化 (DW-S07)

`verbatim/` の `.md` は `git diff --check` に触れる行末空白 (Codex 出力の Markdown 二重空白改行) を除いてある。可視文字は
不変。原文 bytes は `verbatim/originals.json` (sha256 `0239d0f60b71833f3d3b271d4a2976fe8d955e4687b92da1762fd300098d73c3`) に UTF-8 text として収め、各 text を
そのまま書き出せば原文 bytes を復元できる。末尾改行の無い file は 1 byte 足しただけ。

| file | 原文 bytes | 原文 sha256 | 行末空白を除いた行数 | 正規化後 bytes |
|---|---|---|---|---|
| `s1-brief.md` | 4490 | `1bcf656e5e98c43e…` | 0 | 4490 |
| `s2-plan.md` | 25789 | `8be70daa66f60028…` | 4 | 25782 |
| `s3-lensA.md` | 17865 | `619635f4a37c2932…` | 60 | 17746 |
| `s3-lensB.md` | 17481 | `b6caf4ee716f1e42…` | 88 | 17306 |
| `s4-ruling.md` | 15950 | `89a2a17f2628ad89…` | 0 | 15950 |
| `s5-author-lock.md` | 6375 | `c4e5a13b010402e8…` | 0 | 6376 |
| `s5-author-message.md` | 6688 | `1a513e5e076bad14…` | 0 | 6689 |
| `s6-reviewA.md` | 10715 | `48e24a1f39487f6c…` | 36 | 10644 |
| `s6-reviewB.md` | 11557 | `4a403ab2f4398155…` | 48 | 11462 |
| `s6-fix.md` | 8754 | `3438a26da33ef27d…` | 0 | 8755 |
| `s6-rereview.md` | 4082 | `2ed8b58d302bd93e…` | 4 | 4075 |
