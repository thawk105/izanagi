# [T-2661][T-2663] 到達不能監査の用途分離 — 掃除は repo 外走査を明示 off、救出 triage は明示 full (第 2 段)

- 日付: 2026-09-17
- wave: `dev-wave-t2661-rescue-scope-split` (branch `worktree-dev-wave-t2661-rescue-scope-split`、基準 main `38353207f` → wave 中に
  `05eca6af4`、`60b4bd13f` を取り込み)
- 裁定: D2120 項 24 (第 21 回 /rulings、2026-09-17、用途分離を条件 5 件つきで採る)。D2104 項 20 / D2038 / D2034 (順序)、
  D2115〜D2117 (第 1 段)、D958 / D2116 (所要判定の形)、D247 (抑止の連言条件)、D970 / D1031 (28 + 19 件の裁定)。
- 実装 commit: `0f7b6b73e` (Codex `role=author`、`gpt-6-astra` / `medium`、7 file)、段 6 fix `56d53f247` (同)。docs は後続 commit。
- 一次資料: 本 README、`verbatim/` (brief・plan・段 3 レンズ 2 本・段 4 裁定・author / review 2 本 / fix の報告と prompt)、
  `mutation-spec-*.json` / `mutation-ledger-*.json`、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2661-rescue-scope-split/`
  (計測の生 log = `measure/*.out|.meta|.err`、段 1 / 計測 (d) の probe JSON、patch、prompt、receipt。repo 外なので要点を本 README に写す)。
- 設計判断は decisions fragment (用途分離の契約、本 wave の所要受理対象) に書き、採番は fold が付ける。

## 何をしたか

`tools/audit_dangling_commits.py` に明示 mode `--offrepo-scan {off,full}` を足し、掃除の規範入口 2 箇所を off に固定した。

- **off** は探索根の検証・blob metadata・repo 外走査・cat-file のいずれにも触れず、core snapshot の findings をそのまま返す
  (抑止 0、`findings(full) ⊆ findings(off)` を同一 snapshot の (commit, path) 対で保証)。環境変数 `IZANAGI_DEV_WAVE_JOBS_DIR`
  の探索根は無視し、その旨を専用の開示行に出す (「探索を未実施」「未指定」とは別の文字列。「同一実体は未確認」「findings は
  full なら抑止されうる対を含みうる」「救出 triage は `--offrepo-scan full --offrepo-root <root>` を単独実行」)。
  `--offrepo-root` との併用は usage error (rc 2、terminal 行なし)。`AuditReport.offrepo_scan` (既定 `"full"`、off だけ `"off"`)。
- **full** は既存経路と同一 (同じ探索根を与えた省略時と findings / suppressions / unreferenced_copies / 非時間依存の報告行が一致)。
  探索根が CLI にも環境変数にも無ければ `audit_with_offrepo` 冒頭で `RuntimeError` → 既存の「実行できません」経路 (rc 2、
  stdout に terminal 行 1 本、超過行の順序も既存どおり)。
- **flag 省略は互換経路**として残す (CLI の探索根が環境変数を上書き、どちらも無ければ未実施を開示)。固定したのは掃除の規範
  入口であり、ad-hoc 実行の機械封鎖ではない (第 3 の入口、段 3 レンズ B の B4)。
- **rescue gate** (`tools/check_branch_rescue.py --ledger-check`) の監査の子 process は argv に `--offrepo-scan off` を持ち、
  `_child_env` の allowlist から `IZANAGI_DEV_WAVE_JOBS_DIR` を外した (argv と環境の二重防壁)。JSON の `ledger.audit` に
  `offrepo_scan: "off"` (timeout / decode 失敗 / 通常の 3 返却点すべて)。rc 契約 (0 / 2 / 3 / 64)・通知 kind・parser は不変。
  `_base_payload` の `audit: None` (未起動) は維持。
- **`/cleanup-branches` §1** の監査 bullet を `--offrepo-scan off` に替えた (6,201 → 6,181 bytes、予算 6,204、
  sha256 `7cc008fabc10b3b495eedfeb0bfbee2de14a3c908e1eb5aa6dd7ff4d7ebaf8ae`)。`tools/check_docs.py` の `CLEANUP_COMMAND_SHA256`
  と `test_check_docs.py` の digest・synthetic・予算 fixture (`6_181`、超過 `"x" * 23` = 6,205 bytes) を同時更新。
  `test_branch_rescue_ledger.py` の実行 edge (監査 path と台帳 doc の同一 bullet 共起) は維持。
- docs (親): `docs/unreachable-object-ledger.md` の「dangling audit の分岐」を off / full の入口・実行主体で書き直し、rc 0→3 の
  開示・追記候補集合の増加・既存の追記契約への従属・D970 / D1031 の限定を書いた。`docs/pegasus-runbook.md` §7.2 は triage 用途に
  限定し CLI 例に `--offrepo-scan full` を足した。運用契約の段落 (62〜98) と schema・状態遷移の逐語 pin は触っていない
  (D2120 項 25 = T-2707 が同 doc の別段落を触る予定)。
- test 新設 12 node (`test_audit_dangling_commits.py` 8、`test_check_branch_rescue.py` 4) + p04 の assert 追加。既存 test の期待値は
  変えていない。

## 一次資料 §5 の条件 5 件との対応

| 条件 | 対応 |
|---|---|
| 1. D2034 の順序 | 第 1 段 (T-2637) の実測 (走査強制 fixture、warm 6 走 max 335.8 秒 > 300 秒) で有効化条件を充足 (D2117、D2120 項 24) |
| 2. 未実施と否定結果の分離 | off 専用の開示行 (「未確認」「抑止されうる」)、full + root 無しは rc 2 で黙って未実施にならない、root 拒否・oversize・読出し失敗・reference_failure は従来どおり「確認不能 (抑止せず)」の行 |
| 3. 台帳通知の増加の開示 | 台帳 doc に「`unledgered-audit-finding` が増え rc 0→3 に変わりうる、追記候補集合は off で増える、状態遷移は既存契約、full の抑止行を判断材料に残す」。JSON に `offrepo_scan`。**台帳 entry の免除は書かない** (段 3 レンズ A の must-fix A1: 追記契約 (台帳 doc 47〜48 行) と矛盾) |
| 4. D970 / D1031 を一般許可にしない | 台帳 doc と decisions に「当時の 28 件と追加 19 件についての裁定、新規 commit の一般的破棄許可ではない」 |
| 5. 入口と実行主体の固定 + allowlist の同時修正 | command §1 = off、rescue 子 = argv off + env 遮断、triage = 台帳 doc が full を単独実行として固定 |

## 段 1 の生死確認と計測 (d) — rescue gate の子 process (fixture、job dir `probe_env_inherit.json` / `probe_after.json`)

| tool | 親 env に探索根 | rescue rc | 未記帳通知 | 子の argv 末尾 | 子 env に root key | 子 stdout |
|---|---|---|---|---|---|---|
| 変更前 (main `38353207f`) | あり | **0** | 0 件 (子が走査して抑止) | `--repo <fixture>` | あり | (要約 hash のみ) |
| 変更前 | なし | 3 | 1 件 | `--repo <fixture>` | なし | (同上) |
| 変更後 (`56d53f247`) | あり | **3** | 1 件 (`offrepo_scan: "off"`、`complete: true`) | `--repo <fixture> --offrepo-scan off` | **なし** | 「repo 外走査は明示 off(…の指定も無視);…」の開示行 |

変更前は環境変数の継承だけで掃除の rescue gate の結果が rc 0 / 3 に分かれた (T-2663 の前提)。変更後は環境に依らず off。

## 所要 (login node、`/usr/bin/python3` 3.10、変更後 tool の絶対 path、`--repo` 明示、探索根は full だけ CLI で渡す)

判定対象は掃除の規範入口 (off) の所要 (decisions fragment 2 本目)。D958 項 1 の形 (warm-up 1 走を捨てた独立 3 走、
max/min > 1.5 なら 3 走追加、全走の max)。生 log は job dir `measure/`。

| 系列 | 入力 | warm-up | 有効走 (秒) | max/min | 判定 |
|---|---|---|---|---|---|
| (a) 実 repo `/work/1/SFC/tanab/izanagi` (main `60b4bd13f` 時点、findings 0)、off | rc 0 | 19.793 | 17.697 / 28.915 / 28.322 → 1.63 > 1.5 で +3 → 16.498 / 13.140 / 19.616 | 6 走 max/min 2.20 | **max 28.915 秒 ≤ 300 秒** |
| (b) 走査強制 fixture `/work/1/SFC/tanab/t2637-audit-fixture/repo` (到達不能 1 commit・4 path)、off | rc 1 | 0.240 | 0.079 / 0.086 / 0.083 | 1.09 | **max 0.086 秒 ≤ 300 秒** |
| (c) 同 fixture、full (探索根 `/work/1/SFC/tanab/dev-wave-jobs`) | — | — | 161.400 (1 走、所要判定に使わない) | — | A (`output/wave/s1-brief.md`) を抑止して 3 path を報告。off は A を含む 4 path を報告 = `findings(full) ⊂ findings(off)` の実根デモ |

- (a) の 2〜3 走目 (28.9 / 28.3 秒) は同時刻に本 wave の変異 harness が login 側で `run_tests.py` の収集を走らせていた
  (計数 script は `test_audit_dangling_commits.py` を含む argv に自己マッチしていた。実監査の argv に限定して数え直した追加 3 走は
  0 本)。主観で値を捨てず D958 の形どおり 3 走追加して全 6 走の max で判定した。
- full の 161.4 秒は第 1 段の実測 (110〜336 秒) の範囲内で、本 wave は full を変えていないので再判定も上限達成の主張もしない。
- (a) は現行 main が findings 0 件なので off と省略時の所要差は無い (走査段に入らない)。off の効果は findings がある状態 ((b) と
  (c) の差 = 161 秒 vs 0.08 秒) で出る。

## 段 3・段 6 の所見 (逐語は `verbatim/`)

- 段 3 レンズ A (luna): must-fix 2 = **A1** 「full で全対抑止なら台帳 entry 不要」は台帳 doc の追記契約と矛盾 → 撤回し、追記候補
  集合の増加の開示と既存契約への従属に書き換えた。**A2** P5 (所要受理対象を掃除入口に限定) は D958 / D2116 の読替えでは導けず
  本 wave の判断として明記 → decisions fragment 2 本目。refuted: 受理集合の不変、開示の区別、D970 / D1031 の限定、D247 との両立、
  既存 test の互換。
- 段 3 レンズ B (sol): must-fix 1 = B1 (= A2)。nit: M1 の killer は API off + 非空 roots で (採用)、「127 test」の数量根拠は
  外す (採用)、flag 省略の第 3 の入口は意図した残存 (記録)。refuted: 別 env 経路・landed checker 経由の走査復活、JSON / rc 契約、
  pin 閉包 (文案 6,181 bytes / sha256 は親も独立検算で一致)、T-2639 残骸 (着地済み `99125e783` の patch と一致)。
- 段 6 レビュー U1 / U2: **must-fix 0**。nit = 開示行の全角記号 (fix で半角へ)、M3 の帰属 (`test_explicit_full_without_root_is_execution_failure`
  は git repo でない `tmp_path` を渡すため、拒否を除く変異では `_checked_git` の失敗が先に rc 2 → trap を `_checked_git` にも置いた。
  反実仮想: 拒否ブロックを除くと 2 failed、赤理由 "off must not touch offrepo I/O")、計測 (d) は spawn 記録で子 stdout を取る
  (`probe_after.py`)、焦点走は「計算ノード完走」と記録 (下記)。fix 後の追加レビュー子は起動していない (nit のみ、DW-G05)。

## 実走 (親)

- 焦点走 1 (実装 commit、5 file = TA・TR・TL・plain_runner_coverage・TD): login の bounded local が OOM 上限で計算ノードへ dispatch
  (request 4076.nqsv)、**872 passed / 3 skipped** (skip は `test_check_docs.py` の既存 growth-hold 3 node = 実 repo 検査、
  `opted_in: false`)。author が growth-hold の解除 token で直呼びした TD 22 関数の結果は親の権威に数えない。
- 焦点走 2 (fix 後 `56d53f247`、TA・TR・TL): login bounded local、**289 passed / 0 failed**。
- `python3 tools/check_docs.py`: 違反なし (docs 編集後)。
- 受入全走: docs commit 後の最終 tip で land 前に 1 回 (結果は land の受領証と job dir `acceptance-*.log`)。

## 変異 matrix

container worktree `.codex/worktrees/t2661-mutcontainer` (HEAD `56d53f247` = fix 後の最終実装 tip)、`tools/mutation_harness.py`、
runner = `tools/run_tests.py test_audit_dangling_commits.py test_check_branch_rescue.py test_check_docs.py -q -rf --force-dispatch`
(計算ノード dispatch、`--detached`)。probe 走 (全件 SURVIVED 登録、spec sha `698d4d58…`) で観測 node を集め、それを期待 node に写した
本走 (spec sha `cb9607ee…`)。本走: **baseline PASSED (416 秒、queue 待ち込み)、KILLED 12 / SURVIVED 1 / MISMATCH 0 / TIMEOUT 0、
期待 node と観測 node が 13/13 完全一致** (`mutation-ledger-final.json`)。anchor は全件 file 内で一意 (`make_spec.py` で 0 bad)。

DW-M03 / M08 に従い、受理集合か fail-closed 挙動が変わる本物の kill と、出力・I/O の契約 pin (受理集合は不変) を分けて記録する。

| ID | 変異 | 種別 | 観測 node (完全集合) |
|---|---|---|---|
| M0 | `audit_with_offrepo` の docstring だけ変更 | 等価対照 | SURVIVED (0) |
| M1 | off でも API roots を検証し通常走査経路へ (2 置換) | **受理集合 kill** (API off + 非空 roots で抑止が復活) | `test_explicit_full_suppresses_copy_that_off_reports`、`test_explicit_off_touches_no_offrepo_io` (2) |
| M2 | `main` の off 分岐で env root を読む (読んで捨てる) | 契約 pin (I2「読まない」) | `test_explicit_off_ignores_env_and_preserves_core` (1) |
| M3 | full + roots 空の `RuntimeError` を除去 | **fail-closed kill** (rc 2 → 未実施) | `test_explicit_full_without_root_is_execution_failure[absent]` / `[empty]`、`test_explicit_full_missing_root_preserves_elapsed_overrun` (3) |
| M4 | rescue 子 argv から `--offrepo-scan off` を落とす | 契約 pin (env 遮断が残るため結果不変) | `test_audit_child_argv_is_explicit_off`、`test_real_audit_off_reports_landed_external_copy_with_or_without_env` (子 stdout の開示行 assert) (2) |
| M5 | `_child_env` の allowlist に root env を戻す | 契約 pin (argv off が残るため結果不変) | `test_child_env_omits_offrepo_root` (1) |
| M45 | M4 + M5 (両層) | **受理集合 kill** (子が走査して抑止、rescue rc 3 → 0) | M4 の 2 + `test_child_env_omits_offrepo_root` (3) |
| M6 | off の開示行を従来の未指定 2 行に替える | 出力契約 pin (条件 2) | `test_explicit_off_disclosure_is_distinct_from_missing_root`、`test_real_audit_off_reports_…` (2) |
| M7 | off + `--offrepo-root` の usage 拒否を除去 | **fail-closed kill** (rc 2 → off で走り rc 1) | `test_explicit_off_with_cli_root_is_usage_error[no-env]` / `[env]` (2) |
| M8 | rescue JSON の summary 3 箇所から `offrepo_scan` を落とす | 出力契約 pin (条件 3) | `test_audit_summary_discloses_off_for_all_outcomes` ×5、`test_real_audit_off_reports_…`、`test_p04_…` (7) |
| M9 | `CLEANUP_COMMAND_SHA256` を旧値へ戻す | **gate kill** (check_docs が赤) | `test_codex_cleanup_branches_skill_contract_pins_exact_surface` を含む 321 node (digest 不一致で合成 repo を実 checker に掛ける正例 test が一斉に赤) |
| M10 | off の早期返却前に `_load_blob_metadata` を呼ぶ | I/O 契約 pin (I2) | `test_explicit_off_touches_no_offrepo_io` (1) |
| M11 | off でも `_validate_offrepo_roots` を呼ぶ | I/O 契約 pin (I2) | 同上 (1) |

- 「`or offrepo_scan == "off"` だけを削る」局所変異は roots 空で既存条件が返すため等価 → 登録していない (段 2 plan の指摘)。
- M4 / M5 は単独では二重防壁の片方が残り findings は変わらない — argv / env を直接 assert する node が殺す契約 pin であり、
  受理集合の kill は両層 M45 が担う (事前登録どおり、DW-M04)。
- M3 は段 6 fix (`_checked_git` にも trap) の後で probe を取っており、赤理由は拒否欠落 (trap) に単一化されている。
- 所要: probe 44 分 (13 変異 + baseline、queue 待ち込み、最長 M3 699 秒)、本走 34 分 (最長 M0 821 秒 = queue 待ち)。test 自体は 1 走 32〜48 秒。

## 残存限界・scope 外 (記録のみ)

- flag 省略 + 環境変数の探索根は full 相当のまま (第 3 の入口)。固定したのは掃除の規範入口 2 箇所であり、任意の ad-hoc 実行の機械
  封鎖ではない。
- off で通知された object は既存の追記契約どおり `pending` entry の追記対象になる。従来 full で抑止され通知されなかった object も
  含まれるため、掃除 1 回あたりの追記候補は増えうる (条件 3 の開示)。full の抑止行は `resolution_note` の判断材料に残すが、状態遷移
  (`rescued` / `accepted-loss` / …) の選択は従来どおり人間の裁定。
- `IZANAGI_AUDIT_SCAN_WORKERS` は rescue 子の allowlist に足していない (off の子には無意味)。T-2663 の残部 (二重走査) は本 wave で消えた。
- T-2662 (境界 helper)、T-2664 (hardlink alias)、T-2749 (rescue 予算定数)、cleanup command §2〜§5、通知 kind・台帳 field は触っていない。
- `/cleanup-branches` は wave 中に peer session が稼働していた (main の現行 tool を使用)。本 wave の変更後経路は掃除に使っていない。
- 「現在 145 本」(brief) は親の `scan_overlap.py` (21:5x JST、`git worktree list --porcelain` の worktree 行数) が出所。

## 逐語の行末空白の可逆正規化 (DW-S07)

`verbatim/` の `.md` は `git diff --check` に触れる行末空白 (Codex 出力の Markdown 二重空白改行) を除いてある。可視文字は不変。
原文 bytes は `verbatim/originals.json` (sha256 `a9416bf9f81a42a263130cdf6d44396d3dece7916f14eeda774db03065582e28`) に UTF-8 text として
収め、各 text をそのまま書き出せば原文 bytes を復元できる。末尾改行の無い file (`s2-plan.md`、`s3-lensA.md`、`s3-lensB.md`、
`s5-author.md`、`s6-reviewA.md`、`s6-reviewB.md`、`s6-fix.md`) は末尾改行を 1 byte 足しただけ。

| file | 原文 bytes | 原文 sha256 | 行末空白を除いた行数 | 正規化後 bytes |
|---|---|---|---|---|
| `s1-brief.md` | 9406 | `f2d270f8d549f9a0…` | 0 | 9406 |
| `s2-plan.md` | 29790 | `8ff1991e4bcc7c8e…` | 2 | 29787 |
| `s3-lensA.md` | 15019 | `cbbd3e6a352e685a…` | 1 | 15018 |
| `s3-lensB.md` | 17528 | `496580ac2b0edf0d…` | 0 | 17529 |
| `s4-adjudication.md` | 13254 | `eb996a3197e0b3d6…` | 0 | 13254 |
| `s5-author.md` | 11022 | `b722ea5e30d5b11e…` | 0 | 11023 |
| `s6-reviewA.md` | 12750 | `5166d4020765ddca…` | 0 | 12751 |
| `s6-reviewB.md` | 8177 | `fa25acf654ff2426…` | 0 | 8178 |
| `s6-fix-prompt.md` | 4966 | `de8893228d284fde…` | 0 | 4966 |
| `s6-fix.md` | 2316 | `3b2c72c75a3685a5…` | 0 | 2317 |
