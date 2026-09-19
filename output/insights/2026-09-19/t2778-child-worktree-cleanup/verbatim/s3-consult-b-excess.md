## 総括

**推奨は P1 の限定版です。登録 CLI・日時・purpose 列挙・子 branch 削除を外し、履歴 pack は必要条件を絞ってください。** 代案 (c) は今後の author 運用では有望ですが、今回の資料だけでは P1 を全面置換できません。(a) は統合契約を変え、(b) は確定済みの統合条件を緩めます。

指定4資料と関連コードを静的に確認しました。変更・pytest・撤去は実行していません。以下、`brief.md`・`materials.md`・`measurements-integration.txt` は指定 parent 配下、`plan.md` は指定 artifacts 配下を指します。

**1 / 対象：plan §2、brief (P2) / 種別：削除**

根拠：`plan.md:35–47,65–81,119–133`、`brief.md:29–32,61–62`。

- `registered_at`：削除。失うのは時刻の参考情報であり、作成時登録の証明ではない。
- `purpose` の5列挙：削除。失うのは用途ラベルと用途別登録拒否。撤去可否は統合証明・attached/detached の実体で決められる。
- `base_sha`：現行 P1 では削除。登録時祖先性の診断を失うが、A/B 判定はこの値を使っていない。代案 (c) なら変更集合の起点として残す。
- `owned_paths`：P1 を採る限り残す。削ると非祖先 author の正例を通せない。
- header の `job_dir`：manifest の配置から導出可能。`common_gitdir` も main と対象の実体照合で検証できる。`wave_worktree` は本体除外に必要。

削った後の残余リスク：用途・登録日時による診断は減るが、整合した manifest の偽造を防げない点は現案と同じ。

提案骨子：`schema / wave_worktree / entries[{path, branch, owned_paths}]` を基準とし、各 field に「撤去判定で使う箇所」を一つ以上要求する。

**2 / 対象：plan §2・§5、brief (P3) / 種別：削除**

根拠：`plan.md:55–81,176,184,258`、`brief.md:29–31,63–64`。

確定裁定が要求するのは作成時登録であり、登録専用 CLI ではありません。親だけが逐次更新するなら、**worker 起動前に親が JSON を Write し、remove 側で全検証する構成で足ります**。CLI を追加しても「作成時だった」ことは証明できず、登録・撤去の二重検証と fix 再登録テストが増えます。

削った後の残余リスク：手書き誤りや中断による不完全 JSON は撤去拒否となり、その回の残骸が残る。

提案文面：「manifest は親のみが逐次更新し、保存完了後に子を起動する。撤去時に構造・実体・exact path を検証する。」複数 writer が実在しない限り flock は不要です。

**3 / 対象：plan §3・§4、brief (P1) / 種別：縮約**

根拠：`plan.md:137–154,198–200`、`brief.md:48–52`。

退避の必要性とファイル配置を分けてください。

- `index.patch` は必要です。HEAD→worktree だけでは index 固有の編集を保存できません。
- `status.txt` 等を個別5ファイルとし、空 patch/tar まで必須にする理由は先例との一致だけです。metadata を一つにまとめても保存保証は変わりません。
- **main 非到達というだけで全履歴を pack するのは過剰**です。残す child branch から到達可能な commit は保持されます。
- 一方、HEAD reflog にしか残らない reset 前 commit は branch 保持だけでは救えません。

削った後の残余リスク：独立した履歴アーカイブを省くと、復元は保存 branch と共通 object database に依存する。

提案骨子：「子 branch は保持。HEAD reflog の各 commit が main または保持 branch から到達可能なら pack 不要。到達不能履歴がある対象は今回は拒否。」これなら pack writer・復元検査・追加 Git allowlist を削れます。detached も保持参照がなければ拒否します。

**4 / 対象：plan §3・§7、brief 不変条件4 / 種別：削除**

根拠：`plan.md:158–165,273–277`、`brief.md:8–11,52`。

子 branch の `-d` は今回の固定費削減に必須ではありません。問題の中心は約734 MB・26k files の worktree と走査対象の残置です。branch を常に残せば branch-recheck/delete と専用変異を削れます。D703 の「削除するなら `-d` のみ」は削除義務ではありません。

削った後の残余リスク：軽量な branch ref が蓄積し、将来の明示 cleanup 対象になる。

提案文面：「子 mode は branch を削除せず、保持した ref と SHA を報告する。wave 本体の branch 削除契約は維持する。」

**5 / 対象：plan §9、brief (P1)、代案 (a) / 種別：代案**

根拠：`plan.md:302–304`、`materials.md:50–55,72–77,280–286`、`tools/dev_wave_cleanup.py:652–675,946–972`。

`git merge -s ours` は blob 判定を省けますが、**既存検査だけで撤去できるわけではありません**。dirty 退避・manifest 束縛は依然必要で、tip の merge は reset 前 reflog 全体の祖先性を保証しません。

変更量は cleanup 判定では小さくなる一方、DW-S05-A の patch 統合に履歴統合を追加する変更が必要です。D2044 項16とは「記録とは別に親が統合する」と区別すれば両立しますが、ours merge 自体は内容採用を検査しません。

削った後の残余リスク：未採用内容も祖先化できるため、祖先性を内容統合の代用にすると未統合 author を通す。

提案：今回は不採用。採るなら「採用確認済み patch の履歴保持」として別途契約化し、掃除を通すためだけに merge しない。

**6 / 対象：brief (P1)、代案 (b) / 種別：代案**

根拠：`brief.md:14–15,29–31,48–49`、`materials.md:50–55`。

path 一覧＋祖先性だけは最も小さい manifest になります。しかし「非祖先でも退避して branch を残せば撤去」は、**統合済みであることを条件とする確定裁定と、未統合 author を拒否する完了条件に反します**。

変更量は最小ですが、D2044 項16の記録を撤去可能性へ読み替えてしまいます。非祖先を拒否する版なら安全側ですが、実測 author 群を通せません。

削った後の残余リスク：退避済みだが未採用の成果を、正常撤去として扱う。

提案：現裁定下では不採用。「保存」と「統合」を別条件として維持する。

**7 / 対象：brief (P1)、代案 (c) / 種別：代案**

根拠：`measurements-integration.txt:1–9`、`materials.md:72–77`、`tools/dev_wave_codex.py:71,234`、`tools/codex_worker_launch.py:2892–2900`。

**今後の author に限れば最も有望です。** 既存 `-o/--output-file` で job dir を指定でき、起動器のコード変更は不要です。報告を最初から子木外へ出しても、子木に残った全残差を commit する D2044 項16と矛盾しません。patch 統合も維持できます。

必要変更は出力先の運用指定と、`base_sha→HEAD` の全 changed path に対する tree entry 比較です。owned_paths・purpose は不要になりますが、削除・mode・type も比較し、reflog 保存は別途必要です。

削った後の残余リスク：報告以外の所有外編集が一つでもあると、内容を保存できても撤去できない。

提案：本 wave の新規 author で成立するかを確認する候補にする。ただし資料は不一致 path 名を列挙しておらず、「全差分が報告だけ」と独立検証できないため、現時点で P1 の全面置換は推しません。

**8 / 対象：plan §4・§5・§9、brief scope / 種別：scope 外**

根拠：`brief.md:19–25`、`plan.md:115,204–222,306–312`、`tools/mutation_worktree.py:408–409,534–541,947–961`。

現 plan は occupancy scanner・起動器・mutation tool の変更を提案していません。ここに架空の scope 違反はありません。ただし「全 producer の流入を閉じる」ために追加変更するなら別件です。

削った後の残余リスク：mutation 内部作成木の登録前中断と、外側 container の残骸は残る。

提案文面：「本 wave は親が作成時登録できる子木を対象とする。mutation tool 自己登録、外側 container 撤去、occupancy 判定変更、`/cleanup-branches` 改訂、起動器改訂は別件。」既存 `-o` の指定変更はコード改訂と区別します。

**9 / 対象：plan §8、brief (P5) / 種別：縮約**

根拠：`materials.md:136–142`、`tools/check_docs.py:628`、`orchestrator/tests/test_check_docs.py:9488,9686`。

DW-O28 は現物989 bytes。plan の989固定指摘は正しいですが、上限引き上げは不要です。次の全文は**見出し・空行・末尾改行込み989 bytes**に収まります。既存の変異対象文字列も保持します。

```text
## DW-O28 — land 後の自己撤去

親は`landed`/`already-landed`後、段9でmain worktreeへ移り、計算ノードjob終端後に実行（絶対path）。
`python3 tools/dev_wave_cleanup.py --main-worktree <MAIN> --wave-worktree <WAVE> --wave-branch <BRANCH> --tested-wave-tip-sha <TIP>`
本体はunoccupied・clean・tested tipの`refs/heads/main`祖先性・fold state不在・非primary・cwd対象外を要求。不成立・不明は停止。
wave の worktree・branch を撤去し、次 wave・ユーザー・`/cleanup-branches` へ引き渡さない。D703例外を作成時manifest登録済み子木へ拡張。先に各子をremove-childで非占有・統合確認、dirty退避後unlock・撤去しbranch保持。回収waveは旧manifestを明示。本体は最後。manifest外・不明・退避失敗は撤去しない。
F26の`git worktree remove`/`git submodule deinit`禁止。branchは`git branch -d`のみ。不能理由を報告し次waveのworklogへ記録。
```

削った後の残余リスク：子 CLI の全 option はこの節に載らず、実装の usage を参照する。

提案骨子：この本文を literal・synthetic fixture と同時更新する。byte 適合だけの確認であり、checker 合格は未確認です。

**10 / 対象：plan §5・§8、brief (P5) / 種別：縮約**

根拠：`docs/dev-wave/workers.md:19–27`、`materials.md:124–134`、`tools/check_docs.py:359,5330–5378`。

静的集計では L1.5 は **9660/9696 bytes、余裕36 bytes**。DW-S05-A は単節783 bytesでも無制限に追記できません。DW-O20 は996/1000なので変更不要です。

次の DW-S05-A 案は末尾空行込み817 bytes、差分+34、L1.5 は9694 bytesになります。

```text
## DW-S05-A — 段 5 所有と投入

所有path素集合の単位別worktree。依存完了後、所有path限定patch
（`git add -A`→`git diff --cached <base> --output=<f> -- <所有パス>`→`git apply`、`<base>`=子作成SHA。隔離sessionは`git -C`不可）だけ展開し並列投入。
worktreeは`-b`必須(detachedはmidflight rc=1)。
作成時job dirのmanifestへexact path・所有集合を登録後に起動。fixは同木を再利用。
投入先へcdせず直前に`tools/check_wave_startup.py --repo <abs> --mode midflight`。非0停止。
乖離量は非関門。gate実測NOTE≠0ならanchor再読。
起動器はauthor/fixの全残差を終端commit、待ち手は`--commit-worktree <abs>`を指定。記録のみ(D2044項16)。
codexは`reasoning=medium`、`sandbox=workspace-write`。
```

削った後の残余リスク：残り2 bytesなので、追加説明は再縮約が必要。

提案：登録 CLI の説明増設をやめ、この縮約で収容する。D730/D782（`docs/decisions.md:28560,30058`）の増枠段階には達しません。資料の「194本」「212本走査」「author4本一致」を、独立した文書予算起因の実害3例として数えることもできません。

**11 / 対象：plan §6・§7 / 種別：縮約**

根拠：`plan.md:213,230–260,268–275`、`orchestrator/tests/test_dev_wave_cleanup.py:57–88,1534–1553`。

tmp repo fixture の方針は妥当で、実 repo の状態を読む node を増やす提案はありません。ただし **tmp repo だから合計数秒とは断定できません**。実 scanner、複数 CLI、復元 checkout、各 phase 故障を全 node で繰り返す費用は未計測です。

削った後の残余リスク：専用機構を削った箇所の個別診断被覆が減るが、残す受理・拒否境界は維持する。

提案骨子：

- 登録 CLI を削り、登録側と remove 側の同型負例の重複を削除。
- branch 削除変異を削除。正例で branch 保持を確認。
- 実 scanner 成功は dirty 統合正例に統合。
- phase 故障は新経路固有の backup と admin 再検査を重点化。既存経路を通るだけの重複 node は追加しない。
- 変異は exact entry、統合恒真、空集合、backup省略、占有省略、realpath、admin binding の**7件**。

4ファイルという数だけでは1 author単位の規模は保証されません。登録・pack・branch削除を削った構成なら、1単位に収める見通しが改善します。

**12 / 対象：plan §9、brief (P6) / 種別：削除**

根拠：`plan.md:300,314,320` と `materials.md:31–41`。

plan の「materials の D2148 項9 は T-2051／B-4」という指摘は誤りです。今回の射影は **T-2778、項9、決定(iii)** と明記しています。

削った後の残余リスク：今回読んでいない別版との不整合までは判断しない。

提案差分：§9・総括からこの出典不整合 finding を削除。P6 の番号未確定時の表記方針は維持する。

**13 / 対象：brief 決定 fragment、plan §2–§4 / 種別：縮約**

根拠：`brief.md:29–33,61–67`、`materials.md:13–17,35–41,50–55,365–375`。

決定 fragment に必要なのは次の範囲です。

- **対象**：wave が作成時に job dir の manifest へ exact path 登録した子木。
- **条件**：非占有、author 成果の main 到達または wave 統合、dirty 退避完了、manifest 外・判定不能拒否。
- **置換範囲**：D703 の対象拡張と D2148 項9(iii) の子木自動撤去禁止部分。
- **維持**：stale lock 推定禁止、F26、終端 commit は記録のみ、branch 削除制限。
- **却下案**：周期 sweep、位置・名称による包括削除、記録だけを統合とする案。

削った後の残余リスク：CLI・退避配置は実装文書を参照する必要がある。

提案：schema 名、purpose 値、timestamp、rc 表、pack 形式、phase 名は決定へ持ち込まない。P1 の owned_paths 比較を採るなら、それが**どの対象集合を統合済みと認める条件か**は明記し、確定裁定の逐語と混同しない。

**14 / 対象：brief (P1)・自己実測、plan §3 / 種別：縮約**

根拠：`brief.md:58–60,84–85`、`measurements-integration.txt:1–9`、`plan.md:126–133`。

「author4本の所有 blob 一致」から全 producer の撤去方式は導けません。

- 1行目の t2484 は `anc_parent=None`。4本すべての親祖先性 False を、この出力は裏付けません。
- 測定出力は一致件数だけで、owned_paths 一覧・不一致が報告だけという根拠がありません。
- probe 3本は一致ゼロ。P1 の所有集合をどう定めてもよい根拠にはならない。
- scratch/freeze は親との全一致を観測していますが、用途ラベルから所有集合は決まりません。
- mutation container は測定9本に含まれず、detached・dirty・外側 evidence を持つ別型です。
- author でも reset 前履歴、所有外ソース編集、統合後に親側で修正された path は今回の成功型から外れます。

削った後の残余リスク：probe・container 等が保留となり、残骸流入を全面的には閉じない。

提案文面：「P1 は所有契約を固定した author/fix の観測に基づく限定方式。probe・scratch・mutation container への成立は未確認。今回の完了は author 正例と必須負例の確認に限り、全 producer の恒久回収完了とは報告しない。」