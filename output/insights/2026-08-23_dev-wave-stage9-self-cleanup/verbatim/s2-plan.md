結論は、`dev_wave_land.py` を変更せず、成功 JSON を親が確認した後に新 CLI を呼ぶ二段構成です。ただし brief には、実装前に裁定が必要な矛盾が二つあります。

- 条件 25 は「land 起動直前」ですが、自己撤去の発火点は「land 成功後」です。
- 「非 0 なら何も撤去されていない」は、`rm -rf` 後に prune / branch 削除が失敗し得るため、文字どおりには保証できません。

以下は、この矛盾を明示した実装プランです。テストは実走しておらず、緑は主張しません。

## 1. file:line 実装順序

### `tools/dev_wave_cleanup.py`（新規、予定行）

- `:1-35` — import、rc 定数、40/64 桁 lowercase SHA、結果・要求 dataclass。
- `:36-75` — CLI parser。4 引数を必須かつ各 1 回だけ受け付ける。
- `:76-130` — shell を使わない subprocess wrapper、git stderr の一行化・500 byte 上限。
- `:131-210` — canonical path、branch、`worktree list --porcelain -z` parser。
- `:211-315` — main / wave / ref / tip / dirt / cwd / ancestry の preflight。
- `:316-355` — [既存 occupancy checker](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_worktree_occupancy.py:459) の呼び出しと JSON 再照合。
- `:356-440` — unlock → detach →再検査→ `rm -rf` → prune → `branch -d`。
- `:441-485` — postcondition、`removed` / `already-clean`、stderr、`main()`。

### `orchestrator/tests/test_dev_wave_cleanup.py`（新規、予定行）

- `:1-90` — import、git helper、cwd helper、CLI 呼び出し helper。
- `:91-165` — primary repo と `.claude/worktrees/<wave>` を作る fixture。
- `:166-235` — locked / unlocked の実 Git 正例、削除後の全 postcondition、二回目の `already-clean`。
- `:236-360` — dirt、occupancy、cwd、primary、branch/tip/ancestry、別 repo、symlink の負例。
- `:361-420` — porcelain の `locked` / `locked <reason>` / malformed / duplicate の parser テスト。
- `:421-500` —各 mutation phase の失敗注入、後続命令を呼ばないこと、partial failure 表示。
- `:501-540` — source/argv の静的検査。`worktree remove`、`submodule deinit`、`branch -D` が実行経路にないことを固定。

### docs と pin

- [operations.md:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/dev-wave/operations.md:165) — `DW-O25` の見出しと節全文。
- [check_docs.py:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:577) — exact section literal。
- [check_docs.py:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:608) — exact pin 登録表の見出し key。
- [test_check_docs.py:167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:167) —合成 O25 節。
- [test_check_docs.py:8567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:8567) — production literal と fixture の一致、および新たに 960-byte assertion。
- [test_check_docs.py:8737](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:8737) —実 repo の exact-pin 正例。

## 2. CLI argv 契約

```text
python3 tools/dev_wave_cleanup.py \
  --main-worktree <ABSOLUTE_PRIMARY_MAIN> \
  --wave-worktree <ABSOLUTE_WAVE_WORKTREE> \
  --wave-branch <LOCAL_BRANCH_NAME> \
  --tested-wave-tip-sha <FULL_LOWERCASE_SHA>
```

4 引数すべてを必須にします。重複指定も拒否します。

推論しないものは次のとおりです。

- cwd から main / wave を推論しない。
- wave の symbolic HEAD から branch 名を推論しない。
- branch ref から tested tip を推論しない。
-環境変数、最新 land receipt、最後の stdout を探索しない。
-複数 worktree、glob、branch prefix を受け取らない。
- `--force`、`--all`、`--resume` は設けない。

`--land-status` は追加しません。任意文字列を渡しても land 成功の証明にはならないためです。親が [dev_wave_land.py:3618-3627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/dev_wave_land.py:3618) の JSON と rc を確認し、`status` が厳密に `landed` / `already-landed` の場合だけ cleanup を起動します。cleanup 自身は tested tip の main 包含を再検証します。

## 3. fail-closed 検査の順序

すべて unlock より前に完了させます。

|順|検査|失敗時|
|---:|---|---|
|1|4 argv が各 1 回、絶対・正規化 path、SHA 40/64 桁 lowercase、branch が安全な short name|usage/preflight failure|
|2|main が primary checkout、symbolic HEAD が `refs/heads/main`、HEAD と main ref が一致|停止|
|3|tested tip が commit object として存在|停止|
|4|porcelain snapshot を取り、wave path と branch の存在状態を同時分類|不整合なら停止|
|5|wave が main と同じ common git-dir に属し、許可 container 内の linked worktree で、primary でない|停止|
|6|wave record が branch に接続され、record HEAD、wave HEAD、branch ref がすべて tested tip と一致。他 worktree は同 branch を保持しない|停止|
|7|実 cwd と lexical cwd の双方が wave の外|停止|
|8|`git status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none` が空|停止|
|9|`merge-base --is-ancestor <wave-ref> refs/heads/main` が rc=0|停止|
|10|occupancy checker が rc=0、JSON が `unoccupied`、対象 path 一致、occupants/issues/同 UID 観測不能候補なし|停止|
|11|worktree path の inode/binding が preflight 開始時から不変|停止|

I1〜I5 との写像は次のとおりです。

- I1: 6、9、および最終 `branch -d`。branch ref を tested tip に束縛してから ancestry を検査します。
- I2: 検査ではなく実装禁止事項。静的 source 検査と実 argv spy で固定します。
- I3: 5、7、8、10。指定された4条件をすべて含みます。
- I4: cleanup 対象を単数 argv に固定し、対象を回す loop を実装しません。porcelain record の走査は削除 loop ではありません。
- I5: 手順4の状態分類。後述の厳密条件だけで `already-clean` にします。

追加すべき検査は path/common-dir/ref の同一性、SHA の完全一致、別 worktree による branch 使用、symlink/alias、TOCTOU binding です。これらがないと、正しい ancestry を持つ別 branch/worktree を誤って消せます。

落とすべき検査は次の二つです。

- `cleanup-branches` §2 の「HEAD 直近 1h」ヒューリスティック。tested tip と land 後 main ancestry という強い証明があるため不要です。
- main worktree 全体の clean 要求。並行 session の非衝突 dirt を自己撤去の理由にせず、対象 wave のみを検査します。

occupancy checker は走査後に開始する process、別 PID namespace、FD 参照を観測できません。[checker:4-10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_worktree_occupancy.py:4) が明記する残余リスクです。また rc=0 でも `same_uid_cwd_unreachable` があり得るため、cleanup 側では payload も検査して拒否します。

## 4. git 命令と出力解釈

### Identity と state

- `git -C MAIN check-ref-format --branch BRANCH`
  - rc=0 かつ stdout が入力名と同一のときだけ受理。
- `git -C MAIN symbolic-ref --quiet HEAD`
  - `refs/heads/main\n` だけを受理。
- `git -C MAIN rev-parse --verify refs/heads/main^{commit}`
  - full SHA 1 行。HEAD の SHA と一致必須。
- `git -C MAIN cat-file -e TESTED_TIP^{commit}`
  - rc=0 のみ受理。
- `git -C MAIN worktree list --porcelain -z`
  - raw path を NUL 単位で読む。各 record は `worktree`、`HEAD`、`branch` / `detached` / `bare`、任意の `locked` / `prunable` として解析。
  -未知 field、重複 field、欠落 field、同一 path の複数 record は判定不能として拒否。
- `git -C WAVE symbolic-ref --quiet HEAD`
  - `refs/heads/<BRANCH>` の完全一致。
- `git -C MAIN rev-parse --verify refs/heads/<BRANCH>^{commit}`
- `git -C WAVE rev-parse --verify HEAD^{commit}`
  -両方とも tested tip と一致必須。
- `git -C MAIN merge-base --is-ancestor refs/heads/<BRANCH> refs/heads/main`
  - rc=0 は包含、rc=1 は未包含、その他は検査不能。後二者は停止。
- `git -C WAVE status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none`
  - stdout がゼロ byte のときだけ clean。

### `locked` 行

`locked` と `locked <reason>` はどちらも「対象は lock 中」と解釈します。reason は診断用の opaque bytes で、所有権の証明には使いません。

-対象 record に一つだけあれば preflight 後に `git -C MAIN worktree unlock -- WAVE`。
-行がなければ unlock phase は no-op。
- `locked` の重複、対象が `prunable`、既存 directory と record の矛盾は拒否。
- unlock 後に porcelain を取り直し、対象 binding が同一で `locked` が消えたことを確認。

## 5. 撤去順序

採用順は brief の指定どおりです。

1. `git -C MAIN worktree unlock -- WAVE`（locked の場合だけ）
2. `git -C WAVE checkout --detach`
3. status、HEAD、inode、occupancy を再検査
4. shell なしで `rm -rf -- WAVE`
5. `git -C MAIN worktree prune --expire=now`
6. porcelain から対象 record が消えたことを確認
7. branch ref=tested tip と ancestry を再確認
8. `git -C MAIN branch -d -- BRANCH`
9. path、registry record、branch ref がすべて不存在であることを確認

この順序は [cleanup-branches.md:33-35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/.claude/commands/cleanup-branches.md:33) の detach → branch delete → directory delete → prune と食い違います。しかし branch を最後にする方が安全です。`rm` が失敗しても branch が残り、`branch -d` 自身も最後の ancestry 防壁になります。F26 本文の恒久対応も detach → directory delete → prune です。[failures.md:580-582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/failures.md:580)

`worktree remove` と `submodule deinit` は一切使いません。[F26:552-586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/failures.md:552) の二つの事故経路を同時に避けます。

## 6. rc・stdout/stderr・冪等性

推奨契約は次です。

- rc=0、stdout `removed\n`: path、registry、branch の撤去後 postcondition がすべて成立。
- rc=0、stdout `already-clean\n`:厳密な冪等条件が成立。
- rc=2: argparse usage error。
- rc=20: identity / dirt / ancestry / state の preflight 拒否。
- rc=21: occupied。
- rc=22: occupancy 判定不能または payload 不整合。
- rc=30: unlock 以後の mutation/postcondition failure。部分状態の可能性あり。

非 0 では stdout を空にし、stderr を次の一行に固定します。

```text
dev-wave-cleanup: status=<rejected|partial> phase=<phase> reason=<sanitized-reason>
```

`already-clean` は次をすべて満たす場合だけです。

- main の primary/common-dir/main-ref/tested-tip/ancestry 検査が成立。
- wave path が `lexists` でも porcelain record としても存在しない。
- `refs/heads/<wave-branch>` が存在しない。
- path residue、stale/prunable record、branch だけ残存、別 worktree の同 branch は一つでもあれば不成立。

brief の「非 0 = 何も撤去せず」は preflight rc=2/20/21/22 には保証できます。しかし `rm -rf` は途中失敗し得て、成功後の prune / `branch -d` も失敗し得るため、rc=30 まで同じ保証を延ばすのは不可能です。これを隠して `removed` と返すべきではありません。

## 7. テスト設計

一時 repo の正例では次を実体化します。

1. `git init -b main`、user config、base commit。
2. `MAIN/.claude/worktrees/wave` に `git worktree add -b wave/...`。
3. wave commit を作り、main で `merge --ff-only` して land 後状態にする。
4. `git worktree lock` を reason あり/なしで実行。
5. occupancy だけ deterministic な rc=0 fixture に差し替える。
6. cleanup の実 Git unlock、detach、実 directory delete、prune、`branch -d` を通す。
7. path/record/ref の不存在、stdout `removed`、二回目の `already-clean` を確認。

負例は各 preflight を一件ずつ壊し、対象 directory、lock、branch、HEAD が保持されることを確認します。特に ancestry rc=1、dirty tracked/untracked、occupancy rc=1/2、同 UID 観測不能、cwd 内部、primary 指定、別 common-dir、branch/tip 不一致、symlink path、porcelain malformed を分離します。

mutation phase は command runner を偽装し、unlock / detach / rm / prune / branch-delete の各位置で失敗させます。後続命令を呼ばず、rm より前なら directory が残り、rm 以後なら `status=partial` になることを固定します。

submodule 実体化 worktree は作りません。代わりに次の二面で I2 を固定します。

- source AST/text を走査し、git argv に `("worktree", "remove")`、`("submodule", "deinit")`、`("branch", "-D")` が構築されないことを検査。
-全成功・全失敗注入の argv spy で、実行された命令にも同じ subsequence がないことを検査。

## 8. `DW-O25` の逐語案と byte 数

見出しは内容を発見可能にするため変更する案を推奨します。

```markdown
## DW-O25 — ff-only land の全史 provenance・自己撤去関門

D254 に従い、land は `locked_main != tested_tip` のときだけ lock を解放して全史 provenance 監査を自ら走らせ、480 秒以内の rc=0 を必須とする。赤は `RC_PROVENANCE = 29` で main を 1 bit も変えず拒否し、CLI flag・環境変数・警告化の逃がし道を作らない。
lock 再取得後に全検査をやり直し、`tip_sha` / `checker_blob_sha` / `executed_bytes_sha` / `returncode` を束縛した receipt を lock 内で再照合する。`already-landed` の no-op と active fold transaction の recovery では監査を起動しない。
`landed`/`already-landed`後、親は対象外cwdから`tools/dev_wave_cleanup.py`を呼ぶ。占有rc0・clean・非primary・branch=tip・tip⊆mainを全件先に要求し、欠ければ停止する。成功は`removed`/`already-clean`だけ。`worktree remove`/`submodule deinit`は禁止。
```

LF、末尾改行込みの静的計算は次のとおりです。

-現状: 649 bytes。
-見出し増分: 15 bytes。
-追記本文: 296 bytes。
-変更後: **960 bytes**、単節上限 1,000 bytes に対して残り 40 bytes。

[check_docs.py:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:339) の 1,000-byte 上限は変更しません。[`_check_dev_wave_layer_budget`:4781-4788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:4781) が実 section slice を UTF-8 で計測します。

## 9. O25 逐語変更の全連鎖

###直接編集が必要

- [operations.md:165-168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/docs/dev-wave/operations.md:165) —見出し・本文。
- [check_docs.py:577-581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:577) — `DEV_WAVE_DW_O25_SECTION_LITERAL`。
- [check_docs.py:603-610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:603) — `DEV_WAVE_EXACT_VISIBLE_SECTIONS` の見出し key。
- [test_check_docs.py:167-171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:167) — `_SYNTHETIC_DW_O25_SECTION`。
- [test_check_docs.py:797-806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:797) —合成 repo に `tools/dev_wave_cleanup.py` placeholder を追加。
- [test_check_docs.py:6950](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:6950) — exact heading を含む期待 finding。
- [test_check_docs.py:8583-8586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:8583) — exact-section 登録表 assertion。
- [test_check_docs.py:8627-8630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:8627) — raw HTML rejection の heading tuple。
- [test_check_docs.py:8567-8576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:8567) — fixture equalityに加え O25=960 bytes の assertion を追加。

###内容が自動伝播する consumer

- [test_check_docs.py:899-915](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:899) — synthetic reference の構築と O25/O26 の境界調整。
- [test_check_docs.py:6461-6474](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:6461) — O25 reorder mutation。
- [test_check_docs.py:8567-8569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:8567) — production/fixture 同値。
- [test_check_docs.py:8676-8686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:8676) —順序負例。

### ID のみなので変更不要だが確認対象

- [check_docs.py:735-754](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:735) — `REQUIRED_REFERENCE_SECTIONS`。ID は `DW-O25` のままなので変更しない。
- [check_docs.py:5526-5545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/tools/check_docs.py:5526) — O23/O25 順序 pin。ID ベースなので変更しない。
- [test_check_docs.py:194-215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:194) — synthetic ID・dispatch row。新節を作らない限り変更しない。
- [test_check_docs.py:7204-7228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:7204) —登録 section set。
- [test_check_docs.py:7284-7293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:7284) —条件 25 の発火点と対象。

## 10. 既存テストへの影響

`orchestrator/tests/` を節 ID、見出し逐語、tool path、成功語、禁止命令で grep した結果です。

直接更新する既存テストは [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_docs.py:167) だけです。

編集不要だが consumer として確認対象になるものは次です。

- [test_check_worktree_occupancy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_check_worktree_occupancy.py:653) — rc=0/1/2 と payload 契約。
- [test_dev_wave_land.py:3291-3323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_dev_wave_land.py:3291) — `landed` / `already-landed`。
- [test_dev_wave_land.py:4403-4436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_dev_wave_land.py:4403) —成功結果の bit-for-bit 契約。
- [test_dev_wave_land.py:6228-6255](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_dev_wave_land.py:6228) — land 本体が `branch` / `worktree` を呼ばない防壁。cleanup を land 内へ埋め込まない根拠でもあります。
- [test_dev_wave_land.py:6554-6566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_dev_wave_land.py:6554) — CLI stdout JSON。
- [test_wave_land_window.py:1638-1666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-stage9-self-cleanup/orchestrator/tests/test_wave_land_window.py:1638) —両成功語の consumer。

grep で見つかった `test_dev_wave_wait.py`、`test_t139_approval_payload.py`、`test_t793_approval_d291.py` は land helper の参照だけで、cleanup を別 CLI にする限り編集不要です。`test_dev_waves_integration.py`、`test_check_acceptance_reds.py`、`test_mutation_fanout.py` の `worktree remove` は別実行機構のテストで、新 tool の禁止検査とは独立です。

## 11. provisional 判断への攻撃

- P1:厳密には弱い判断です。条件 25 は land 前、cleanup は成功後なので「同一発火点」とは言い切れません。D271 第3条件を文字どおり解釈すれば新 O28 候補は成立します。一方、新条件 row は残 3 byte の command を変更するため I6 と衝突します。O25 を land lifecycle 節として明示的に拡張する裁定が必要です。
- P2:妥当です。§3 の branch 削除順が brief と違うため、そこを dev-wave の実行手順として引用しない方がよいです。
- P3:条件付きで妥当です。親が wave 外 cwd に移り、全 worker が終了し occupancy rc=0 になった場合だけ dogfood します。満たせなければ dogfood を理由に防壁を弱めません。
- P4: tool から scheduler 検査を外す判断は妥当ですが、`git status` は remote job 不在の代替証明ではありません。段 9 の呼び手が全 job の終端を保証する必要があります。
- P5:妥当です。破壊操作、D204、exact docs pin、部分失敗を含むため軽量版には不向きです。

なお brief S4 の failures/decisions fragment は、今回の「作るもの」3項から抜けています。黙って落とさず、段4で scope に戻すか、明示的に別 wave へ分離する必要があります。射影には spool 命名規約が含まれていないため、この plan では fragment path を推測していません。

## 総括

- (a) 実装順序: CLI/porcelain/preflight → mutation/postcondition →一時 repo 回帰 → O25/pin/fixture の同時更新。
- (b) 最大のリスク: `rm -rf` 以後の失敗は部分状態を残し、「非0なら何も撤去されていない」を保証できないこと。
- (c) 段4裁定: O25 を land lifecycle として拡張するか O28 を新設するか、および partial failure を rc 契約へ正直に出すかを択一する。