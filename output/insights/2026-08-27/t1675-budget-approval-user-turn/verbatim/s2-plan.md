## 現況

- `BUDGET_APPROVAL_SHA256` は現在 `None` で、HEAD と worktree の双方に assignment は 1 件だけ存在する。`orchestrator/campaign/s8b_holdout_freeze.py:50-52`
- `_budget_approval_authority()` は入力を読む前に `None` を拒否する。したがって現状の草案だけでは gate は必ず閉じる。`orchestrator/campaign/s8b_holdout_freeze.py:1297-1304`
- 承認 loader は固定 path、raw SHA-256、exact key 集合、canonical JSON、固定 scope、非空承認者、canonical UTC timestamp、budget schema の全てを要求する。変更または緩和しない。`orchestrator/campaign/s8b_holdout_freeze.py:1307-1339`
- budget は exact 3 key、`oracle_shared=true`、有限非負数、active holdout と完全一致する `per_holdout_bench_s` を要求する。`orchestrator/campaign/s8b_holdout_freeze.py:57-60,1267-1294`
- active v1 と実装上の holdout 集合は `rr20`, `rr80`。candidate builder も active v1 が実装集合と一致することを再確認する。`orchestrator/campaign/s8b_holdout_freeze.py:100-103,1703-1707`
- 既存 fixture は別 budget 文書を `output/s8b-freeze-budget-inputs/g1.json` に作り、同じ budget object を承認 JSON に埋め、承認 raw hash を返している。`orchestrator/tests/s8b_v2_freeze_fixture.py:463-493`
- candidate builder は承認とは別に `--budget` 文書を読み、両者を canonical bytes で比較する。整数と浮動小数点の表記差も拒否される。`orchestrator/campaign/s8b_holdout_freeze.py:1712-1719`、`orchestrator/tests/test_s8b_holdout_freeze.py:1909-1926`
- `None` pin の先行拒否は既に missing input と valid fixture の両方でテスト済みである。`orchestrator/tests/test_s8b_holdout_freeze.py:1597-1611,1955-1967`
- 実 repo の `output/` snapshot は `rglob("*")` の全 entry から Git ignore 対象だけを除く。ignored subtree 内でも tracked path は再び Git-visible になる。`orchestrator/tests/output_snapshot_ignores.py:227-293,330-341`、`orchestrator/tests/test_real_repo_serialization.py:581-611`
- `FROZEN_MANIFEST` は exact 23 path だけで、承認 path と budget input path は含まれない。新規 draft を自動的に凍結対象へ加える仕組みでもない。`orchestrator/tests/test_frozen_artifacts.py:41-88,90-151,234-248`
- 数値根拠は 2592/1296 を planning scale、2400/1200 を余裕ゼロとしており、双方とも operational approval には非推奨である。`output/insights/2026-08-24_t986-budget-approval-package/README.md:11-25,156-165,225-238`
- 既存 CLI の作法は argparse の入力不正を code 2、処理失敗を code 1、成功を code 0 とする形である。create-only/no-follow の実装例もある。`tools/hold_inventory.py:236-251`、`tools/issue_env_contract_activation.py:27-43,46-141,156-233`

## プラン

### 変更単位 A: ratify CLI

`tools/s8b_budget_approval.py` を新規追加する。

- `tools/s8b_budget_approval.py:1-45` 追加  
  repo 固定 root、承認固定 path、budget input 固定 path、draft schema、T986 dossier path と SHA-256、pin の旧行と置換形式を定義する。`--root`、任意 approval path、任意 source path は公開しない。

- `tools/s8b_budget_approval.py:47-105` 追加  
  active v1 を固定 path から no-follow で読み、builder と同じ raw hash、schema、holdout 集合を確認する。数値は canonical JSON number の字句として解析し、bool、非有限、負数、負のゼロ、非 canonical 表記を拒否した後、既存 `_validate_budget()` に通す。

- `tools/s8b_budget_approval.py:107-165` 追加  
  `draft --out PATH` を実装する。出力は repo 外の既存 directory に create-only で作る。draft の exact schema は `schema/status/authority/scope/evidence/ratification_requirements` とし、`approver`、`approved_at`、`budget` の各 approval fieldを持たせない。予算値も持たせず、T986 dossier の tracked path と SHA-256、入力が必要な field 名だけを載せる。

- `tools/s8b_budget_approval.py:167-225` 追加  
  `ratify` は `--total-bench-s`、holdout ごとの反復 `--per-holdout-bench-s ID=VALUE`、`--approved-at` を全て必須とし、既定値を置かない。holdout 引数は active v1 の集合と exact 一致させ、重複も拒否する。

- `tools/s8b_budget_approval.py:227-275` 追加  
  承認者は argv、環境変数、draft から受け取らず、controlling TTY から直接読む。空白だけ、前後空白、制御文字を拒否する。canonical budget と canonical approval raw、approval SHA-256 を TTY に表示し、ユーザーに `RATIFY <approval-sha256>` の exact 入力を要求する。stdout や非 TTY からの代用は認めない。

- `tools/s8b_budget_approval.py:277-355` 追加  
  budget raw は `_canonical_bytes(budget)`、approval raw は `_canonical_bytes({approved_at,approver,budget,scope})` とし、いずれも末尾 newline を付けない。budget input、canonical approval の順に固定 pathへ create-only/no-follow で発行し、pin は最後に更新する。途中停止時は pin が `None` のため gate は閉じたままになる。同じ bytes の部分発行は再開可能、異なる既存 bytes は拒否する。

- `tools/s8b_budget_approval.py:357-425` 追加  
  pin 更新前に ratify CLI 自身と `s8b_holdout_freeze.py` がそれぞれ HEAD blob と一致することを確認する。source 内で次の旧 anchor が exact 1 件、かつ同名 assignment 行も 1 件だけであることを確認する。

  ```python
  BUDGET_APPROVAL_SHA256: Optional[str] = None
  ```

  置換先は次の 1 行だけとする。

  ```python
  BUDGET_APPROVAL_SHA256: Optional[str] = "<approval raw の 64hex sha256>"
  ```

  同一 directory の staging file、元 inode と bytes の再確認、mode 保持、fsync、atomic replace を使う。ratify は commit、stage、candidate 生成を行わない。

- `tools/s8b_budget_approval.py:427-475` 追加  
  argparse 不正は code 2、TTY 不在、確認不一致、既存 file 不一致、source drift、anchor 不一致は code 1、成功は code 0。成功時は変更した exact 3 path と「未 commit、candidate 未生成」を表示する。

本 wave の commit では `orchestrator/campaign/s8b_holdout_freeze.py:52` を変更しない。変更が生じるのは、land 後にユーザーが ratify を明示実行した時だけである。

### 変更単位 B: テスト

`orchestrator/tests/test_s8b_budget_approval.py` を新規追加する。

- `:1-90`  
  canonical number parser、重複 holdout、欠落 holdout、余分な holdout、bool、非有限、負数、負のゼロを検査する。`rr20`, `rr80` の期待値は active v1 fixture から導出する。

- `:92-155`  
  draft の exact key 集合を検査し、approval の 4 key を持たないこと、数値値を含まないこと、`draft --approver`、`draft --total-bench-s`、`--root` が argparse code 2 になることを固定する。

- `:157-220`  
  draft 実行前後で source bytes、canonical approval path、budget input path が不変であることを検査する。repo 内 `--out`、canonical approval path、既存 leaf、symlink leaf を拒否する正例付きテストを置く。

- `:222-270`  
  draft raw を capture mock から loader に渡し、`approval_sha256` にはその raw の正しい hash を明示する。それでも approval exact key 集合不一致で拒否されることを検査する。これにより `None` pin の先行拒否を迂回した状態でも draft bytes 自体が authority にならないことを固定する。

- `:272-355`  
  ratify の全数値引数が必須で既定値がないこと、`--approver` が存在しないこと、TTY 不在または確認文字列不一致では approval、budget、source の全てが未変更であることを検査する。

- `:357-455`  
  temporary repo の HEAD に未批准 source と CLI を置き、fake TTY から人間名と exact hash 確認を供給する。ratify 後に変更 path が source、canonical approval、budget input の 3 件だけであること、HEAD が不変で commit がないことを検査する。

- `:457-535`  
  approval raw hash が source pin と一致し、`_load_budget_approval()` が受理し、standalone budget raw が `_canonical_bytes(approval["budget"])` と byte exact 一致することを検査する。

- `:537-610`  
  source が HEAD と不一致、pin が既に別 hash、旧 anchor が 0 件または 2 件、approval/budget が異なる既存 bytes、途中発行後の exact 再開を検査する。各失敗で pin が開かないことを確認する。

既存 `orchestrator/tests/test_s8b_holdout_freeze.py:1597-1611,1955-1967` は変更しない。既存 fixture `orchestrator/tests/s8b_v2_freeze_fixture.py:463-493` も正例として再利用し、便宜値 100/50 を実運用既定値へ昇格させない。

### 変更単位 C: 読解導線

親所有で `docs/s8b-budget-approval-user-turn.md` を新規追加する。

- `docs/s8b-budget-approval-user-turn.md:1-30`  
  T986 dossier `:11-25,225-238` を先に読むこと、現時点の推奨が保留であること、draft が authority を持たないことを明記する。

- `docs/s8b-budget-approval-user-turn.md:31-60`  
  repo 外 job dir への `draft --out`、ユーザー選択値を placeholder にした ratify の 1 コマンド例、TTY 上の canonical bytes と hash 確認を記載する。2592/1296 や 2400/1200 をコマンド既定値または copy-ready command にしない。

- `docs/s8b-budget-approval-user-turn.md:61-90`  
  ratify 後に exact 3 path の diff を人間が確認し、commit は人間が別途行うこと、candidate 生成は別手番で `--budget output/s8b-freeze-budget-inputs/g1.json` を渡すことを記載する。

## 論点の判定

### 1. P1: 承認 pin の更新主体

結論は、ratify による直接更新を採用してよい。ただし固定 source の exact 1 行だけを、ユーザーの TTY 確認後、approval と budget の発行後に更新する条件付きである。

現在の authority は source 定数だけであり、`None` のままでは固定 path に正しい承認を置いても必ず拒否される。`orchestrator/campaign/s8b_holdout_freeze.py:52,1297-1304`。したがって source を一切変更しない設計では gate を確定できない。

直接更新を許す根拠は、間接 patch emitter も結局は同じ 1 行と approval bytes を生成でき、改変済み emitter に対する攻撃面は消えないためである。安全境界は、land 済み CLI 自身の HEAD 一致、TTY からの承認者入力、canonical raw hash の exact 確認、固定 3 path、pin-last、commit しないことに置く。

現時点で確認した exact anchor は `orchestrator/campaign/s8b_holdout_freeze.py:52` の 1 件だけである。実行時にも `tools/s8b_budget_approval.py:357-425` で次を再確認する。

- worktree source bytes が HEAD blob と exact 一致
- 旧 anchor の byte count が 1
- `^BUDGET_APPROVAL_SHA256...$` assignment 行が 1
- 置換後に旧 anchor が 0、新 hash 行が 1
- それ以外の source bytes が不変

直接更新を採らない場合は、`tools/s8b_budget_approval.py:277-355` を unified patch emitter に置き換え、`docs/s8b-budget-approval-user-turn.md:45-55` に次の単一 pipeline を載せれば「1 コマンド」は満たせる。

```bash
python3 tools/s8b_budget_approval.py ratify <全数値引数> --approved-at <UTC> --emit-patch | git apply -
```

ただしこれは ratify 自身が書かないだけで、ratify が trust-root edit を生成する点は同じである。stdout と TTY の分離、patch 生成と適用の障害点も増えるため、本案では採用しない。

### 2. P2: 草案の置き場所

草案 instance は tracked file にせず、`draft --out` で repo 外 job dir に create-only 生成する。

tracked draft を `output/` に追加すると、非 ignored path はそのまま `rglob` の母集合に入り、ignored subtree 内でも tracked path は `git_visible_paths` として除外を解除される。`orchestrator/tests/output_snapshot_ignores.py:227-293,330-341`。実 repo snapshot はその集合全体の mode、size、mtime、ctime を比較するため、安定した追加だけで即失敗するとは限らないが、比較対象の母集合は確実に増える。`orchestrator/tests/test_real_repo_serialization.py:581-611,614-677,1019-1038`

`docs/` の手順書は `output/` snapshot の対象外である。読解導線は tracked docs から T986 dossier と外部 draft の再生成コマンドへ結ぶ。draft instance を失っても同じ CLI で再生成できる。

`FROZEN_MANIFEST` は exact 23 件のままとし、draft、approval、budget input を追加しない。`orchestrator/tests/test_frozen_artifacts.py:41-151,234-248`

### 3. P3: 数値の束縛

ratify は全数値を必須引数で受け、既定値を一切持たない。draft も数値値を保持しない。

CLI source に 2592、1296、2400、1200 を候補値として埋め込まない。ユーザーは T986 dossier の「保留推奨」と限界を読んだうえで値を入力する。`output/insights/2026-08-24_t986-budget-approval-package/README.md:11-25,225-238`

確認時には次を TTY に表示する。

- canonical budget raw
- approval 全 field
- approval raw SHA-256
- T986 dossier の path と SHA-256
- exact 確認文字列 `RATIFY <approval-sha256>`

同じ budget object から approval 埋込みと standalone budget raw を生成する。`budget_raw == _canonical_bytes(approval["budget"])` を ratify 自身とテストで検査するため、`build_v2_g1_candidate()` の canonical comparison と一致する。`orchestrator/campaign/s8b_holdout_freeze.py:1712-1719`

ソフトウェアは actor が AI か人間かを暗号学的には識別できない。固定できるのは、draft や非対話引数から承認者が流入しないこと、数値に既定値がないこと、controlling TTY で人間が exact bytes hash を確認することまでである。

### 4. 負例テスト

「pin が `None` なら草案だけで開かない」を追加するだけでは、既存 `orchestrator/tests/test_s8b_holdout_freeze.py:1597-1611,1955-1967` と重複する。これは新しい防壁とは申告しない。

代わりに新しく pin する性質は次の 2 点である。

- draft route は approval key、予算値、承認者入力 surfaceを持たず、source と canonical artifacts を変更できない。draft へ `approver` を追加する mutant、draft から ratify writer を呼ぶ mutant、repo 内出力を許す mutant が赤になる。`orchestrator/tests/test_s8b_budget_approval.py:92-220`
- `None` gate をテスト内で使わず、draft raw の正しい SHA-256 を loader へ明示しても exact approval schema 不一致で拒否される。capture mock を使うため草案を canonical path へ置かない。これが既存テストにない新しい固定点である。`orchestrator/tests/test_s8b_budget_approval.py:222-270`

「AI が承認者欄を埋められない」は、draft exact schema、`--approver` 不在、非 TTY refusal で検査する。AI と人間の主体判定そのものをテストできるとは主張しない。

### 5. 別 budget 文書

`output/s8b-freeze-budget-inputs/g1.json` を承認と同じユーザー ratify 手番で生成する。

AI の draft 手番では作らない。ユーザーが明示した数値から、ratify が次の 3 つを同時に準備する。

1. standalone canonical budget
2. 同じ object を埋め込んだ canonical approval
3. approval raw hash を束縛した source pin

後続手番では `generate-v2-candidate --budget output/s8b-freeze-budget-inputs/g1.json` とする。builder が `orchestrator/campaign/s8b_holdout_freeze.py:1712-1719` で再検証する。fixture の同型構造は `orchestrator/tests/s8b_v2_freeze_fixture.py:463-493` にある。

## risk

- ratify は tracked production source を変更する。source または CLI が HEAD と不一致なら全面拒否し、ユーザーの既存変更を上書きしない。
- 3 file を完全には単一 filesystem transaction にできない。budget、approval、pin の順にし、部分状態では pin を最後まで `None` に保つ。exact 同一 bytes だけ再開可能にする。
- source pin 更新直後も、現在動いている Python process は旧 import 値を保持する。ratify は candidate を同 process で生成せず、新 process と人間による diff 確認を要求する。
- ratify CLI が受け付ける数値字句は canonical JSON number に限定される。loader の受理集合自体は変更せず、手動に作られた既存承認の受理条件も緩めない。
- ratification artifacts を後で tracked にすると、実 repo `output/` snapshot の母集合へ入る。安定した存在は before/after 比較を壊さないが、テスト中の変更は検出対象になる。
- malicious な land 済み ratify tool を TTY だけで防ぐことはできない。ユーザーによる tool diff、表示された canonical bytes、最終 3 path diff の確認が信頼境界となる。
- pytest は実行していない。本回答は指定 file の静的読解に基づく計画である。

## 総括

- provisional の直接 pin 更新は、厳格な source guard と TTY 確認を条件に採用できる。
- 本 wave の commit では pin を `None` のまま保つ。
- draft は repo 外、承認者欄なし、数値なしの非 authority schema とする。
- ratify の数値は全てユーザー必須入力で、既定値を置かない。
- canonical approval と別 budget 文書は同じ budget object から生成する。
- pin は approval raw hash を使い、固定 1 行だけを最後に更新する。
- 既存の `None` 拒否テストは新防壁として数えず、valid hash でも draft schema が拒否される点を追加で pin する。
- loader、candidate builder、frozen manifest、既存 fixture の受理条件は変更しない。