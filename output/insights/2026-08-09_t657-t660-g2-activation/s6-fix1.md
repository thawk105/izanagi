指定 script 1 ファイルのみ作成しました。

[reissue_floor_protocol.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh:1)  
mode: `755`

## 必須要件との対応

1. fail-fast  
   先頭を `#!/bin/bash`、`set -Eeuo pipefail` とし、検査は `if ...; then ... else` または `[[ ... ]] || die` で停止させています（1–2、65–364 行）。

2. trap 復元  
   23–63 行で EXIT・HUP・INT・TERM を捕捉。失敗時は `git restore --source=HEAD --staged` と `git restore --source=HEAD --` を実行し、HEAD/index/worktree の blob 一致を検査します。221–236 行で repo 外へ非破壊 copy、239 行から復元を有効化し、commit 成功後の 352–353 行でのみ解除します。

3. T-080 receipt  
   183–219 行で次を実行し、rc=0、`state == "active-valid"`、`refusals == []`、observation が object であることを assert します。
   ```text
   python3 -m orchestrator.campaign.t080_freeze_migration verify \
     --path output/t080-migration/legacy-freeze-repin.receipt.json
   ```

4. 独立 golden  
   142–174 行で旧 774 bytes・旧 SHA・g1 出現 1 回・18 key を事前検査。251–296 行で単一置換との byte 完全一致、新 SHA、18 key、変更 key が `contract_sha256` のみであることを検査します。

5. provenance  
   326–364 行で message file を作り、唯一の trailer `AI-Agent: none` を検査後、`--message-file` preflight → `git commit --only -F` → full-history 監査の順で実行します。

6. stage exact 性  
   301–324 行で、staging 前の staged 集合が空、unstaged が target のみ、staging 後の staged 集合が target 1 件のみ、unstaged が空であることを assert します。

7. isatty 維持  
   65 行で stdin の tty を検査。245–247 行の `freeze-protocol` は stdin redirect を一切行いません。

8. 前提条件  
   65–140 行で cwd、Git root、clean tree、tracked floor、HEAD blob、activation record serial=2、Pegasus g2、`_ACTIVATION_HEAD_SERIAL == 2`、旧 SHA を検査します。

9. 冪等性  
   136–139 行で新 SHA と一致済みなら「実施済み」と報告し、変更せず rc=0 で終了します。

10. pin 非更新  
    366–376 行で別工程の更新対象と値を案内します。対象は `FROZEN_MANIFEST`、protocol builder golden、real seal E2E の protocol/calibration/contract pin です。

## CLI・根拠の検証

- `freeze-protocol` の正確な module 起動形は原案どおりです。[s8b_floor_campaign.py:3519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:3519) と [同:3543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:3543) で確認しました。
- create-only writer は [s8b_floor_campaign.py:548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:548) にあり、既存 target は `os.link` が拒否します。同 writer を実 floor に呼ぶ箇所は [同:656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/s8b_floor_campaign.py:656) です。
- receipt の実 path は [t080_freeze_migration.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/t080_freeze_migration.py:34)、`verify --path` は [同:2102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/orchestrator/campaign/t080_freeze_migration.py:2102) で確認しました。
- `--message-file` は [check_ai_provenance.py:1928](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-t660-g2-activation/tools/check_ai_provenance.py:1928) に実在します。

## 検査結果・波及

`bash -n output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh` は rc=0。mode `755`、作業木の追加は当該 1 ファイルのみです。

既存コード・テスト・docs・floor 成果物は未変更です。`git add`、`git commit`、script 本体、receipt verify、`freeze-protocol`、pytest は実行していません。したがって受入については「実装済み・未実走」です。floor 再発行前の certified writer／prediction seal の期待赤は残り、ユーザー実行後も列挙した pin 更新までは post-C 受入対象になりません。

## 総括

- D-1/D-2/D-3 を閉じる fail-closed script を作成。
- 失敗・中断時は tracked floor を HEAD blob へ復元。
- receipt、golden、staging、provenance をすべて停止条件化。
- 実行可能 mode `755`、`bash -n` rc=0。
- script・freeze・pytest は未実走。
- 変更面は指定 script 1 ファイルのみ。