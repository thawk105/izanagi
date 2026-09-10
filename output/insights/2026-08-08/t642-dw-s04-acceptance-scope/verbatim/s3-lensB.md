結論は、**案 O のままでは NO-GO**です。**brief の前提が覆った。** ただし、同じ 2 行・予算内で修正でき、scope 拡大は不要です。

静的検査だけを行いました。pytest、`check_docs.py`、`spool_fold.py --dry-run`、受入全走は実行しておらず、「緑」とは判定していません。

## 親 brief の独立検算

| 主張 | 判定 | 根拠 |
|---|---|---|
| `docs/dev-wave/**` = 25,196 / 25,200 bytes | 一致 | 4 ファイルは 8,646 + 4,575 + 3,674 + 8,301 = 25,196 bytes。上限は [check_docs.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:254)、合算 gate は [check_docs.py:3558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:3558)。案 O 後は 25,194 bytes。 |
| `DW-S04` の機械 pin なし | 一致 | checker は `DW-S04` 見出しの実在だけを登録する [check_docs.py:395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:395)。core の literal pin は `DW-S09` だけ [check_docs.py:3803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:3803)。`4→7→8→9` は入口にもあるが機械 pin ではない [dev-wave.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:49)。 |
| 同義の規範文は他の正本にない | **記述どおりなら不一致** | living operational runbook に限れば対象は core だけ。ただし canonical decisions には同じ旧規則が wave-local 決定として 11 件ある。後述。 |
| 並行 wave は `docs/dev-wave/**` を編集しない | **段 3 時点では不一致** | brief 後に T-181/T-182 が同じ基準から始まり、`workers.md` と同じ合算予算を所有している [T-181 handoff:31](/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t181-stage6-high.md:31)。元の snapshot が当時正しかった可能性はあるが、現在の前提としては失効した。 |

## 所見 1 — 案 O は「実走」せず約束だけ書ける

- **所見:** `走らせると worklog に書く` は、「走らせる」という未来形を記録すれば満たせ、実走と結果記録を義務化していない。
- **なぜ real か:** 案 O は [s2-plan.md:17](/work/1/SFC/tanab/dev-wave-jobs/t642/s2-plan.md:17)。`DW-S07` は未実測値の先書きを禁じるが、全走自体を強制しない [core.md:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:97)。checker も意味的なずれを検出しないと明記する [check_docs.py:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:6)。
- **成果物影響:** 実走なしでも契約準拠を名乗れて、`check_docs` / spool fold が検出するはずの台帳・成果物索引の赤を含む land 受理集合が旧契約のまま残る。
- **推奨:** **採用。案 O は不採用**。次の同一 scope 案なら実効性を閉じ、物理 2 行で 223 bytes、合計 25,191 / 25,200 bytesに収まる。

```text
「実装しない」裁定時だけ段 5・6 を飛ばし `4→7→8→9` とする。対象外は変異 matrix だけで、
受入全走は実 repo を読むテストがあれば実走し、結果を worklog に書く。
```

## 所見 2 — 「他の正本にない」は repo-wide には偽

- **所見:** 性質検索では、旧規則を wave-local に確定した canonical decision が残っている。
- **なぜ real か:** `docs/decisions.md` の D72:2864、D75:3042、D120:5744、D134:6502、D138:6803、D150:7484、D154:7671、D162:8073、D163:8084、D211:10061、D229:10716。例えば [D72:2864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/decisions.md:2864) は「実装差分なし→変異・受入全走対象外」、[D75:3042](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/decisions.md:3042) はそれを precedent として再利用している。さらに worklog 族で 87 行、insights で 76 ファイル・85 行の性質 hit があった。一方、ゼロ差分でも全走した反例も [worklog.md:1840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/worklog.md:1840)、[worklog archive:1197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/archive/worklog-phase3-0802-106-110.md:1197)、[worklog archive:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/archive/worklog-phase3-0805-239.md:39) にある。
- **成果物影響:** D72 系を一般 precedent として読む consumer は、改訂後も real-repo 全走を受理集合から落とし、runbook と台帳・レポートの参照が分岐する。
- **推奨:** **採用:** brief の主張を「他の living operational norm にはない」へ限定し、新 worklog/insight に「将来 wave の手続を前向きに変更する」と明記する。**不採用:** 過去 decisions/worklog/insights の遡及修正。過去 worklog は凍結 [worklog.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/worklog.md:14)、archive は訂正注記以外の改変禁止 [archive/README.md:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/archive/README.md:1)。当時の契約と実行を示す歴史記録を書き換えるのは改竄になる。

## 所見 3 — 並行 wave の予算所有が後発で競合した

- **所見:** T-642 brief 後、T-181/T-182 が `docs/dev-wave/workers.md` を編集する wave として発生した。
- **なぜ real か:** T-181 は残余 4 bytes と T-182 の同一ファイル編集を明記する [T-181 handoff:31](/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t181-stage6-high.md:31)。T-182 の依頼は段 3 model の置換である [T-182 handoff:9](/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t182-luna-stage3.md:9)。これは T-642 handoff の「触るものはない」[T-642 handoff:17](/work/1/SFC/tanab/dev-wave-jobs/handoff/dev-wave-t642-s04-scope.md:17) より後の新事実である。
- **成果物影響:** 個別ファイルが異なっても合算 ceiling を共有するため、後に land する wave の受理集合が `check_docs` で拒否され、T-642 のレポート・台帳 fragment も certified land 集合へ入れない。
- **推奨:** **採用。** T-642 の scope を `workers.md` へ広げず、段 4 前に所有と land 順を再確認し、commit・land 直前に4ファイル合計を再計測する。未確定なら `DW-STOP` の新事実扱い [core.md:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:20)。

## 所見 4 — checker 非強制は real だが別 scope

- **所見:** 改訂後も checker は旧文への回帰を検出しない。P2 の「4 bytes なので機械化不能」という理由は成立しない。
- **なぜ real か:** `check_docs.py` 自身が義務本文の保存・意味検査を対象外とする [check_docs.py:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/tools/check_docs.py:7)。literal pin は `tools/check_docs.py` とそのテストへ置けるため、`docs/dev-wave/**` の4-byte余白とは別問題である。
- **成果物影響:** 将来、旧文または同義の「全走対象外」へ戻しても checker が受理し、docs 起因の破損を見逃す受理集合が復活する。
- **推奨:** **scope 外。** 本 wave を checker/test 差分へ広げず、P2 の理由だけ訂正する。機械 pin を採るか、意味レビューのみを明示的に受容するかは別 hardening 裁定にする。

入口・skill・hooksには古い full-run 除外の独立規範はなかった。入口は `DW-S04` を直接 dispatch し [dev-wave.md:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:64)、段 7 でテスト条件 `DW-O18` を読む [dev-wave.md:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:72)。skill も関連テストを省略しない [SKILL.md:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.agents/skills/dev-wave/SKILL.md:43)。したがって入口・skill・hooksの同時改訂は不要である。

NIT: 入口の説明では受入再走が段 6 に置かれ、その段を飛ばすとも書く [dev-wave.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/.claude/commands/dev-wave.md:49)。ただし段 4 leaf と段 7 `DW-O18` が直接到達可能なので、成果物影響を実証できる矛盾ではない。

## 所見 5 — P3 は成立するが bootstrap 時点を記録すべき

- **所見:** 本 wave への新契約適用は妥当。ただし「旧契約に従って開始した wave」と「未 land の新契約を qualification に用いた時点」を混同してはならない。
- **なぜ real か:** 開始時の core は全走対象外 [core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/dev-wave/core.md:79) だが、ユーザー裁定は既に台帳へ記録済み [worklog.md:3179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/worklog.md:3179)。land は branch の ff-only 後に fragment を fold する [spool/README.md:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/spool/README.md:82) ため、canonical worklog が生成される時点では新 core が先に main に入る。
- **成果物影響:** 時点を省くと、台帳が「まだ land していない規範を既に有効だった規範」と誤って参照し、手続監査の authority/effective-time が壊れる。
- **推奨:** **採用。** P3 は user-approved bootstrap として実行する。旧契約でも追加の全走は禁止されていないため赤にはならない。fragment には「開始時 main は旧射程だったが、2026-08-08裁定済み置換を bootstrap 適用し、実 repo test の存在確認後に全走した」と時制を明記する。

## spool fragment の静的検算

所見なしです。

- ファイル名・frontmatter は共通契約 [spool/README.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/spool/README.md:28) と一致。
- `## 本文` → `## 次の一手差分` の exact 2 H2 は ledger 契約どおり [worklog/README.md:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/spool/worklog/README.md:5)。
- `### 完了`、`remaining: none`、`base:` の形式・順序は一致 [worklog/README.md:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/spool/worklog/README.md:64)。
- 現 T-642 実体 [worklog.md:3179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/worklog.md:3179) の3行を末尾 LF 1個に正規化した SHA-256 は、プランどおり `ba6a72db24c2b9f9782ecb7693c7f6b769be751adb1d45f56f6e09c70ef1e282`。
- `check_docs` は base 不一致を検出しないため、作成直前の再計算と `spool_fold.py --dry-run` は依然必須 [spool/README.md:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t642-s04-scope/docs/spool/README.md:72)。

## 総括

最も重い所見は次の3件です。

1. **案 O の実走義務が文章上閉じていない — real 度: 高。** 同一 scope・予算内の「実走し、結果を」で修正必須。
2. **並行 wave 非競合の前提が段 3 時点で失効 — real 度: 高。** T-181/T-182 を含めて合算予算を再 baseline するまで fail-closed。
3. **repo-wide の「他正本なし」は偽で、旧 D/worklog/insight が多数残る — real 度: 中〜高。** 遡及改変せず、前向き supersession と bootstrap 時点を新記録に明記する。

したがって、案 O はそのまま採用せず、所見1の223-byte案へ差し替えた plan v2 を採るのが妥当です。