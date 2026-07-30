# dev-wave 並行 land — 段 4 裁定 / plan v2

## 裁定

- plan v1 と敵対相談 2 本はいずれも NO-GO。所見は real 19、refuted 8、scope 外 6 と裁定する。
- 採用: 協調する Claude / Codex dev-wave manager の main mutation を短時間 lock + 単一 helper に直列化する。
- 採用: main の untracked 例外は、schema-valid な `docs/handoff/*.md` と Git admin metadata へ
  双方向束縛できる `.claude/worktrees/` / `.codex/worktrees/` direct child だけに閉じる。
- 採用: handoff は `作業中` / `計測中` / `中断` と stale の全てを宣言板/WALとして許可し、
  freshness は診断に限る。他 session 所有物は変更・stash・commit・削除しない。
- 採用: `.gitignore` は変更しない。既存 supervisor の strict cleanliness を横断的に弱めない。
- 採用: helper は common git-dir の lock を `O_NOFOLLOW` で開き、merge child へ FD を限定継承する。
- 採用: Git 2.34.1 の line porcelain を registry trust root にせず、linked worktree の `.git` と
  common admin `gitdir` の双方向 metadata を bytes / dirfd / inode で検査する。
- 採用: shallow / graft / replace を拒否し、hooks / lazy fetch / fsmonitor / autostash /
  auto-maintenance を無効化する。現 repo の local filter / hook 契約を実測し、unsupported 設定は拒否する。
- 採用: merge 後失敗は `not-landed` と `landed-postcondition-failed` を HEAD 実測で分け、後者を自動 retry しない。
- 採用: helper は `DW-S09` / 新しい段9 operation だけから呼ぶ唯一の通常 land 経路とし、
  Claude / Codex adapter は同じ dispatcher を通る。Skill へ helper path を重複 pin しない。
- 採用: 同じ base の2 waveで winner land→loser stale→main merge / 再受入→loser land→最終 main が
  両成果を含む deterministic integration test を必須にする。
- 棄却: `9→6→7→8→9` back-edge。段8一回、worklog一回、期限付き rollback と衝突する。
  stale main / lock busy は現 wave を fail-closed に閉じ、fresh context の `$dev-wave <同対象>` が
  既存専用 worktreeを再利用して upstream audit・merge・必要段から再実行する。
- 棄却: canonical acceptance receipt の新設。helper は acceptance の証明機構ではなく、manager が
  実測した tested SHA と監査済み commit 列を stale/race から守る操作 guard とする。自己申告を
  暗号学的証明とは主張しない。
- 棄却: gitlink 一律禁止。本 wave のテストは net gitlink 不変で行うが、一般 dev-wave の既存能力を
  縮小しない。gitlink変更時の post-land submodule同期は D16 系の既存契約に従い、本 helperが成功を偽らない。
- scope 外: 同一 UID の非協調 writer、悪意ある common git-dir 改変、cross-host で flock 非整合な mount。
  本変更は dispatcher に従う協調 manager 間の事故防止であり、単一 writer daemonへの権限移管は行わない。
- scope 外: dev-wave supervisor real開放、remote、push、cleanup、他 session の branch / handoff変更。

## plan v2

### author worker 所有

1. `tools/dev_wave_land.py` を新設する。
   - cwd の linked worktreeと common git-dir / primary main worktreeを相互検証する。
   - tested main SHA、tested wave tip SHA、監査済み `A..T` commit列を exact に検査する。
   - `A == current main`、または `A <= current main <= T` かつ current main が監査列内なら受理する。
   - main tracked/index/submodule dirt と未知 untracked を拒否し、上記 control-plane例外だけ許可する。
   - nonblocking land lock内で再観測し、SHA targetへの `merge --ff-only` だけを実行する。
   - rcとJSON結果で `landed` / `already-landed` / `stale-main` / `lock-busy` /
     `not-landed` / `landed-postcondition-failed` を区別する。
2. `orchestrator/tests/test_dev_wave_land.py` を新設し、直接runnerとpytestの両方に結線する。
3. `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` を更新する。
   - 新しい段9 operation、condition dispatch、`DW-S09` 内の helper唯一経路 literalを固定する。
   - Codex Skillが共通 dispatcherを参照し続ける既存閉包を維持する。
   - reference aggregate 24,000 bytesを上げず、意味等価な縮約で収める。
4. docs / handoff / insight / commit は編集しない。

### 親所有

1. `.claude/commands/dev-wave.md` の段9 dispatch / conditionと終端を、新 operationのpointerへ更新する。
2. `docs/dev-wave/core.md` の `DW-STOP` / `DW-S09` を縮約し、fresh-context resume境界を明記する。
3. `docs/dev-wave/operations.md` に段9 land operationを追加し、helper手順とcontrol-plane例外の正本にする。
4. Codex Skillの段9再掲を共通 dispatcher遵守へ縮退し、Codex固有のfresh context / hook /
   supervisor境界は残す。
5. D/F/phase/worklogとmutation台帳を記録し、main再同期時にtask ID・worklog番号を再採番する。

## mutation 事前登録

| ID | 単一変異 | 期待する赤 |
|---|---|---|
| M1 | tested-main exact / ancestor-in-tested-tip 判定を常時許可 | stale loser test |
| M2 | `LOCK_EX | LOCK_NB` を無効化 | concurrent two-lander test |
| M3 | main tracked dirt 判定を無効化 | tracked/staged dirt test |
| M4 | unknown untracked を control-plane扱い | unknown-untracked test |
| M5 | handoffのregular/non-symlink/schema判定を無効化 | symlink/malformed handoff test |
| M6 | worktree admin metadataのbackpointer照合を無効化 | unregistered/alias container test |
| M7 | shallow/graft/replace拒否を無効化 | history-modifier test |
| M8 | wave HEAD/ref == tested tip再照合を無効化 | moved-wave-tip test |
| M9 | main mutation後のHEAD実測による結果分離を無効化 | landed-postcondition-failed test |
| M10 | valid foreign handoffを一律拒否 | handoff positive control |
| M11 | registered Claude/Codex worktreeを一律拒否 | container positive controls |
| M12 | helper pointerを `DW-S09` から除去 | check_docs negative fixture |
| M13 | loser再同期の2-wave E2Eをhelper単発に縮退 | independent surface pin / E2E test |

各変異は対象test nodeを実装後に台帳へ固定する。前段で同じ入力を拒否する場合は無効 kill として
数えず再照準する。復元後は対象 module の bytecode cache を無効化し、source bytesと対象testを再確認する。

## 成果物影響

この plan を実装しない場合、正常な並行 session の handoff / worktreeだけで mainがdirtyと誤判定され、
また同時landがmain index / working tree / refを競合更新し得る。実装により通常landを直列化し、
race loserを復旧可能なfresh-context resumeへ送る一方、未知dirtと未監査tipは引き続き拒否する。
