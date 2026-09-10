---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-10
wave: rulings-land-recovery
seq: 1
---

## 新規

### {{F:rulings-commit-before-land}}. rulings が main への fragment commit だけで終わり、裁定を canonical へ届けなかった [手順漏れ] [誤前提]

- 事象: 全50項のユーザー裁定を `32603d385` で local main へ直接commitし、68項の更新を持つ
  worklog fragmentとdecisions fragmentを未foldのまま残して終了した。
  ユーザーの「main landsいた？」に未landと回答した後も、その事実の報告だけで止まり、
  「他のdev-waveが困るのでは？」と再指摘されて初めて復旧へ進んだ。
- 根本原因: rulingsの入口が「fragmentへ記録しcanonicalを直接編集しない」までしか明記せず、
  agentが記録形式の遵守を完了条件と取り違えた。既存の受入・land・foldを記録作業にも適用する
  導線を読まず、通常のmain着地経路を直接commitで代用した。
- 影響: canonicalの裁定と次の一手は古いまま、mainには未fold fragmentが存在した。
  別waveがfoldするまで判断が正本へ届かず、同じID更新のbase不一致や混載を起こし得る状態だった。
  別waveの受入失敗やデータ消失を実測したとは主張しない。
- 恒久対応: `.claude/commands/rulings.md` の記録導線に、専用branch・main直接commit禁止と
  `docs/dev-wave/operations.md` DW-O17/O23/O25/O27による受入→land→foldを明記した。
  成功応答とcanonical反映の確認前に完了報告しない。Codex Skillは既に同commandを全文適用する。
  新guard、checker機能、権限拡張は作らない。プロンプト規律であり機械的な再発不能保証ではない。
- 再発検知: 最終報告前にlandの成功応答、FOLDED receipt、canonicalにある裁定と対象ID、
  自分の未fold fragmentの不在を実体で確認する。今回の復旧で同じ既存経路を実走する。
- 既存型との区別: F747はcleanup権限を記録権限へ広げた事故、F907はcwd誤認と全stageの事故。
  今回の裁定記録は授権済みで対象pathも明示していたが、mainへの記録だけを終端にした点が異なる。

## 再発

### F672

- **再発: 2026-09-10** — rulings-land-recoveryの正式受入1は22463 passed / 68 skipped、
  child-greenだったが、landが別waveの登録path `.codex/worktrees/t1851-c2-s2` のstrict解決で
  `[Errno 4] Interrupted system call` を返しrc31になった。main_before/main_afterはいずれも
  `32603d3858289e3851227f8cad60d97e2e01f761`、release_safe=true、retryable_same_request=false。
  直後の読取専用再確認では同pathのstrict解決と.git fileの存在を確認した。
  既存F672の復旧に従い、新しい受入とrequestで再試行する。他waveの登録は触らない。
