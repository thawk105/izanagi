# [T-2232] 段 4 loop 用 Pegasus job body と登録簿の同期

段 4 loop (`orchestrator/campaign/p3_s4_loop.py`) を Pegasus 計算ノードで走らせるための
compute-only job body `tools/pegasus/p3_s4_loop_pegasus.sh` を新設し、登録簿・手順書投影・README の
tagged qsub command・hooks golden を同じ変更単位で同期した wave の一次資料。
**新規 Pegasus 実行体なので、本 wave では一度も投入していない (F660)。** 検証は login node の
短走 (DW-G01: stub harness による job body の実行、`bash -n`、契約テスト 44 件) と登録簿の contract
テストまでで止めた。

## 何が変わったか

- `tools/pegasus/p3_s4_loop_pegasus.sh` (新規、755): 親が直接 `qsub` する job body であり投入器ではない。
  host gate (`bnode[0-9]+`) を PATH sanitize より前に置き、環境を閉集合へ落とし (`GIT_*`、`CCACHE_*`、
  `CONFIG_SITE`、`IZANAGI_*_OUTPUT_ROOT` 等を unset、`GIT_OPTIONAL_LOCKS=0`)、`/.claude/worktrees/`・
  `/.codex/worktrees/` を含む REPO_ROOT と repo 配下の evidence root を rc=2 で拒否する。
  `python3.10` を exact に解決して `python3` だけを置く shim dir を作り、expected HEAD・tracked clean・
  CCBench pin (`p3_s4_loop.PIN` exact) を検査し、`qstat -f` から `IZANAGI_RESERVATION_*` 8 変数を
  A-2 と同じ形で束縛し、claim root を provisioning し、3 つの hydrate source を scratch へ `cp -a`
  してから `buildcache.prepare_masstree_fetchcontent` で masstree `config.h` を事前構築する
  (F813: PATH の CMake wrapper で third-party を注入しない)。driver は `--allow-coder-derived-build
  --isolate-worktree` で起動し、`--no-build` は禁止。成果物は evidence root に `compute-result.json`
  (create-only)、`reservation.json`、`masstree-prebuild-receipt.json`。
- `tools/pegasus/admission_registry.json`: `dispatch-required` で登録 (`static job-body classification`)。
- `orchestrator/tests/test_hooks.py`: 登録簿 golden 2 箇所に同じ entry。
- `orchestrator/tests/test_p3_s4_loop_job_contract.py` (新規、44 node): 静的契約 fragment、禁止構文、
  実行面 (heredoc・comment 除去後) での段順序と出現数 1、rc=2 文言、fragment 変異、shim 閉集合、
  `--no-build` 負例、CMake env 負例、qsub token 検査、resolver harness (旧 `python3` 負例)、
  `PBS_JOBID` 写像、login-host 拒否 harness、worktree container 拒否 harness、`git status` 失敗の
  fail-closed harness、claim-root の env tag import、登録簿 exact entry、README tagged fence の `-o`/`-e`。
- `tools/pegasus/README.md` §0 に `qsub-job-body` / `dispatch-required` 行、§7 に tagged qsub command
  (`# admission-site: qsub-job-body`、`-o`/`-e` は evidence root)。`docs/pegasus-runbook.md` §7.0 に投影行。

## 構成

- `s1-brief.md` — 段 1 brief (親)。割れうる前提 P1〜P4
- `s4-adjudication.md` — 段 4 裁定 (親)。C0〜C17、plan v2、変異事前登録 16 件
- `s6-adjudication.md` — 段 6 裁定追補 (親)。D1〜D9、must-fix 6 件
- `mutation-spec.json` — 本走に使った変異 spec (期待 node は probe の実測から機械生成)
- `mutation-probe-spec-v1-erratum.json` — 初回 probe spec (erratum: M3 の anchor が fix 後に消えたため再照準前の原本)
- `mutation-ledger.json.gz` — 変異本走の台帳全文
- `verbatim/` — codex 子の出力逐語 ([T-686] により placeholder guard・三軸語検査の対象外)
  - `s2-plan.md` (plan)、`s3-lens-a.md` / `s3-lens-b.md` (敵対相談)
  - `s5-author.md` (実装)、`s6-review-a.md` / `s6-review-b.md` (敵対レビュー)
  - `s6-fix.md` (fix)、`s6-focus-review.md` (fix 後の焦点再レビュー、GO)

### 逐語の可逆最小正規化 (DW-S07)

codex 出力の総括節にある markdown の強制改行 (行末 2 空白) が `git diff --check` に抵触するため、
可視文字を変えずに行末の空白だけを落とした。復元法: 下表の `行:byte 数` の各行末へ同数の
半角空白 (U+0020) を戻すと原文 sha256 と byte 数に一致する。原文は wave job dir
(`dev-wave-jobs/dev-wave-t2232-s4-loop-pegasus-job-script/codex/`) にも残る。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 落とした行:byte 数 |
|---|---|---|---|---|---|
| `s2-plan.md` | `25449b316af609722286e53a302cf51dce5996dc2b97d218c888ee89b6856163` | 23435 | `83fda4e8c77fb8527e52f212ba89e449a1ec6ac79344d808d87bfc26274bf31b` | 23429 | 315:2, 316:2, 317:2 |
| `s3-lens-a.md` | `8c8fc99717e5ce373e547c32bdbfc8fc3951e674823ffb636294ccaddcda9da2` | 10583 | `95788712eb603c5c396612c33b26eaba11113ab1283c486fdc4c16d5f0e60050` | 10575 | 43:2, 44:2, 45:2, 46:2 |
| `s3-lens-b.md` | `041ea77456fd77f7dcd6b56fc0073a11d05bc27d2a500154d399a41b1bd6694d` | 9348 | `e805c4ac83f5332e45d8e6c1144c9d3c345f897a9646d0764c5d2de0e6f27228` | 9340 | 39:2, 40:2, 41:2, 42:2 |
| `s5-author.md` | `e0979abcb2455634d12e5a259c0a5b8bb75bc3401a741dcc68ca8d119eda063c` | 7890 | `b107996da19482957a5a80c2568fa28fccffcc13884176f42aa494a3cdf63919` | 7884 | 77:2, 78:2, 79:2 |
| `s6-fix.md` | `ed71a64b87ba4373abe13684bd017ee5742fe3075ee8e887ad079963958645cb` | 4497 | (無変更) | 4497 | なし |
| `s6-focus-review.md` | `950a1e4e3483dfaeeb2cf05227beb2e28f76332e5ef87151d7ef1a988ce0e5dc` | 3222 | `0084deb2e497efa7f1f5c591af45f5f7ac074ff4272f5c3dee51d58acd53466d` | 3216 | 22:2, 23:2, 24:2 |
| `s6-review-a.md` | `2ba358852a69e39d602459ca3a81d7789d6a9b3653aa23675bf0841edc097e1e` | 4226 | `a507614e03c7618e63767e108b994a84b00ab045c655dc8c0b9ab3432d8d8e72` | 4220 | 31:2, 32:2, 33:2 |
| `s6-review-b.md` | `ef2b0ac8397a5d7446f7c78b92f603f450d54dda6e670e081e20609fc87b1349` | 6836 | `ff19eb152805a88ef48d57e38b4be628eb49bbb66f39e6f7568b6126122b9979` | 6830 | 56:2, 57:2, 58:2 |

## 実測・レビューで覆した前提

1. **「事前構築は無害な死んだ経路」(brief P1) は誤りだった。** hydrate 済み source root の中で
   masstree を configure すると durable な staged source に `config.h` と archive が生成されて汚れる
   (`ThirdParty.cmake`)。3 source を scratch へ `cp -a` してから SOURCE_DIR に渡す形に訂正した (C0/C4)。
2. **`[[ -n "$(git status ...)" ]]` は `git status` の失敗を clean と読む。** 3 箇所 (superproject、
   CCBench、third-party source) すべてで rc を明示検査し、失敗は rc=2 で止める形へ直した (D1)。
   負例 harness は stub `git` に「status で rc=1・空 stdout」を返させ、後段の sentinel が呼ばれない
   ことを固定する。
3. **順序検査は raw source の `index` では dead comment の前置複製に欺かれる。** heredoc と comment 行を
   除いた実行面で照合し、各 marker の出現数 1 を要求する形へ直した (D6)。

## 保証範囲 (主張の限界)

- job body は本 wave で一度も Pegasus に投入していない。`qstat -f` の出力形式、`/scr/$USER` の可否、
  compute node 上の `python3.10` の実在、proxy 経由の FetchContent、reservation 束縛の実効は
  **未実測**であり、初回投入で割れうる。attestation の exact 照合
  (`env_attestation.load_verified_calibration`) はユーザー指示により本 wave では触れていない。
- 契約テストの harness は stub (`hostname`・`git`・`qstat`・`cmake` の sentinel) で job body を
  login node で走らせたものであり、実機の挙動を一般化しない。
- 登録簿の class 変異 (M13) は `test_hooks` golden と exact entry test の冗長 gate で捕まる。
- scope 外の real 所見 (実装せず、裁定パッケージ候補): FetchContent 依存 identity の build identity
  未束縛、`make`/`ar`/`git`/`nm` の tool identity、condition gate record の durable 化、
  `--isolate-worktree` の `TMPDIR` 検査、事前構築成果を driver が消費する seam。

## 変異の結果 (16/16 KILLED、期待 node と完全一致)

- 手順 (DW-M07): 事前登録 16 件を probe (全件 SURVIVED 登録) で走らせて観測 node を集め、期待 KILLED +
  観測 node の spec を機械生成して本走した。runner は `tools/run_tests.py --force-dispatch`
  (contract test + `test_hooks.py`)、`--runner-mode dispatch`、baseline PASSED。
  本走 spec sha256 `de838ea60a5c3122b12e3baf1b06f8b58ea09a0b6fc5fa174eb275ca4ae1fc2c`、
  repo HEAD `525a9997a`、schema `izanagi-dev-wave-mutation/v4`。台帳全文は `mutation-ledger.json.gz`。
- erratum (DW-M02): fix (`8a55e663a`) で superproject clean 検査が 2 行に分かれ、M3 の anchor
  (`[[ -n "$(git status ...)" ]]` の 1 行形) が消えた。fix 後の実効 gate `[[ -z "$superproject_status" ]]`
  行へ再照準した (spec v2、初回 spec は `mutation-probe-spec-v1-erratum.json` として残置)。
  段 6 裁定 D3 (M7 の登録文) は「shim を作らず bare `python3` を PATH 先頭に残す」で spec と一致。
- probe 1 回目は untracked な `s6-adjudication.md` で harness が起動前に停止 (rc=2、tree 無変更)。
  docs-only commit の後に再投入した。

| 変異 | 内容 | 殺した test (node 数) |
|---|---|---|
| M1 | host regex を `^(bnode\|pegasus)[0-9]+` へ緩める | login 拒否 harness (1) |
| M2 | expected HEAD 比較行を削除 | 静的契約 + fragment mutant 群 (25) |
| M3 | superproject clean 検査を恒真化 (`[[ -z "" ]]`) | 静的契約 + fragment mutant 群 (24) |
| M4 | CCBench pin を `pin.CURRENT_PIN` から取る | 静的契約 + fragment mutant 群 (24) |
| M5 | `${PBS_JOBID//:/_}` を `$PBS_JOBID` へ | PBS_JOBID 写像 test (1) |
| M6 | evidence root の repo 配下拒否を削除 | 静的契約 + fragment mutant 群 (24) |
| M7 | shim を作らず bare `python3` を PATH 先頭に残す | resolver harness + status 負例 harness (2) |
| M8 | shim dir へ `cmake` symlink を足す | 静的契約 + status 負例 harness (2) |
| M9 | `cp -a` を省き hydrate root を SOURCE_DIR に直接渡す | 静的契約 + fragment mutant 群 (24) |
| M10 | receipt の `open(..., "x")` を `"w"` へ | 静的契約 + fragment mutant 群 (24) |
| M11 | `--allow-coder-derived-build` を `--no-build` へ | 静的契約 + shim / CMake env 負例 (15) |
| M12 | job body へ `qsub job.sh` 行を足す | token 化 qsub 検査 + status 負例 harness (2) |
| M13 | 登録簿 class を `local-ok` へ | 登録簿 exact entry test + `test_hooks` golden 3 件 (4) |
| M14 | host gate を PATH sanitize の後ろへ移す | 順序検査 + login / worktree / status harness (4) |
| M15 | reservation の `DEADLINE_EPOCH` export を削除 | 静的契約 + fragment mutant 群 (24) |
| M16 | claim root の provisioning 行を削除 | 静的契約 + fragment mutant 群 (24) |

fragment 削除型 (M2〜M4、M6、M9、M10、M15、M16) が 24〜25 node を落とすのは、静的契約に加えて
parametrized な fragment mutant test が「production 側の欠落 + 試験 mutant」で 2 件の静的失敗を観測して
赤になるためである (D7 の前提 `count <= 1` は重複だけを拒否し、欠落は helper の例外へ委ねる)。
M13 は `test_hooks` golden との冗長 gate であり、登録簿 exact entry test 単独でも捕まる。
