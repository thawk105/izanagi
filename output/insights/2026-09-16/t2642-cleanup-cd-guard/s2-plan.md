## 結論と前提

**5897 bytes・最長行105文字に収まる案を推奨します。** §1 に進入禁止、§3 にセッション cwd の確認を置き、§2 の退避指示を§3へ統合します。

以下の行番号は、特記しない限り**現行ファイルの行番号**です。文面の組立て・UTF-8計数・定数との照合はメモリ上だけで行いました。編集、ファイル作成、commit、pytest、受入実走はしていません。

## 文面案と配置

対象は [.claude/commands/cleanup-branches.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2642-cleanup-cd-guard/.claude/commands/cleanup-branches.md)。

**① §1、現行28行の直前へ次の1行と空行を挿入する。**

```text
撤去対象へは `cd` せず `git -C` と絶対 path で扱う。

```

棚卸しの最初の操作より先に読ませます。改訂後28行になります。

**② §1、現行31–32行を置換する。**

```diff
-- ahead>0 のブランチは `git cherry main <b>` を出す。ahead だけでは判定できない
-  (rebase / cherry-pick は ahead>0 のまま残る)。`+` 行は実在でなく内容で判定する
+- ahead>0: `git cherry main <b>`。ahead 単独判定禁止
+  (rebase / cherry-pick 後も ahead>0)。`+` は実在でなく内容で判定
```

**③ §2、現行41–42行を置換する。**

```diff
-- ブランチ: **ahead=0 (main に取り込み済み) のみ削除**。`git branch -d` を使う (`-D` は使わない —
-  -d が拒否したら取り込み漏れの兆候なので止めて報告)
+- ブランチ: **ahead=0 (main 取込済) のみ削除**。`git branch -d` 限定、
+  `-D` 禁止。-d 拒否は取込漏れの兆候、停止・報告
```

**④ §2、現行46行を削除し、退避義務を⑤へ移す。**

```diff
-- 自分がその worktree 内で作業中なら、先に main checkout 側へ抜けてから操作する
```

**⑤ §3、現行50行の直前へ次の1行と空行を挿入する。**

```text
撤去 step のセッション cwd を検査。対象配下・不明なら停止し、main checkout へ抜けて対象外と再確認する。

```

改訂後51行になります。既存 checker 呼出しより前に置き、現行50–51行の **exact 2行契約は変更しません**。改訂後は53–54行になります。

ここでいう cwd は、撤去を行う**実行セッションの cwd**です。別 cwd を指定した一時的な子シェルの `pwd` だけでは確認完了と扱いません。対象外への退避を確認できなければ停止を維持し、既存§3末尾の引き渡し規則へ従います。

## byte 収支と安全義務の対応

計数は **各行末の LF を含む UTF-8 bytes**。文字数は LF を除きます。

| 変更位置 | 削除 bytes | 追加 bytes | 新行の文字数 |
|---|---:|---:|---:|
| 28行前：進入禁止 | 0 | 68 | 37 |
| 同：空行 | 0 | 1 | 0 |
| 31行置換 | 100 | 60 | 45 |
| 32行置換 | 102 | 80 | 51 |
| 41行置換 | 124 | 86 | 55 |
| 42行置換 | 76 | 68 | 29 |
| 46行削除・義務移設 | 106 | 0 | — |
| 50行前：cwd確認・退避 | 0 | 143 | 64 |
| 同：空行 | 0 | 1 | 0 |
| **合計** | **508** | **507** | |

算術は次のとおりです。

```text
5898 − 508 + 507 = 5897 bytes ≤ 5900 bytes
```

改訂後全文は84行、最長は変更しない19行の105文字です。追加・置換行もすべて110文字以下です。

**byte の出所と義務の保存**

| 出所 | 縮約・移設 | 禁止・必須・違反時の扱い |
|---|---|---|
| 31行：40 bytes | 「のブランチは」「を出す」「だけでは判定できない」を条件付き命令と「単独判定禁止」に集約 | ahead>0 で `git cherry` 必須。ahead単独判定は禁止。未着地時の§5報告は33行に保持 |
| 32行：22 bytes | 「は…のまま残る」を「後も…」、「`+` 行」を「`+`」、「判定する」を「判定」へ | rebase/cherry-pick後もaheadが残る説明と、実在ではなく内容で判定する義務を保持。spool不在の扱いは33行に保持 |
| 41行：38 bytes | 「main に取り込み済み」を「main 取込済」、「を使う」を「限定」へ | ahead=0のみ削除、`git branch -d`のみ使用。条件未達は§2見出しどおり削除せず報告 |
| 42行：8 bytes | 「が拒否したら…なので止めて報告」を「拒否は…、停止・報告」へ | `-D`禁止、`-d`拒否を取込漏れの兆候と扱い、停止・報告する義務を保持 |
| 46行→§3：**37 bytes増** | 106-byteの退避指示を143-byteの検査・停止・退避・再確認へ置換 | 対象内で操作しない義務とmain checkoutへの退避を保持。対象配下・不明で停止し、対象外と再確認する条件を明文化 |

既存命令の縮約で **108 bytes** を確保し、移設・強化に37 bytes、進入禁止と空行に70 bytesを使います。差引1 byte減です。安全義務を削って予算を作る案ではありません。

## pin 追従：アンカー表1〜10

親表の行番号には一部ずれがあります。下表は現在の実体です。

| # | file:line | 更新 | 指示 |
|---|---|---|---|
| 1 | `tools/check_docs.py:285` | 不要 | `TextLimit(5_900, 110)`を維持 |
| 2 | `tools/check_docs.py:752`、値は753 | **必要** | `CLEANUP_COMMAND_SHA256`を改訂commandのSHA-256へ。実値は親が実測 |
| 3 | `tools/check_docs.py:755` | 不要 | `CLEANUP_OCCUPANCY_SECTION`を維持 |
| 4 | `tools/check_docs.py:756` | 不要 | `CLEANUP_OCCUPANCY_CONTRACT`の2行を一字も変更しない |
| 5 | `tools/check_docs.py:6054` | 不要 | F26 address edge・可視§3一意性・exact契約検査を維持 |
| 6 | `tools/check_docs.py:744` | 不要 | SKILL本文を変えないため、そのSHA-256も維持 |
| 7 | `orchestrator/tests/test_check_docs.py:580`、値は581 | **必要** | `_EXPECTED_CLEANUP_COMMAND_SHA256`を#2と同じ新digestへ |
| 8 | `orchestrator/tests/test_check_docs.py:627` | **必要** | `_SYNTHETIC_CLEANUP_COMMAND`全体を改訂commandの逐語複製へ。末尾LFも一致させる |
| 9 | `orchestrator/tests/test_check_docs.py:9843`、9848、9849 | **必要** | 両byte assertを`5_897`へ。超過生成の`("x" * 2)`を`("x" * 3)`へ |
| 10 | `orchestrator/tests/test_check_docs.py:10123` | 不要 | slack `discard_changes: true`を一意のまま保持 |

#9は次を維持します。

```text
5897 + 改行1 + xを3文字 = 5901
```

したがって9842行の上限、9850行の`5_901`、9857行の超過メッセージは変更不要です。

**更新対象はアンカー4項目（#2・#7・#8・#9）、具体的には6編集箇所**です。全文複製を1箇所として数えています。

静的照合では、現在のsynthetic全文と実commandは一致していました。改訂案でも `$ARGUMENTS`、slack、可視§3見出しは各1件、F26と住所の同一行共起は残ります。

## P1：checker は自身の cwd を検出するか

**通常の可視・観測可能な同一PID namespaceでは検出します。ただし無条件にrc=1を保証する前提は棄却します。**

[tools/check_worktree_occupancy.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2642-cleanup-cd-guard/tools/check_worktree_occupancy.py) の経路は以下です。

- **553–558行**：`/proc`直下の数字名entryを列挙。**586–594行**で全列挙PIDを `_scan_pid` へ渡し、自己PIDを除外していません。
- **401–451行**：cwdを読み、対象そのもの・配下なら`"cwd"`を追加。自己PIDにも適用します。
- **453行**：`pid != self_pid`は **cmdlineの検査だけ**に効きます。checker引数に対象pathがあることによる自己誤検出を避けています。
- **305–327行**：`seen = {self_pid}`は祖先PID探索の循環防止。cwd走査の除外集合ではありません。
- **456–470行**：呼出し元祖先の例外もcmdlineに限定され、cwdの検出結果を消しません。
- **616–621行、713–718行**：occupantがあれば`occupied`、rc=1です。

既存の `orchestrator/tests/test_check_worktree_occupancy.py:285` も自己cwdを除外しない契約を持ちます。今回は読解だけで、実走していません。

**rc=1にならない経路**

- **403–407行、422–426行**のcwd権限不足は、非阻害の診断に分類されます。別のoccupantやissueがなければrc0です。
- checkerを対象外cwdで起動し、対象内にいるharness側プロセスのcwdが観測不能で、argvにも対象参照がなければ、セッションの危険を検出できません。
- 別PID namespace、走査後のcwd変更・新規process等も対象外です。冒頭4–10行がこの限界を明記しています。

**文面で塞ぐ範囲**は、rc0をセッション退避の証明と扱わず、§3で実行セッション自身のcwdを確認し、不明なら停止する運用です。新しいcheckerは不要です。

一方、観測不能なharnessまで含めた**機械的保証**は文面だけでは成立しません。その保証を要求するならcheckerや実行基盤の変更が必要で、scope外の裁定候補です。

## P2・P3：進入前の配置と退避指示

**P2：§1冒頭が必要です。**

2026-09-15の経路は棚卸し中の進入なので、§2・§3だけでは操作後に読む可能性が残ります。§1の最初の操作より前に68-byteの禁止文を置けば、status確認とuntracked確認の双方へ適用できます。§3には重複した進入禁止を置かず、cwd確認を担当させます。

**P3：是正が必要です。**

現行46行は「後でmainへ抜ければよい」と読め、途中で対象へ入ることを抑止しません。また、一時的なshellの退避とセッションの退避を区別していません。

提案では退避義務を§3へ移し、**検査→停止→mainへ退避→対象外と再確認**にします。移設単体の収支は`143 − 106 = +37 bytes`です。cwd固定・occupied/locked時の操作禁止と引き渡しを定める現行63–64行は保持し、その例外を作りません。

## 実装子への分割

**3 fileを1本のCodex authorへ渡します。**

command本文、whole-file digest、synthetic全文、byte境界testは一体で更新する必要があります。pathだけなら素集合へ分割できますが、内容の確定とdigest・fixture更新には依存関係があり、独立した実装にはなりません。親briefの実装子1本という方針に従います。

## 副作用とconsumerの静的確認

| file:line | 壊し得るもの／今回の扱い |
|---|---|
| `tools/check_docs.py:5980`、5986 | byte・行長超過。提案は5897 bytes／105文字 |
| `tools/check_docs.py:771` | frontmatterと`$ARGUMENTS`契約。変更しない |
| `tools/check_docs.py:6054` | F26住所、§3一意性、逐語契約。保持する |
| `tools/check_docs.py:6571` | command全文digest。更新漏れで赤になる |
| `orchestrator/tests/test_check_docs.py:897`、923 | syntheticから最小repoを作るconsumer。全文追従が必要 |
| `orchestrator/tests/test_check_docs.py:9829` | checker定数・期待digest・synthetic digestの一致。3者を同期 |
| `orchestrator/tests/test_check_docs.py:9840` | byte境界test。assertだけでなくpaddingも更新 |
| `orchestrator/tests/test_check_docs.py:9938` | 1-byte変異の`commit graph`文字列。変更しない |
| `orchestrator/tests/test_check_docs.py:9966`、9982、9994、10010 | 見出し・Markdown変異。§4見出しとslackを保持。1-byte増でも予算内 |
| `orchestrator/tests/test_check_docs.py:10123` | 変異の予算中立化。21文字のslackを一意で保持 |
| `orchestrator/tests/test_check_docs.py:10153`、10186、10209、10232 | checker呼出し・rc規則・否定・節分散の変異。exact 2行と§2見出しを保持 |
| `orchestrator/tests/test_check_docs.py:10262`以降 | F26 address edge変異。現行59行の住所表現とfrontmatterを保持 |
| `orchestrator/tests/test_branch_rescue_ledger.py:167`、344 | §1見出しとrescue/audit bulletを解析。見出し・対象bulletは変更しない |
| `.agents/skills/cleanup-branches/SKILL.md:14` | command全文を不可分適用するconsumer。新命令も共有される |
| 同SKILLの22–27行 | cwd固定不能時の縮退・観測missの限界・破壊操作前の再評価。提案と整合する |

**SKILL.mdの変更は不要です。** commandを全文読む設計であり、新命令の複製もoverlayの意味変更も必要ありません。SKILL側のdigest・syntheticも据え置きます。

親の実測では、関連docs testとledger wiring test、`check_docs.py`、brief指定の受入全走を確認してください。ここでは緑とは報告しません。

## 裁定パッケージ候補

1. **P1の機械的保証範囲**：観測不能なセッションcwdまで自動的に停止させる保証が必要なら、別scopeで実行基盤との連携等を検討する必要があります。本案は手順上の停止義務を明文化するものです。
2. **F51の旧恒久対応との不整合**：`docs/failures.md:2516`はdetach・branch削除・unlockまでの縮退を記述していますが、現行command63–64行はそれらも禁止しています。今回は安全側のcommandを維持し、F51再編は行いません。

## 総括

- **予算：yes — 改訂後5897 bytes、最長105文字。**
- **pin追従：更新は4アンカー項目、具体的に6編集箇所。**
- **P1：条件付き成立。自己cwdは走査するが、観測不能経路のrc0は残るため、セッションcwd確認を明文化する。**
- **P2：§1冒頭へ進入禁止を置く。§3だけの配置は不十分。**
- **P3：是正する。退避指示を§3の停止・再確認へ統合し、単体で37 bytes増。**