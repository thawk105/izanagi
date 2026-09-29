# worktree 撤去の同時実行制限 (2026-09-29、branch worktree-dev-wave-cleanup-remove-lock)

authority: none / default_effect: no-state-change — 実装の正本は `tools/dev_wave_cleanup.py` と `docs/dev-wave/operations.md` の DW-O28。

## 1. 依頼と背景

- 依頼: 並行 wave 指示 md_1 (`/work/1/SFC/tanab/tmp/git-maint-2026-09-29/md_1.txt`、共通 `common.txt`)。
- 背景 (common.txt §1、2026-09-29 pegasus02 実測): 並行 session が `tools/dev_wave_cleanup.py remove-child` を 16 本同時に起動し、
  全部が Lustre の I/O 待ち (state D) で 20 分以上止まり login の load が 84 になった。1 本の撤去は単独でも 75 秒〜15 分。

## 2. 変更

- 撤去の両 mode (wave 撤去・`remove-child`) で、既存の最初の `git rev-parse --git-common-dir` の直後に、common dir の
  directory fd (`O_RDONLY|O_DIRECTORY|O_CLOEXEC`) へ `flock(LOCK_EX|LOCK_NB)` を掛け、撤去終了 (process 終了を含む) まで保持する。
  取れなければ待たずに stderr 1 行 `dev-wave-cleanup: status=busy phase=removal-lock reason=...`・stdout 空・rc=75 で返る。
- git 呼出しは 1 本も増やしていない。取得より前に走るのは argv 検査・branch 名の `check-ref-format` (wave mode)・common dir 解決だけ。
- 既存 rc (2/20/21/22/30) の意味は不変。`tools/dev_wave_land.py` は変更せず、この lock を取らない・待たない
  (land が flock するのは common dir 内の別 file `dev-wave-land.lock` と turn dir の file で、common dir の directory fd ではない)。
- DW-O28 に 1 文「撤去はrepo全体で1本ずつ(並列はLustre過負荷)、rc=75は数分後再試行」を足した。L2 単節予算 1000 bytes に収めるため
  既存文の CJK 隣接空白と冗長語を詰めた (994→997 bytes、義務文の削除なし)。exact pin (check_docs literal・合成 fixture) を追随。

## 3. 設計の経緯 (段 6 で 1 回改めた)

- 当初 (段 4 の P1) は `<common>/izanagi-worktree-removal.lock` file を作って flock する案だった。
- 親の login 自走で既存 test `test_remove_child_rejects_wave_root_and_primary[primary]` が赤: 拒否経路でも primary の `.git` に空の
  lock file が新規作成され、「拒否時に primary の木を 1 byte も変えない」既存期待に反した。期待は正しいので実装を直し、
  file を作らない directory fd の flock に改めた (fix-1)。directory flock は同 tool の `_bind_admin` が Lustre 上で既に使っている。
- 実測前提: `/work` は lustre を `flock` option 付きで mount (`/proc/mounts`)。ノードを跨いだ排他の実測はしていない (login 1 台で検査)。

## 4. 検査

- 焦点走 (login 自走 `PYTHONPATH=. python3 orchestrator/tests/test_dev_wave_cleanup.py`): 統合直後 204 passed / 1 failed (上の既存 test) →
  fix-1 後 205 passed → fix-2 後 205 passed。
- 新テスト `test_repository_removal_lock_is_nonblocking_and_released[<release>-<mode>]` (4 通り): 別 process が実際に flock を保持する間に
  CLI を subprocess (timeout 60 s) で起動し、両 mode とも rc=75・stderr 1 行・stdout 空・木/admin/branch/primary 不変。
  保持 process の正常終了後と SIGKILL 後に、同じ撤去が in-process で `removed` になる。
- 実 repo `python3 tools/check_docs.py`: 違反なし。`test_check_docs.py` は growth hold 対象で自走不可
  (`IZANAGI_GROWTH_HOLD_BYPASS_REFUSED_V1`)。代わりに DW-O28 の 3 箇所 (docs・literal・合成 fixture) の byte 一致 (997) を直接照合した。

## 5. 変異台帳 (login 自走 probe `mutation_probe.py`、1 変異ずつ注入→自走→`git checkout --` 復元→sha256/porcelain 照合)

期待 node は走行前に登録 (新テスト 4 node のうち、M4 は remove-child の 2、M5 は wave の 2、他は 4)。

| 変異 | 内容 | run 1 (bcc7bf591) | run 2 (6704fc0a6、最終) |
|---|---|---|---|
| M1 | lock 取得の flock を除去 | KILLED 4 | KILLED 4 (89 s) |
| M2 | `LOCK_NB` を外し blocking 化 | KILLED 4 (timeout) | KILLED 4 (timeout、303 s) |
| M3 | `RC_BUSY = 75` → `20` | **SURVIVED** (205 passed) | KILLED 4 (53 s) |
| M4 | remove-child 側の取得呼出しを除去 | KILLED 2 (remove-child) | KILLED 2 (remove-child、53 s) |
| M5 | wave 側の取得呼出しを除去 | KILLED 2 (wave) | KILLED 2 (wave、66 s) |
| M6 | check_docs の DW-O28 literal 末尾 1 文字 | 実 repo check_docs が DW-O28 exact 不一致 1 件で rc=1 (KILLED) | — (literal 不変) |

- M3 の生存は real (等価変異ではない): 新テストが `returncode == cleanup.RC_BUSY` と定数どうしを比べていた。rc=75 は DW-O28 に書いた
  CLI 契約で、20 は既存の拒否 rc と衝突する。fix-2 で字面の 75 と比べる形にした。
- common.txt が計算ノード job を受入全走に限るため、変異は dispatch final を回さず login 自走だけで判定した。

## 6. 段 6 レビュー (read-only 1 本、正しさ境界 + 過剰・削除の 2 レンズ兼務、NO-GO) の裁定

- R1 lock 前に `check-ref-format` が走る: refuted。branch 名の usage 検査 (rc=2) で argv 検査の一部、親が実装子へ明示許可した順序。
- R2 不正な `--main-worktree` (linked worktree 等) が他の撤去と競合すると rc=20 でなく rc=75 になる: refuted (設計どおり)。
  busy 判定は検証より先に置いた。再試行時は従来どおり rc=20 で拒否され、rc=20 の意味は不変。
- R3 DW-O28 から「段 9 に」が消え「両方に付ける」を「両方に」へ短縮: nit。land は段 9 にしか起きず、節の発火条件も
  「land 成功後の自己撤去直前」。予算 997/1000 に復元の原資なし。
- R4 解放後の再試行が CLI でなく in-process: nit (証明範囲の限定)。

## 7. 限界

- lock は撤去 1 本の全期間 (実測 75 秒〜15 分) 保持されるので、その間の 2 本目以降は rc=75 で戻る。待たせないのが依頼の目的。
- `tools/cleanup_remove_dirs.py` (cleanup-branches の並列 `rm -rf`、D2113) はこの lock の対象外 (依頼の scope 外)。
- ノード跨ぎ (login 同士・計算ノード) の排他は mount option からの推論で、実測していない。
