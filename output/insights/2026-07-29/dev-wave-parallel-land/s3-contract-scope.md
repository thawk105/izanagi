parent brief と plan は全文読了しました。以降は静的検査のみで、編集・テスト実走はしていません。判定は NO-GO です。

## real findings

### R1 — BLOCKER — accepted triple は受入結果ではなく caller の自己申告

Plan は `A/T/L` を受入結果と呼びますが、helper の入力は生の CLI 引数です。[s2-plan.md:49](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:49) [s2-plan.md:90](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:90)

さらに受入を行う段6の後に、段7・8が commit を追加し得るため、段6で検査した tip と「記録・自己改善を含む最終 `T`」は一致しません。[dev-wave.md:51](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/.claude/commands/dev-wave.md:51)

- 成果物影響: caller が現在の main・tip・`rev-list` を再計算して渡せば、受入を再走していなくても stale acceptance を洗浄できる。未検査の最終 tip が land し得る。
- 最小 fix: 生の `--accepted-*` を廃止し、最終 `T` 確定後の固定 acceptance wrapper が create-only receipt を作る。receipt に `A/T/L`、実行した検査、rc、対象 SHA を束縛し、land helper はその receipt のみを消費する。

### R2 — BLOCKER — `9→6→7→8→9` は段8「一度だけ」と衝突

Plan は段8を再実行しますが、core と自己改善正本はともに一度だけと明記しています。[s2-plan.md:79](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:79) [core.md:96](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/dev-wave/core.md:96) [skill-self-improvement.md:55](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/skill-self-improvement.md:55)

段7再実行も、worklog の「セッション末に1回更新」と、handoff を正常終了時に一度吸収する契約が未定義になります。[CLAUDE.md:154](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/CLAUDE.md:154) [handoff/README.md:12](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/handoff/README.md:12)

- 成果物影響: 自己改善 commit の重複、worklog 二重エントリ、保存則の誤消化、handoff 不在での再作業が起こり得る。
- 最小 fix: 推奨は rc10 で現在の wave を停止し、fresh context で再同期すること。どうしても同一 wave で戻すなら `9→6→7→9` とし、段8は再実行せず、段7は既存の未landエントリを一回だけ書き直して新規エントリを足さない。

### R3 — BLOCKER — 固定 `9→6` は期限付き condition rollback を飛ばす

新 upstream `A..C` が freeze、producer bytes、gate 新設に触れた場合、現行 dispatcher は段1または段2まで成果物を invalidate して戻す契約です。[dev-wave.md:26](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/.claude/commands/dev-wave.md:26) Plan の一律 stage 6 復帰にはこの分岐がありません。[s2-plan.md:72](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:72)

- 成果物影響: 新 upstream が変更した gate/freeze 前提を旧 brief・plan のまま取り込み、期限付き防壁を迂回する。
- 最小 fix: `A..C` を merge 前に条件再評価し、O08/O09/O10 なら段1、O13なら段2から fresh に再実行する。それ以外だけを段6候補にする。

### R4 — HIGH — own/foreign 判定不能で、stale/中断拒否は宣言板を破壊

現行 handoff schema に session ID、owner、worktree identity はありません。したがって caller 指定の `--own-handoff-name` だけでは foreign を証明できません。[handoff/README.md:22](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/handoff/README.md:22) [s2-plan.md:29](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:29)

また README は残ファイルを「稼働中か中断」と定義しています。`中断` や48時間超を land blocker にすると、回収すべき WAL が全 session の land を止めます。[handoff/README.md:15](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/handoff/README.md:15) 48時間判定は現在も「死んだ可能性」の診断であり、ownership 証明ではありません。[check_docs.py:1983](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py:1983)

推奨分類は次です。

| handoff | cleanliness | 扱い |
|---|---|---|
| own active | 許可 | land 成功まで残し、成功後に caller が吸収・削除 |
| foreign active | 許可 | 非接触 |
| valid stale active | 許可＋診断 | 回収候補として表示、land は止めない |
| valid `中断` | 許可＋診断 | 宣言板/WALとして保存 |
| malformed・非regular・symlink・未知パス | 拒否 | ownership namespace と確認できない |
| tracked/staged handoff | 拒否 | 通常の main dirt |

- 成果物影響: 現案では中断 session 一つで並行 land が恒久停止し、own handoff は失敗し得る FF の前に消えて復旧情報を失う。
- 最小 fix: land の受理判定から own/foreign と鮮度を外す。schema-valid な全3状態を control-plane 例外とし、鮮度は診断だけにする。

### R5 — HIGH — helper が唯一の終端経路として固定されていない

現行 dispatcher/core は直接の `--ff-only` を許す表現です。[dev-wave.md:39](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/.claude/commands/dev-wave.md:39) [core.md:103](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/dev-wave/core.md:103) Plan の check_docs 強化も Skill 内に literal があるかを見るだけで、段9から helper が実際に呼ばれることを保証しません。[check_docs.py:1524](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py:1524)

Codex には hook が未配線で、Claude の guard も一般的な main FF を拒否する防壁ではありません。[hooks/README.md:183](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/hooks/README.md:183)

- 成果物影響: Claude/Codex が従来どおり手作業 merge すれば、accepted-main 比較と lock が丸ごと迂回される。
- 最小 fix: `DW-S09` に「main ref を変更できる唯一の経路は helper、直接 merge 禁止」を置く。check_docs は helper path を `DW-S09` 節内に固定し、直接 land 文言へ戻す変異を赤にする。

### R6 — HIGH — `.gitignore` は新 helper 以外の clean gate を弱体化

root-anchored 自体は狭いものの、ignore 後は既存 `snapshot_repo()` の status から container 内異物が消えます。[git_state.py:47](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_waves/git_state.py:47) supervisor checker はその snapshot を main clean の根拠にします。[checker.py:443](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_waves/checker.py:443) しかし plan は checker を変更しないとしています。[s2-plan.md:202](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:202)

- 成果物影響: `.codex/worktrees/junk/` のような未登録異物が supervisor 等では clean と見える。親 brief の「未知 untracked 拒否」を横断的に弱める。
- 最小 fix: `.gitignore` 追加を削る。新 helper は導入前正例として既に container を個別分類できる設計なので、ignore は成果に不要。残すなら status を使う全 consumer に同じ登録検査を入れる。

### R7 — HIGH — postcondition failure 時には main が既に変更済み

helper は merge 後に cleanliness を再確認し、失敗を rc24 にまとめます。[s2-plan.md:63](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:63) その間、handoff/worktree 作成者は land lock を使わないため、並行 session の開始が postcheck を赤にできます。

- 成果物影響: helper は「失敗」を返すが main は既に `T`。caller が再同期・再mergeを始め、記録と実Git状態が逆転する。
- 最小 fix: merge の rc にかかわらず HEAD を再観測し、`not-landed` と `landed-but-postcondition-failed` を別 reason にする。後者は絶対に自動 retry しない。handoff/worktree 作成との競合を fault injection で固定する。

### R8 — MEDIUM — Codex Skill の helper 直 pointer は drift 面を増やす

Codex Skill は既に dispatcher 全文を読み、dispatcher の段9が `DW-S09` を読むため、共通経路は成立しています。[SKILL.md:14](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/.agents/skills/dev-wave/SKILL.md:14) [dev-wave.md:75](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/.claude/commands/dev-wave.md:75)

Skill に helper path をもう一度 pin すると、core と Skill の二箇所を更新する必要が生じます。これは D94 の「外延を再掲しなければ drift が存在しない」と逆です。[decisions.md:4211](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/decisions.md:4211)

- 成果物影響: helper rename/契約変更時に Claude と Codex が別経路を読む。
- 最小 fix: helper pointer は `DW-S09` だけに置く。Skill には Codex 固有の fresh-context、`$dev-wave`、hook未配線、worker/supervisor差分を残す。特に現行 line 49 の「新しい Codex context」は削らない。

### R9 — MEDIUM — worktree grammar が正当な並行 worktree を過剰拒否する

Plan は未知 field を拒否し detached も拒否します。[s2-plan.md:39](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:39) 静的観測した現 worktree 一覧には正当な Claude worktree の `locked <reason>` field が既にあります。また detached audit worktree は main cleanliness 上危険ではありません。

- 成果物影響: 正常な Claude session や read-only audit があるだけで land が停止する。
- 最小 fix: `locked` を明示的な既知 field として正例化する。受理根拠は safe path、一意な登録、同一 common git-dir、非main checkout に絞り、branch naming と detached は診断に下げる。

### R10 — HIGH — テスト計画は「両 session が最終的に land」を実証しない

現案は helper の一回の成功/失敗と再受入済み pair の成功を個別に試すだけです。[s2-plan.md:166](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:166) dispatcher/Skill の helper 強制、race loser の再同期、最終 main が両成果を含むことは一つのシナリオで結ばれていません。

- 成果物影響: unit tests は緑でも、実際には一方が rc10 後に回収不能、または直接 merge を続け得る。
- 最小 fix: 同じ `A` から Claude/Codex worktree・handoff・tip を2本作り、競合 land → loser stale → fresh再同期・再受入 → loser land、までを一つの deterministic integration test にする。最終 main が両 tip の descendant、foreign artifacts が byte/inode 不変、未知 untracked は拒否、と確認する。

### R11 — MEDIUM — 450行 helper は既存 Git 観測層を重複実装する

既存 `git_state.py` には sanitized Git runner、repo/worktree identity、porcelain v2 parser、stable snapshot、exact FF chain、branch tip が既にあります。[git_state.py:116](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_waves/git_state.py:116) [git_state.py:176](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_waves/git_state.py:176) [git_state.py:461](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/dev_waves/git_state.py:461)

- 成果物影響: env sanitization、status parsing、SHA規則が supervisor と interactive land で再び drift する。
- 最小 fix: 観測 primitive は既存 module から再利用・最小抽出し、mutating merge と interactive policy だけを新 helper に置く。supervisor の API に merge を追加してはならない。

## refuted findings

- 「Claude と Codex は同じ正本を読まない」は refuted。現行 Skill は dispatcher 全文を共通状態機械として読み、段9 row は `DW-S09` を指しています。問題は共通経路の欠如ではなく、Skill へ helper pointer を重複追加する案です。
- 「短時間 lock では協調 session 二者の race を閉じられない」は refuted。全 lander が helper を唯一経路として使うなら、lock 内の `C==A` と FF で十分です。非協調 writer は別の scope です。
- 「supervisor checker をそのまま land helper にすべき」は refuted。supervisor は既land結果の事後検証で、real 実行も未開放、TOCTOU 完全遮断も非目標です。[README.md:42](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/dev-wave-supervisor/README.md:42) 再利用すべきなのは Git 観測 primitive までです。
- 「active handoff の T-173 衝突は blocker」は refuted。D70 は並行 session の番号を予約と見なさず、land直前に再走査・振り直す契約です。[decisions.md:2702](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/decisions.md:2702) 既知の統合作業であり、段4停止理由ではありません。

## scope外裁定候補

- `9→6...` による状態機械変更と D69 上書きはユーザー裁定が必要です。自己改善正本は段構成・予算変更を自動実装せず裁定へ返すよう要求しています。[skill-self-improvement.md:55](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/skill-self-improvement.md:55)
- candidate の gitlink 変更を一律拒否する案は別の能力縮小です。[s2-plan.md:62](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:62) 本 repo は正規に submodule pin を前進させるため、v1制限として受諾するか、別 land 手順を設計するかの裁定が必要です。[decisions.md:276](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/decisions.md:276)
- 同一 UID の直接 writer まで防ぐ `reference-transaction`/CAS は別脅威モデルです。要求するなら short flock 案だけでは不可、要求しないなら「協調 Claude/Codex の事故防止」と明記すべきです。
- core 9,000→11,000、aggregate 24,000→26,000 は独立予算裁定です。現状の余白が小さいため何らかの変更は必要ですが、+2,000 の根拠となる完成後 byte 見積りがありません。[check_docs.py:148](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/tools/check_docs.py:148) [decisions.md:4228](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/docs/decisions.md:4228)

## 縮退案

同じ保証に対する最小案は次です。

1. `.gitignore` は変更せず、land helper 自身だけが登録済み container と schema-valid handoff を cleanliness 例外として分類する。
2. helper は既存 Git 観測 primitive を再利用し、短時間 lock・receipt検証・一回の FFだけを新設する。
3. helper は共通 `DW-S09` だけから呼び、Skill は dispatcher と Codex 固有差分だけを持つ。
4. own handoff は land 成功まで残す。foreign/stale/中断は非接触の control-plane data として許可する。
5. stale main または lock busy は現 wave を停止し、fresh context で再同期する。状態機械へ back-edge を足さない。
6. 二つの wave が競合後に順次 land し、最終 main が両成果を含む E2E を受入条件にする。

## 総括

**NO-GO。** 段4の must-fix は、① acceptance receipt の実在と最終 tip への束縛、② `9→6→7→8→9` の撤回または明示裁定、③期限付き rollback の保存、④ handoff を全状態で宣言板として守る分類、⑤ helper を唯一の land 経路にする契約、⑥ `.gitignore` による既存 clean gate 弱化の解消、⑦ merge後失敗の状態分離、⑧両 session の eventual land E2E です。

推奨は back-edge を作らず、race loser を fresh context へ返す縮退案です。これが D69、段8一回、worklog一回、D70、宣言板を同時に最も少ない変更で守ります。