# Git ログ不一致の原因分析と自動復旧フロー

**日付:** 2026-06-30
**一文サマリ:** エージェントが起こしていない理由で git の log/reflog が期待と食い違う原因を網羅し、各々の自動解決可否と復旧フローを定める。**背骨の原則は「内容(作業)が失われていなければ破壊的修復(reset/rebase/amend)をしない」。**

---

## 1. 背景

本レポートは「チェックポイントから戻すロジックの検証」テスト中に観測された事象を起点とする。エージェント(Claude)が `git add`/`git commit` しかしていないのに、reflog に身に覚えのない操作が現れた:

- 自分が発行していない `reset: moving to <hash>` / `commit (amend)` / `commit: commit前 <subject>`(スナップショットコミット)
- 自分の commit メッセージが「commit前 dd28ada docs: …」のような別物に化けた
- `git hooks` は空・`core.hooksPath` 未設定 → フック起因ではなく**外部の独立プロセスが直接 git を操作**
- 一方 working tree は clean・**内容の損失はゼロ**(スナップショット退避は機能)
- 副作用でテスト出力が一過性に混線(stability テスト数が 20/8 と食い違って見えた)

**危険だった失敗モード:** エージェントはこれを「履歴が壊された」と誤認し `soft reset` での自力修復を提案した(実行はせず、ユーザー介入で停止)。**外部要因の不一致を自分のせいと誤認し、破壊的に自力修復しようとする**——これが本レポートで最も防ぎたい挙動である。

---

## 2. 原因カタログ

凡例 — 自動解決: ✅可 / ⚠️条件付き / ❌不可。内容損失: none(なし) / recoverable(退避済み) / possible-loss(損失あり得る)。

### 2.1 外部プロセス系

| 原因 | 機序 | 今回該当 | 内容損失 | 自動解決 |
|---|---|---|---|---|
| チェックポイント/スナップショット自動コミット | 外部が add+commit を挿入、退避/復元で reset/amend | **yes** | none | ⚠️ |
| 別エージェント/人間の並行作業 | 同一 repo で同時 commit/checkout、index 競合 | maybe | recoverable | ❌ |
| IDE Git 統合(auto-stage/commit/stash) | エディタ拡張が裏で stage/commit/stash | maybe | recoverable | ⚠️ |
| ウォッチャ/フォーマッタの working tree 変更 | 保存時整形が差分を生み add -A が巻き込む | no | recoverable | ⚠️ |
| pre/post-commit フック・CI 書き換え | フックが内容/メッセージを改変、bot が push | no(空) | none | ⚠️ |
| バックアップ/同期ツールの .git 破壊 | Dropbox 等が refs/index を不整合化 | no | **possible-loss** | ❌ |
| cron/定期ジョブ(自動 commit, gc) | 非同期ジョブが log/reflog/オブジェクトを変更 | maybe | recoverable | ⚠️ |

### 2.2 git 同期・状態系

| 原因 | 機序 | 今回該当 | 内容損失 | 自動解決 |
|---|---|---|---|---|
| origin の force-push/rebase 乖離 | upstream 書き換えでローカルが分岐 | no(push せず) | recoverable | ⚠️ |
| detached HEAD | ブランチ外でコミットが宙に浮く | no | recoverable | ✅ |
| index と working tree の不整合 | 部分 stage で見かけが食い違う | no | none | ✅ |
| submodule の pin と中身の食い違い | submodule 改変が親 status に出る | **yes(良性)** | none | ⚠️ |
| 複数 worktree の混線 | 別 worktree が同一ブランチを触る | no | recoverable | ✅ |
| packed/loose refs 不整合・gc 失効 | reflog 切れ・ref 消失 | no | possible-loss | ❌ |
| shallow clone の履歴欠落 | `.git/shallow` で過去が見えない | no | none | ✅ |

### 2.3 エージェント認知・並行タイミング系

| 原因 | 機序 | 今回該当 | 内容損失 | 自動解決 |
|---|---|---|---|---|
| Edit/commit の成否誤認 | ツール success を信じ実体未確認 | **yes** | none(再実行で回復) | ✅ |
| commit と外部 commit のレース | 横取りでメッセージ化け | **yes** | none | ⚠️ |
| .git/index.lock 競合 | 並行 git が lock を保持 | maybe | none | ⚠️ |
| 並行プロセスの stdout 混線 | 出力が混ざり数値が食い違う | **yes** | none | ✅ |
| 古い SHA/状態の記憶 | 要約前の記憶と現状が乖離 | maybe | none | ✅ |

---

## 3. 自動解決の決定木

```
[git log/reflog が期待と不一致]
        │
        ▼
(1) 自分起因か? ── reflog を読み、セッション内で自分が実行した git 操作と照合
        │           (自分は add/commit のみ? なのに reset/amend/別 commit がある?)
        ├─ 自分起因(誤操作) ──▶ 認知系フロー(§4-C): 実体を再確認し編集を再実行(非破壊)
        │
        └─ 外部起因 or 不明
                │
                ▼
(2) 内容は無事か? ── 【最重要ゲート・必ず読み取りのみ】
        │   git status --porcelain        (空 = working tree clean?)
        │   git diff HEAD                  (空 = HEAD と一致?)
        │   git show HEAD:<path> | grep    (自分の全変更が HEAD ツリーに在るか)
        │
        ├─ 内容に損失あり/疑い ──────────▶ ❌ 破壊的操作をせず即エスカレーション
        │   (作ったはずのファイルが無い /                (§5 のエスカレーション基準)
        │    HEAD に変更が欠落 / fsck エラー)
        │
        └─ 内容は無事(clean かつ全変更在中)
                │
                ▼
(3) 不一致は「履歴の見た目」だけか?
        │   (余分な commit前 / メッセージ化け / reflog の reset-amend)
        │
        ├─ はい(見た目のみ) ──▶ ✅ **触らない**。事実を記録して作業継続。
        │                          履歴整理(squash/drop/amend)は push 前に人間が、
        │                          または外部機構の停止後に行う。エージェントはやらない。
        │
        └─ いいえ(状態の実不整合: detached/部分stage/submodule/worktree)
                │
                ▼
(4) 非破壊で揃うか? ── §2.2 の ✅ 項目(branch 退避 / restore --staged /
        │              submodule update / worktree 移動 / unshallow)
        ├─ はい ──▶ ✅ 非破壊手順で是正(内容は working tree/退避に保持)
        └─ いいえ ─▶ ❌ 人間へ
```

**鉄則:** ステップ(2)を通過しない限り、いかなる `reset`/`rebase`/`commit --amend`/`checkout -- <file>`/lock 削除も行わない。これらは「内容が無事」を確認した上でも、外部機構が動作中は再レースを招くため、原則 push 前の人間操作に委ねる。

---

## 4. 自動化できる部分 / できない部分

### 自動フローに載せてよい(✅ 非破壊・決定的)
- **検出と切り分け**(全カテゴリ共通): reflog/status/diff/grep の読み取りで不一致を検出し、自分起因か外部かを切り分ける。
- **内容無事の立証**: `git status --porcelain` 空 + `git diff HEAD` 空 + 主要変更の `git show HEAD:<f>|grep` 在中確認。
- **A: 認知系の自己修復**: Edit/commit 直後の実体検証と再実行。出力混線は単独再実行+ファイル grep で確定。古い SHA は `git rev-parse` で読み直し。
- **B: 状態系の非破壊是正**: detached → `git branch` 退避後に戻る / 部分 stage → `git add`/`restore --staged` / submodule(誤) → `submodule update` / worktree 誤り → 移動 / shallow → `fetch --unshallow`。
- **C: 予防**: コミットは `git add <明示パス>` のみ(`-A` を避けてウォッチャ差分の巻き込みを防止)。

### 人間に残す(❌ または ⚠️ 判断要)
- **履歴の整理**(余分な commit前 の squash/drop、化けたメッセージの amend、外部機構由来の reset 痕の除去)。push 前に人間が、または機構停止後。
- **破壊的復旧**(reset/rebase/force、lock 強制削除、.git 物理破損の fsck 救済、gc 失効オブジェクト復元)。
- **並行性の意思決定**(別セッション/force-push でどちらの作業を正とするか)。
- **設定の是正**(誤動作するフック/フォーマッタ/同期フォルダ配置)。

---

## 5. エージェント向け実践チェックリスト

外部由来の git 不一致を見たら、上から順に:

1. **手を止める。** 反射的に `reset`/`rebase`/`amend` を打たない(これが最大の事故源)。
2. **自分の操作を思い出す。** このセッションで自分が打った git は何か(通常 add/commit のみ)。reflog の reset/amend/別 commit はそれと矛盾するか。
3. **読み取りだけで内容の無事を立証する:**
   - `git status --porcelain`(空か)
   - `git diff HEAD`(空か)
   - 自分の主要変更が HEAD ツリーに在るか: `git show HEAD:<path> | grep -c <token>`
   - テスト等の期待値も**単独実行+grep**で裏取り(出力混線に注意)
4. **内容が無事なら、履歴の見た目は触らない。** 「外部機構由来・内容は無事」と明記して作業を続ける。整理は push 前の人間に委ねる。
5. **内容損失の疑い(ファイル消失/HEAD に変更欠落/fsck エラー)があれば、即エスカレーション。** それ以上 git に書き込まない。
6. **外部機構が動作中である可能性を常に添える**(自分が整理しても再発しうる)。
7. **予防**: commit は明示パスで `git add`、ツールの success を鵜呑みにせず実体検証を挟む。

---

## 6. 今回の事例への当てはめ

| ステップ | 本件での結果 |
|---|---|
| (1) 自分起因か | ❌外部。自分は add/commit のみ、reflog の reset/amend/`commit前` は外部機構 |
| (2) 内容は無事か | ✅無事。`status --porcelain` 空、`diff HEAD` 空、全9変更が HEAD ツリーに在中(grep=1)、122 テスト緑 |
| (3) 見た目だけか | ✅はい。余分な `commit前`×3 とメッセージ化けのみ、実体差分なし |
| 判定 | ✅**触らない**。事実を記録して継続。履歴整理は push 前に人間 |
| 副作用 | テスト数 20/8 混線 → 単独再実行+grep で stability=8 が真と確定(誤報告を訂正) |

**もしこのフローに従っていれば**、ステップ(1)→(2)で「外部起因・内容無事」を即断でき、`soft reset` の提案(誤った自力修復)に至らずに済んだ。実際にはステップ(2)の確認が事後になり、一度 `soft reset` を提案してしまった——これが本フロー策定の動機である。

---

## 7. 限界・残課題

- **監査者自身の認知**: エージェントが「内容は無事」と判定する手順自体が誤りうる(grep のパターン漏れ等)。重要判断は複数の独立確認(status/diff/grep/test)を重ねて確度を上げるが、ゼロにはできない。
- **外部機構の透明性**: 本質的解決は外部機構(チェックポイント等)が**エージェント可視の git 履歴を汚さない**こと(別 ref / worktree / `.git` 外への隔離)。機構が透明・隔離される限り、本フローの大半は不要になる。フローはあくまで「機構が干渉してくる前提」での防御策。
- **possible-loss 系の自動化不可**: .git 物理破壊・gc 失効・force-push orphan は内容損失を伴い、自動修復は危険。これらは検出して人間に渡すのが唯一安全。
- **push 前提**: 本フローは「push 前でローカル整理が安全」を前提にする。push 済みで共有された履歴の是正は、影響範囲が広がるため別途人間の調整が要る。
