# [T-2146] 段 4 裁定

## 0. 手順の確定 — D374 ではなく D427

親 brief の N1 は誤りだった。段 2 と段 3 の両レンズが独立に倒し、親も実測で確かめた。

- 実測 (`probe_guard.py`): 現行 HEAD では `hooks/guard_write.py` / `hooks/guard_bash.py` への
  Write・apply_patch・Bash 書込みがすべて拒否される。D374 の手順 2・3 は現行 main では実行できない。
- 正本は **D427** (2026-08-16)。有効化前 commit を base にした**第 2 worktree**で実装し、
  親が統合 commit を作り、wave branch へ `git merge` で持ち込む。テストは編集可能な wave worktree 側の
  別の実装子が書く (所有を分ける)。
- **D428** も同時に発火する。受理集合を変える wave は、wave 前後の実装へ同一コマンド集合を通し
  **`deny → allow` の反転 0 件**を実測して記録する。本 wave の必須成果物に加える。

**実測で確定した第 2 worktree (W2):**
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-guard-author` @ `d92800f49`
(= `84e5e0b0` の 1 つ手前 = guard_write に hooks 判定が入る直前)。

- `probe_w2.py` 実測: W2 では `hooks/guard_write.py` / `hooks/guard_bash.py` /
  `orchestrator/tests/test_hooks.py` への apply_patch がすべて **allow**。
- `.codex/hooks.json` は W2 の HEAD と wave tip で **byte 一致**。配線 drift は起きない。
- **モデル権威の食い違いは無い。** 親が段 1 後に「W2 では高額モデルになる」と書いたのは
  古い記憶に基づく誤りで、実測では wave tip も W2 も同じ `gpt-5.6-sol` を導出する
  (D682 が D514 を supersede 済み)。W2 側は author の effort を導出しないので、
  現行権威が定める `xhigh` を親が明示して渡す。

## 1. 設計原則 — 既存の防護判定と同型にし、新機構を作らない

依頼は「本題の防護追加だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
段 3 が出した real 所見は次の 2 種に割れる。

- **(a) 既存の防護対象 tree が既に持っている性質を、発行主体 root が持っていない** → 採用。
  同じ機構を新しい subtree へ適用するだけで、新機構でも一般化でもない。
- **(b) 既存の防護対象 tree にも同じ穴がある** → 不採用。閉じるには新しい機構が要り、
  発行主体だけ閉じると設計が非対称になる。README に残余として明記し、裁定パッケージへ回す。
  族一般化は `DW-G03` により独立 2 例が要る。

## 2. 所見の裁定

### 採用 (scope 内、must-fix)

| # | 出所 | 内容 | 採用理由 |
|---|---|---|---|
| S1 | A1 / B5 | **祖先の破壊**。`rm -rf /work/1/SFC/tanab` を拒否する。`_inside(candidate, root)` の一方向だけでなく、`_inside(root, candidate)` 側も見る | 既存 `_tree_violation` は campaign tree と ccbench で祖先を明示的に捕捉している。同型 (a) |
| S2 | A3 | **部分 glob**。`dev-wave-authorit?` のようにメタ文字前のリテラル prefix で重なりを判定する | 既存 `_tree_violation` の glob 規約と同型 (a) |
| S3 | A8 / P1-b | **inode alias**。発行主体 root 配下の regular file の (st_dev, st_ino) 索引を張り、hardlink 別名への書込みを捕える | 既存 `_HooksInodeIndex` が hooks subtree に対して持つ機構と同型 (a)。親 brief の「0700 だから不要」は両レンズが独立に倒した |
| S4 | A-巻き込み 2 | **削除・移動元は最終要素を解決しない** (`resolve_final=False`)。`rm /tmp/alias` (alias 自身の unlink) を巻き込まない | 既存 `classify_path` の規約をそのまま使う (a)。守らないと過剰拒否になる |
| S5 | 段 2 / P1-c | **挿入点**。`_hooks_tree_violation` の実呼出し 3 箇所 (tree / 引数 / redirect) に加え、fast path、`main()` 例外 fallback、`perf` 専用分岐、builder 例外の分離まで足す | 段 2・段 3 が独立に「4 箇所では足りない」と実コードで示した |
| S6 | 段 2 | **境界判定**。lexical と canonical の両側で `_inside` の path 要素境界を使う。`_repo_relative*` は repo 外 path で絶対性を失うので使わない | 兄弟 directory (`…-copy`, `…2`) と job dir を巻き込まないため |
| S7 | 段 2 / P1-a | 発行主体 root は argv・環境変数・repo root から導出しない固定 module 定数 | 参照側 2 箇所と同型。両レンズが支持 |

### 不採用 (scope 外、README 残余 + 裁定パッケージ)

| # | 出所 | 内容 | 不採用理由 |
|---|---|---|---|
| R1 | B2 / C5 / N3-b | 秘密鍵の**読取り**と署名能力は閉じない。D906 の「偽造不能」は本 wave では成立しない | 読取り防護は新機構。`guard_read` は fail-open の衛生層で流用できない。裁定パッケージ 1 |
| R2 | A5 / A6 / A7 / B6 | `pushd`、`env --chdir`、subshell・`&&`/`||` の制御フローによる cwd 追跡漏れ | 既存の cwd 追跡も `cd` だけを直列に見る (b)。shell 状態模型の新設が要る。裁定パッケージ 2 |
| R3 | A4 | ANSI-C quote (`$'...'`) で綴りを割った path | 既存の防護 path 判定も同じ (b) |
| R4 | A2 | archive 内容・source basename から親 directory 経由で発行主体を生成・上書き | 既存の防護 tree も archive 内容は見ない (b) |
| R5 | A9 | `perf -oFILE` の密着短 option | 既存の `perf` 分岐が `-o FILE` と `--output=FILE` しか見ない既存欠陥 (b)。**failures 台帳へ記録**する |
| R6 | A10 / B7 | 内部例外 fallback は exact literal だけを見るので canonical/hardlink alias は fail-open | 既存 fallback も同じ (b) |
| R7 | A11 / B3 / B4 | script 経由・変数展開・persistent shell・別 process・同一 uid・cron・IDE・MCP・設定面・path literal を持たない Git 操作 | 既存 README が自認する限界 (b)。同じ精度で再掲する |
| R8 | A-巻き込み 1 | `cp <authority>/pub /tmp/x` は拒否されるのに `cat … > /tmp/x` は通る非対称 | 既存の防護 tree でも同じ (b)。**failures 台帳へ記録**する |
| R9 | A-巻き込み 3 / 4 | 実行されない `cd` の後続、authority path をデータとして表示する opaque command の過剰拒否 | 既存の保守的拒否と同型 (b) |

### 親 brief の訂正

- N1 は誤り → D427 へ差し替え (上記 0)。
- N2 の「凍結 pin 閉包 1 件」は機構が 1 つという意味。束縛される file は 5 本 (B/C2 の指摘どおり)。
- N3-a (読取り防護は scope 外) は両レンズが支持。N3-b (それでも D906 は未完) を受け入れ、
  README と worklog に明記する。
- P1-b・P1-c・P1-d は倒された。P1-b は inode 索引を採用する形へ改める。
- 「編集面の衝突なし」は着手時点の snapshot であり実装開始時までの保証ではない (A の指摘)。
  段 6 の受入直前に取り直す。

## 3. 実装単位 (D427 の所有分割)

| 単位 | 場所 | 所有 path | 順序 |
|---|---|---|---|
| A1 | W2 | `hooks/guard_bash.py` | 1 番目。完了後に親が commit |
| A2 | W2 | `hooks/guard_write.py` | 2 番目。**最後の 1 回**で書く。完了後に親が commit |
| B | wave worktree | `orchestrator/tests/test_hooks.py`、D428 反転検査 runner | A2 の commit 後 |
| 親 | wave worktree | `hooks/README.md` (exact README 例外)、fragment | 最後 |

A1 を先にするのは、W2 の `guard_write.py` が P 版である間だけ hooks/ への apply_patch が通るため。
`guard_write.py` を書き換えた瞬間に W2 でも hooks/ が施錠される。

A1・A2 とも **現行 wave tip の file 全文を base** にする。W2 の作業ツリーにある版は 3 週間古いので
使わせない。親が現行版を job dir へ射影して渡す。これにより B1 の内容は「現行 + 追加」となり、
wave branch への merge が退化して衝突しない (親が blob hash で検算する)。

## 4. 変異事前登録 (DW-M01)

実装前に登録する。各変異は「同じ入力を拒否する層が前後にも内側にも無い」ことを実装後に確認し、
確認できなければ登録から外して実効 gate へ再照準する。

### 拒否側 (受理集合を縮める側の歯)

| ID | 変異位置 | 期待赤 |
|---|---|---|
| M1 | `guard_write.classify_path` の発行主体判定を削除 | 発行主体 root への Write / Edit / MultiEdit / NotebookEdit が allow へ |
| M2 | `_decide_apply_patch` 経路の発行主体判定を削除 | apply_patch の Add / Update / Delete / Move to が allow へ |
| M3 | `guard_bash._tree_violation` の発行主体 OR を削除 | `rm -rf <authority>` が allow へ |
| M4 | `guard_bash._argument_hits_protected` の発行主体 OR を削除 | `cp /tmp/x <authority>/key` が allow へ |
| M5 | `guard_bash._redirect_hits_protected` の発行主体 OR を削除 | `cat /tmp/x > <authority>/key` が allow へ |
| M6 | `decide()` の fast path から発行主体 trigger を削除 | 発行主体だけを名指す writer が精査へ入らず allow へ |
| M7 | 祖先判定 (`_inside(root, candidate)`) を削除 | `rm -rf <authority の親>` が allow へ |
| M8 | glob の literal prefix 判定を削除 | `rm -rf <authority の末尾を ? にした形>` が allow へ |
| M9 | inode 索引を削除 | 発行主体内 file への hardlink 別名書込みが allow へ |
| M10 | canonical (realpath) 側の判定を削除、lexical だけ残す | 発行主体を指す symlink 経由の書込みが allow へ |
| M11 | lexical 側の判定を削除、canonical だけ残す | 未存在 path (これから作る file) への書込みが allow へ |
| M12 | `main()` の例外 fallback から発行主体 literal を削除 | 内部例外時に発行主体 payload が rc=0 へ |

### 過剰拒否側 (承認外の拒否を検出する正例)

| ID | 変異位置 | 期待赤 |
|---|---|---|
| M13 | `_inside` の path 要素境界を部分文字列一致へ弱める | 兄弟 directory (`…-copy` / `…2`) への書込みが deny へ (過剰拒否) |
| M14 | 削除・移動元の `resolve_final=False` を `True` へ | 発行主体を指す symlink 自身の unlink が deny へ (過剰拒否) |
| M15 | 読取り判定を外し、発行主体に触る全コマンドを拒否 | `cat <authority>/公開鍵` が deny へ (過剰拒否) |

## 5. 追加の必須成果物

- **D428 反転検査。** wave 前 (`d92800f49` ではなく現行 wave tip の guard) と wave 後の実装へ
  同一コマンド集合を通し、`deny → allow` の反転 0 件を実測して worklog に記録する。
  runner は repo 外 (job dir) に置く。
- **hooks/README.md の残余記述。** R1〜R9 を既存の残余記述と同じ精度で書く。
  「完全ロック」「AI は署名を偽造できない」「D906 を満たした」とは書かない。
  主張の上限は「信頼済み PreToolUse が観測する直接書込み面から発行主体 subtree を追加で除外した」。

## 6. 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

1. **D906 の実効層。** 書込みだけを閉じても、同一 uid の AI が秘密鍵を読んで署名できる。
   真正性を機械的に主張するには、鍵と署名実行権限を別 OS principal / 別 host / hardware signer へ
   置く必要がある。本 wave の着地は「直接書込み面の縮小」までで、D906 の完了根拠に数えない。
2. **shell 状態模型。** `pushd` / `env --chdir` / subshell / 条件実行の cwd 追跡は、現在どの防護対象
   でも成立していない。閉じるなら全防護対象へ同時に入れる独立 wave が要る。
3. **既存欠陥 2 件** (R5 `perf -oFILE`、R8 copy-out 非対称) は failures 台帳へ記録する。
   修正は発行主体に限らない族の問題なので別 wave。
