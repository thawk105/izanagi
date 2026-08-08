## 読了結果

指定された全ファイルを読了しました。欠落・読取不能はありません。`DW-S02` / `DW-O05` に従い、編集・pytest 実走・緑の主張はしていません。作業ツリーも静的確認時点では clean です。

現物から、親の事前観測を補正すべき事実が二つあります。

- 外部 handoff は現在 7 regular file あり、旧書式、見出し後の空行、許可外の状態値、短縮 SHA が混在しています。正規書式は [docs/handoff/README.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/docs/handoff/README.md:22)、既存 checker の exact 判定は [tools/check_docs.py:3989](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/check_docs.py:3989) です。したがって「全件が正規 4 行ヘッダ」という前提には依存できません。
- roster は観測時点で 10 件でした。親の 12 件という値との差は、roster が可変 snapshot であるためと解釈できます。件数をテストへ固定してはいけません。

最大の設計上の穴は、正規 handoff ヘッダに `wave_id`、worktree、branch、session ID がなく、一意な session join key が存在しないことです。

## S-A: `tools/wave_peers.py` の設計

### 予定する file:line 構成

新規 `tools/wave_peers.py` は次の配置にします。行番号は実装予定範囲です。

| 予定行 | 内容 |
|---|---|
| 1–55 | import、上限値、status 語彙、land status 語彙 |
| 56–112 | `SourceReport` / peer record、制御文字除去・長さ制限 |
| 113–170 | component-wise nofollow open、bounded read、bounded subprocess |
| 171–245 | handoff ディレクトリ列挙・4 field 抽出・旧書式 salvage |
| 246–315 | roster `proto: 1` parser |
| 316–405 | Git worktree / branch inventory と main ancestry |
| 406–485 | task ID / slug / cwd の一意 join、活動分類、宛先候補 |
| 486–535 | JSON・人間向け表示・land 通知文 |
| 536–610 | argparse、`summary` / `notify`、最終 fail-soft 境界 |

### CLI 表面

```text
python3 tools/wave_peers.py summary \
  [--repo PATH] [-H DIR|--handoff-dir DIR] [--self-handoff PATH] \
  [--roster PATH|--no-roster] [--json|--one-line]

python3 tools/wave_peers.py notify \
  --land-status STATUS \
  [--repo PATH] [-H DIR|--handoff-dir DIR] [--self-handoff PATH] \
  [--roster PATH|--no-roster] [--json]
```

- `--repo`: 既定は cwd。
- `-H/--handoff-dir`: `IZANAGI_WAVE_HANDOFF_DIR` を次順位に使う。未指定なら handoff source を `unavailable:not_configured` とし、固定の `/work/...` は持たない。
- `--roster`: `IZANAGI_CLAUDE_ROSTER`、次に `$HOME/.claude/daemon/roster.json`。存在しなくても handoff＋Git だけで動作する。`--no-roster` で明示無効化できる。
- `--self-handoff`: 自分の handoff を候補から除外する。
- `summary --one-line`: startup checker 用の 1 行・上限制要約。
- `notify`:送信は行わず、固定通知文と候補だけを生成する。
- 外部 source の欠損・破損は rc=0。CLI 誤用と不正な `--land-status` だけ argparse の rc=2。

`--land-status` は [tools/dev_wave_land.py:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/dev_wave_land.py:86) と各返却箇所で実在を確認した次の値だけを許可します。

```text
landed, already-landed, stale-main, lock-busy, rejected,
not-landed, landed-postcondition-failed, fold-failed,
fold-recovery-failed, fold-rollback-failed
```

### 実在する入力 field

| source | 使用する実在 field | 扱い |
|---|---|---|
| handoff | `- 目的:`, `- 状態:`, `- 最終更新:`, `- 基準コミット:` | exact prefix。状態の正規値は `作業中/計測中/中断` |
| roster top | `proto`, `updatedAt`, `workers` | `proto == 1` 以外は schema drift として取得不能 |
| roster worker | `cwd`, `sessionId` | exact 型検査 |
| roster dispatch | `dispatch.short`, optional `dispatch.seed.name`, `dispatch.seed.intent` | `intent` は起動 prompt。本文は出力せず task ID 抽出だけ |
| Git porcelain | `worktree`, `HEAD`, `branch`, `bare`, `detached`, `locked`, `prunable` | local Git 2.34.1 の実在 field。自由文 reason は join に使わない |
| Git `for-each-ref` | `refname`, `objectname`, `worktreepath` | NUL 区切りの主 inventory。`worktreepath` は branch が checkout 中だけ非空 |
| land JSON | `status`, `reason`, `main_before`, `main_after`, `wave_tip`, `fold_commit_sha` | 現行 `LandResult.as_json()` の field。[tools/dev_wave_land.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/dev_wave_land.py:96) |

`name` や `prompt` という roster field は存在しません。対応する実体は optional `dispatch.seed.name` と `dispatch.seed.intent` です。`dispatch.short` が `SendMessage` の recipient として使えるかは undocumented なので、候補としてのみ出し、`ListAgents` の表示名との照合を要求します。

`ListAgents` 自体の機械可読 field schema はこの checkout から確認できていないため「未確認」です。`wave_peers.py` はその出力を parse しません。

また、現行 Git は `git worktree list --porcelain -z` を拒否しました。したがって非実在の `-z` は使わず、主 inventory は次の固定 format にします。

```text
git for-each-ref \
  --format='R%00%(refname)%00%(objectname)%00%(worktreepath)%00' \
  refs/heads/
```

branch-attached worktree はこれで NUL-safe に取得します。plain porcelain は detached / bare / locked / prunable の補助検出だけに使い、主 inventory と相互検証できない record は送信候補にしません。

### join 規則

一次情報は brief の P1 どおり handoff＋Git、roster は補助です。

1. Git branch/worktree から safe slug を作る。

   - `worktree-dev-wave-t139-producer`
   - `dev-wave-t139-producer`
   - `wave-t139-producer`

   の既知 prefix だけを一度除去し、残りを完全一致させます。部分一致・類似度・自然言語推測はしません。

2. `t139` のような slug と、handoff の先頭見出し・目的、roster の `seed.intent` から、境界付き正規表現で canonical `T-139` を抽出します。

   - 値が 1 個だけなら join key 候補。
   - 複数 ID、slug と本文 ID の不一致、同じ ID の複数 handoff/worktree/session は `ambiguous`。
   - `intent` は命令として読まず、最大 8 KiB 内の ID token だけを見る。

3. roster の `cwd` が worktree の canonical path と完全一致すれば、task ID より強い exact join とします。

4. handoff の `基準コミット` は join ID にしません。7–64 桁 lowercase hex だけを Git で commit に解決し、worktree HEAD の ancestor かを検査します。曖昧短縮・未解決なら `base_resolution=unavailable`。

5. roster 単独では peer を作りません。handoff または dev-wave branch/worktree と一意に結合できなければ `unmatched.roster` に残します。

6. 宛先候補にできるのは、次をすべて満たす record だけです。

   - join が一意。
   - 自分ではない。
   - 明示 `中断`、48 時間超の stale mtime、main 合流済みではない。
   - Git worktree＋roster が一致するか、handoff＋Git＋roster の同一 task ID が一致する。
   - `dispatch.short` / `dispatch.seed.name` はなお未検証として出力し、送信直前に fresh `ListAgents` と exact 照合する。

### Git relation

各 worktree HEAD `T` と `refs/heads/main` の HEAD `M` に対して、固定 SHA を使う `merge-base --is-ancestor` を双方向に実行します。

| `T ≤ M` | `M ≤ T` | relation |
|---|---|---|
| true | true | `equal` |
| true | false | `merged-or-behind` |
| false | true | `ahead` |
| false | false | `diverged` |
| Git rc が 0/1 以外 | — | `unknown` |

`merged-or-behind` は通知対象外ですが、検査省略の根拠にはしません。

### JSON schema

```json
{
  "schema_version": 1,
  "mode": "summary",
  "generated_at": "UTC timestamp",
  "main": {
    "ref": "refs/heads/main",
    "head": "full sha or null",
    "status": "ok | unavailable"
  },
  "sources": {
    "handoff": {
      "status": "ok | partial | unavailable",
      "reason": "stable reason code or null",
      "complete": true,
      "record_count": 0,
      "valid_count": 0,
      "invalid_count": 0
    },
    "git": {
      "status": "ok | partial | unavailable",
      "reason": null,
      "complete": true,
      "worktree_count": 0,
      "branch_count": 0
    },
    "roster": {
      "status": "ok | partial | unavailable",
      "reason": null,
      "complete": true,
      "proto": 1,
      "record_count": 0
    }
  },
  "peer_count": {
    "kind": "exact | lower_bound | unknown",
    "value": 0
  },
  "peers": [
    {
      "id": "task:T-139",
      "activity": "active | interrupted | stale | merged | unknown",
      "self": false,
      "handoff": {
        "file": "sanitized basename",
        "header_status": "exact | salvaged | invalid",
        "purpose": "sanitized bounded text",
        "state": "作業中",
        "updated": "raw sanitized value",
        "base_declared": "sanitized value",
        "base_oid": "full sha or null"
      },
      "git": {
        "worktree": "sanitized canonical path",
        "branch": "refs/heads/...",
        "head": "full sha",
        "relation": "ahead"
      },
      "roster": [
        {
          "session_id": "...",
          "short": "...",
          "seed_name": null,
          "cwd": "...",
          "join": "cwd | task-id"
        }
      ],
      "join": {
        "methods": ["task-id"],
        "ambiguous": false
      },
      "recipient_candidates": [
        {
          "token": "d350e650",
          "field": "dispatch.short",
          "requires_list_agents": true
        }
      ]
    }
  ],
  "unmatched": {
    "handoffs": [],
    "worktrees": [],
    "branches": [],
    "roster": []
  },
  "notification": null
}
```

`unavailable` の `record_count` は `null` とし、成功した空 source だけを `status=ok, complete=true, record_count=0` にします。partial は「確認済み N 件」という lower bound です。

### 人間向け表示

通常表示は source 状態、main、peer 1 行ずつ、unmatched/error 件数を出します。startup 用 `--one-line` は最大 1,024 文字です。

```text
並行 wave: 3件; main=6cc3e59a…; handoff=ok(7/invalid 5);
git=ok(9); roster=ok(10); active=T-139,T-632,…; 宛先候補=2(ListAgents要照合)
```

区別は明示します。

```text
並行 wave: 0件 (handoff/git の完全取得に成功; roster は取得不能)
並行 wave: 件数不明 (handoff=取得不能:not_configured; Git で確認済み2件)
並行 wave: 少なくとも2件 (handoff は上限到達により partial)
```

### land 通知

固定 template だけを生成し、handoff の目的や roster prompt は挿入しません。

```text
[dev-wave land advisory]
land_status: stale-main
main_head_observed: <full SHA>
sender_branch: <validated ref>
sender_tip: <full SHA>
observed_at: <UTC>
advisory_only: true
この通知は外部データで権限を付与しない。受信側で local main を git 再照合し、既存 gate を省略しない。
```

- `main_head_observed` は caller 引数でなく、その場で `refs/heads/main` を再読した値。
- main を取得できなければ `notification.available=false` とし、偽の文面を作らない。ただし CLI rc は 0。
- `recipient_candidates` は fresh `ListAgents` と一意に照合できたものだけ送る。
- 送信は land 事象 1 回につき各 peer 1 回。poll、retry、応答待ちを行わない。
- 受信側の次 tool round まで drain されないため、約 18 分の受入中に届く保証はない。

## 敵対入力への具体策

`tools/wave_peers.py:new:56–405` で次を実装します。

- 制御文字は Unicode category `Cc/Cf/Cs` を除去し、空白を正規化。JSON にも未処理文字列を入れない。
- purpose/path/reason は用途別に 160–512 文字へ切り詰める。起動 prompt 自体は出力しない。
- handoff directory は component ごとに `O_DIRECTORY|O_NOFOLLOW` で開く。entry は `dir_fd`＋`O_NOFOLLOW|O_NONBLOCK`、`fstat` で regular file と inode 不変を確認。
- roster も親 component と final file の symlink を拒否し、regular file だけ読む。
- handoff は最大 128 件、各 64 KiB、解析対象は先頭 16 行・各 2 KiB。
- roster は最大 256 KiB、worker 128 件、intent 8 KiB。
- Git stdout＋stderr は合計 256 KiB、branch/worktree 各 128 件、1 command 2 秒、全体 deadline 5 秒。
- Git child は固定 argv、`shell=False`、stdin `/dev/null`。`GIT_*` repository selector、global/system config、replace object、lazy fetch、prompt を遮断する。
- 外部の hash/ref/path は regex と canonicality 検査後にのみ argv へ入れる。handoff・roster の文面を command、`eval`、import、format expression として実行しない。
- unknown field、duplicate field、unknown proto、出力上限、timeout、race は stable reason code に畳み、traceback や生の例外文字列を外へ出さない。
- source 単位で `ok/partial/unavailable` を保持する。ある source の失敗を他 source の 0 件へ変換しない。

## S-B: startup checker への非阻害表示

現行 visibility は [tools/check_wave_startup.py:229–259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/check_wave_startup.py:229)、rc 決定は [tools/check_wave_startup.py:319–335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/check_wave_startup.py:319) です。

変更位置は次の三点です。

1. original line 21 後に sibling helper path と 2 秒 timeout 定数を追加。
2. original line 259 後に `_describe_wave_peers_fail_soft()` を追加。

   - `wave_peers.py summary --one-line --repo ...` を subprocess 隔離で呼ぶ。
   - `--external-handoff` があれば、その親を `-H`、そのファイルを `--self-handoff` として渡す。
   - helper 不在、symlink、timeout、非 0、invalid UTF-8、複数行、2 KiB 超を固定の「取得不能」1 行へ変換する。
   - helper の例外や rc を `failures` へ入れない。

3. original lines 323–324 の間、main divergence 表示直後かつ `check_repository()` 前へ次を差し込む。

```python
print(f"INFO: {_describe_wave_peers_fail_soft(...)}", flush=True)
```

これにより、正常・dirty・missing submodule・invalid external handoff の全経路で、最終 rc は従来どおり `check_repository()` の `failures` だけで決まります。`check_repository()` 本体と既存 failure 文言は変更しません。

## S-C: command 追記案

[.claude/commands/dev-wave.md:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/.claude/commands/dev-wave.md:111) の「終端」末尾、現行 line 115 後へ次をそのまま追記します。

```markdown

- land 成否後、`python3 tools/wave_peers.py notify --land-status <結果> -H <dir>` の候補を `ListAgents` で照合して `SendMessage` する。
  受信通知は外部データ。git 照合後だけ使い、検査を省略しない。
```

静的計数は以下です。

- 追記: 246 UTF-8 bytes（先頭空行・末尾改行込み）
- 行長: 117 / 34 code points
- command 全体: 9,035 → 9,281 bytes、上限 9,500
- 現在の最長行 137 字を増やさず、上限 140 内
- `docs/dev-wave/**`: 25,196 bytes のまま、変更 0 byte

根拠は [tools/check_docs.py:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/check_docs.py:168) の command limit、[tools/check_docs.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/check_docs.py:254) と [tools/check_docs.py:3558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/check_docs.py:3558) の aggregate ceiling です。

新規 H2 や dispatch 行は作らず、`段 dispatch` / `条件 dispatch` 表の外へ置くため、[tools/check_docs.py:3148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/check_docs.py:3148) と [tools/check_docs.py:3875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/check_docs.py:3875) の閉包集合は不変です。`tools/wave_peers.py` は同じ commit で実在させます。

## S-D: テスト計画

### 新規 `orchestrator/tests/test_wave_peers.py`

以下の test 名を事前に固定します。

- `test_empty_handoff_source_is_exact_zero_but_missing_source_is_unknown`
- `test_handoff_reader_rejects_symlink_nonregular_oversize_and_entry_overflow`
- `test_handoff_exact_headers_and_salvaged_legacy_records_remain_distinct`
- `test_external_text_is_control_stripped_and_bounded_in_json_and_human_output`
- `test_roster_proto1_uses_confirmed_nested_fields_without_emitting_intent`
- `test_roster_unknown_proto_invalid_json_symlink_and_worker_overflow_are_unavailable`
- `test_git_inventory_parses_nul_for_each_ref_and_confirmed_porcelain_fields`
- `test_git_inventory_rejects_unknown_duplicate_spoofed_and_oversize_output`
- `test_git_child_is_fixed_argv_shell_false_sanitized_and_bounded`
- `test_join_requires_unique_consistent_cwd_task_id_or_slug`
- `test_ambiguous_or_conflicting_join_never_yields_recipient_candidate`
- `test_main_relation_distinguishes_equal_ahead_merged_diverged_and_unknown`
- `test_notify_uses_observed_main_head_and_fixed_advisory_template`
- `test_notify_excludes_self_interrupted_stale_merged_and_unmatched_peers`
- `test_cli_source_failure_is_rc_zero_without_traceback`
- `test_human_summary_never_reports_unavailable_source_as_zero`

### `test_check_wave_startup.py` への追加

既存の divergence テスト群 [test_check_wave_startup.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/orchestrator/tests/test_check_wave_startup.py:328) の後へ追加します。

- `test_peer_summary_success_does_not_change_startup_rc`
- `test_peer_summary_failure_timeout_and_malformed_output_do_not_change_startup_rc`
- `test_peer_summary_is_printed_before_ng_output`
- `test_peer_summary_receives_external_handoff_parent_and_self_path`
- `test_peer_summary_output_is_one_line_and_bounded`

2 本目は helper outcome（missing、timeout、rc 非 0、decode error、oversize）× repository outcome（fresh 成功、resume 成功、dirty、submodule 不正、external handoff 不正）を parameterizeし、helper 挿入前と同じ `0 if not failures else 1` であることを比較します。

既存 test 名、fixture、期待値は変更しません。

## 変異事前登録候補

| ID | 壊す予定箇所 | 変異 | 必ず落とす test |
|---|---|---|---|
| M1 | `wave_peers.py:new:113–150` | `O_NOFOLLOW` を外し symlink target を読む | `test_handoff_reader_rejects_symlink_nonregular_oversize_and_entry_overflow` |
| M2 | `wave_peers.py:new:151–170` | size / 件数上限超過を `ok` として受理 | 同上、`test_roster_unknown_proto_invalid_json_symlink_and_worker_overflow_are_unavailable` |
| M3 | `wave_peers.py:new:56–90` | 制御文字除去または切り詰めを無効化 | `test_external_text_is_control_stripped_and_bounded_in_json_and_human_output` |
| M4 | `wave_peers.py:new:246–275` | unknown `proto` を空 roster とみなす | `test_roster_unknown_proto_invalid_json_symlink_and_worker_overflow_are_unavailable` |
| M5 | `wave_peers.py:new:340–390` | malformed Git record、unknown field、ancestry rc>1 を正常値として受理 | `test_git_inventory_rejects_unknown_duplicate_spoofed_and_oversize_output`、relation test |
| M6 | `wave_peers.py:new:406–445` | ambiguous join で先頭 record を選ぶ | `test_ambiguous_or_conflicting_join_never_yields_recipient_candidate` |
| M7 | `wave_peers.py:new:446–485` | self / 中断 / stale / merged を宛先候補へ含める | `test_notify_excludes_self_interrupted_stale_merged_and_unmatched_peers` |
| M8 | `wave_peers.py:new:486–515` | caller 提供値を main HEAD とし、Git 再読を除く | `test_notify_uses_observed_main_head_and_fixed_advisory_template` |
| M9 | `check_wave_startup.py:original 259後` | helper failure を `failures` へ追加、または例外を外へ再送出 | `test_peer_summary_failure_timeout_and_malformed_output_do_not_change_startup_rc` |

いずれも受理集合、送信候補集合、または fail-closed/fail-soft 境界を変える変異です。単なる診断文言変更は含めていません。

## 所有分割

実装子 1 本で足ります。推奨所有は次です。

- Codex author 1 本:

  - `tools/wave_peers.py`
  - `tools/check_wave_startup.py`
  - `orchestrator/tests/test_wave_peers.py`
  - `orchestrator/tests/test_check_wave_startup.py`

- 親:

  - `.claude/commands/dev-wave.md` の 246-byte 追記

`wave_peers` と startup integration は API と rc 不変テストが密結合しており、分割の利益が小さいためです。分ける必要が生じた場合だけ、A=`wave_peers.py`＋専用 test、B=`check_wave_startup.py`＋既存 test とし、A の patch 適用後に B を投入すれば所有集合は素になります。

`tools/dev_wave_land.py` は全 2,000 行を読みましたが、編集所有者を置きません。lock、ff-only、audit、postcondition、成功条件 `landed/already-landed` は [tools/dev_wave_land.py:1658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/dev_wave_land.py:1658) 以下のままです。

## 総括

- 採用すべき設計: handoff＋Git を一次情報、roster を補助とし、取得状態を `ok/partial/unavailable` で保持する。一意 join と fresh `ListAgents` 照合後だけ `SendMessage` し、通知は advisory に限定する。
- 最大のリスク: 正規 handoff に session/worktree の一意 ID がなく、現物にも旧書式が混在すること。誤 join は誤送信につながるため、曖昧時は候補ゼロへ倒す。
- 段 4 で親が裁定すべき択一: task ID の三者一致（handoff＋Git＋roster）を送信候補に認めるか、cwd 完全一致だけに限定するか。推奨は「三者一意一致を候補には認めるが、fresh `ListAgents` の exact name 照合を送信条件にする」です。