# [T-2593] 静的 tail 本走の投入経路を配線した

2026-09-14。branch `worktree-dev-wave-t2593-tail-formal-submission`。
基点 local main `af3762d62`、受入時の tested main `8daf52cfb` / tip `200fa7ed9`。

## 0. 依頼と、実際に起きたこと

依頼は「本走 driver は着地済みだが、Pegasus の投入経路が新しい走行種別を受理しない。
そこを配線する。投入はしない」だった。配線そのものは素直で、実際に時間を使ったのは
**既存 3 系列の挙動を 1 bit も変えずに新しい枝を足すこと**と、
**足した検査が本当に効くかを確かめること**である。

本走の投入は行っていない。依頼の scope 外である。

## 1. 「既存 3 系列を変えない」は文字どおりには達成できなかった

親 brief は不変条件として「既存 3 系列の観測可能な挙動を 1 bit も変えない」と書いた。
段 3 の敵対相談がこれを壊した。

**投入 script が job へ渡す環境変数には、job script 自身の SHA-256 が入る。**
本 wave は job script を編集するので、旧 3 系列の起動 argv に現れるこの値は必ず変わる。
したがって「旧系列の argv を bytes で完全一致比較する」テストは、書いた瞬間に赤か、
値を潰して恒真かのどちらかにしかならない。

裁定として比較契約を書き直した。**可変値は消さず、その場で正しさを検証する** (D 参照)。

- job script の SHA は、現行 job script の実 bytes を読んで sha256 を取り、それと一致すること
- 投入 nonce は 3 job と manifest 事象で同一であること
- group ID の時刻部は、起動の直前と直後に取った UTC の窓に入ること
- 同じ引数で 2 回起動して group ID が異なること

残る全部 (環境変数名・値・順序、3 workload の fan-out、出力 path の組み立て) は完全一致。

段 6 のレビューはこの契約でもまだ足りない点を 1 つ出した — group ID の PID 部が実 PID かは
見ていない。`$$` を `$(( $$ + 1 ))` にしても通る。ただし一意性は保たれ receipt の衝突は
起きないので、成果物への影響を 1 行で書けない。nit として記録し、直していない。

## 2. 正規化が、要求したのとは別の directory を指していた

**段 6 のレビューが読解で見つけ、親が実測で対照つきに確認した。**
投入 script は探索走の campaign path を `realpath` で正規化するが、出力を `$( )` で受けていた。

shell の command substitution は**末尾の改行をすべて取り除く**。したがって、名前が改行 1 文字で
終わる directory を渡すと、正規化後の値はその改行を失い、**同名で改行なしの別 directory** を指す。
文字集合の検査 (`^[A-Za-z0-9._/-]+$`) は改行が既に消えているので当然通る。
leaf が symlink でないことの検査も、`.../link/.` のように末尾を付ければ回避できる。

親の実測 (同じ入力・同じ 3 引数で、修正前後を比較):

- 修正前の版 (`c5f51443b` の bytes) は探索走の検査を**通過して先へ進んだ**
  (その後 job script の探索で落ちた。これは一時 copy から起動したため)
- 修正後は `resolved explore campaign contains characters unsafe for qsub -v` で rc=2

直しは、`realpath` の出力に番兵を 1 文字足してから `$( )` に渡し、番兵と `realpath` が付ける
終端の改行だけを取り除く形にした。これで path 自身の末尾改行は残り、既存の文字集合検査が働く。

**同じ穴が既存の `--output-parent` の正規化にもある。** そこを直すと旧 3 系列の受理集合が
変わるので触っていない。新しい持ち越し課題として起票した。

## 3. 集団報告の入口は、新しい実行体を作らずに置いた

依頼の元の起票は「3 走の成果物を 1 集団として集める投入側の入口も要る」と書いている。
素直に読めば `tools/pegasus/` に薄い shell を 1 本置く形になる。**そうしなかった。**

- `tools/pegasus/` 配下に実行体を置くと、admission registry へ実行場所の分類を宣言する必要が
  生じる。`orchestrator/tests/test_hooks.py` の
  `test_bash_pegasus_execution_inventory_is_synchronized` が、拡張子・実行 bit・shebang の
  いずれかを持つ file の集合と registry key の集合の一致を要求する (親が現物で確認)。
- 本 wave には集団報告を実際に走らせる材料 (3 本の完走した campaign) が無く、その分類を
  実測で裏づけられない。同日 main へ着地した裁定 (全件 第 18 回 項 7) が
  「実測が無いまま class を動かさない」「対象を限った入り口は今は作らない」を定めている。
- 置き場所をずらして inventory 検査を避ける案は、不正直なので採らない。

代わりに、3 走を 1 集団として束ねる仕組みが**既に 2 箇所に在る**ことを使った。

- 投入 receipt の group id と workload ごとの出力 root
- 本走 driver の `report` subcommand が 3 つの campaign lock 間で集団の同一性を突き合わせる経路

欠けていたのは、前者から後者への**乖離しない手順**である。それを
`docs/b10-backoff-static-tail-submission.md` に置き、その手順の argv を**文書から抜き出して**
driver の CLI へ通すテストで固定した。文書が壊れればテストが赤になる。

**保証しない範囲:** shell の wrapper を作っていないので、wrapper の終了コード伝播という検査対象は
無い。段 6 のレビュー B はこれを must-fix として出したが、上の理由で不採用にした。

## 4. 変異 — 11 件を事前登録し、11/11 KILLED

`mutation-spec.json` / `mutation-report.json` が台帳、`mutation-probe-*.json` が probe 走である。
基底は PASSED (rc=0、失敗 node 0、28.56 秒)。

| id | 変異 | 期待 node 数 | 結果 |
|---|---|---|---|
| M1 | job が新 driver でなく旧 driver を起動する | 6 | KILLED |
| M2 | 完走に要する genome 数を 8 から 5 へ | 3 | KILLED |
| M3 | 要求する execution 成果物を旧系列の stem へ | 3 | KILLED |
| M4 | 投入が探索走 campaign を job へ渡さない | 2 | KILLED |
| M5 | 事前登録 commit の検査を何でも通す形へ | 11 | KILLED |
| M6 | 旧 3 種別が新 2 flag を受理する | 18 | KILLED |
| M7 | 新 driver へ `--run-kind` を渡す | 6 | KILLED |
| M8 | 新種別を extended の追加解析経路へ流す | 4 | KILLED |
| M9 (正例) | 妥当な 40 桁 commit を弾くよう検査を狭める | 4 | KILLED |
| M10 | 入力検査の直後に環境変数を消す | 2 | KILLED |
| M11 | 投入 receipt の schema 版を上げる | 6 | KILLED |

MISMATCH 0・SURVIVED 0・TIMEOUT 0。期待 node は probe 走 (全件 SURVIVED 登録) で集めた
観測 node の完全集合であり、本走はその完全一致だけを KILLED として数えている。

**M9 を入れた理由。** 受理を広げる方向の変異だけでは、「検査が厳しくなりすぎて正常な投入が
通らなくなる」壊れ方を見逃す。M9 は妥当な入力を弾く変異で、正常経路のテスト 3 本と
負例 1 本が反応した。

**M10 は段 6 の fix が足した検査が捕らえた。** レビュー A が「入力検査と driver 起動の間を
テストが素通りする」と指摘し、その具体例として挙げた注入がこれである。

## 5. 実装子は 5 名とも「実装済み・未実走」と申告した

段 5 の 2 名と段 6 の fix 3 名は、いずれも sandbox に scheduler の実行 file が無く `qstat -Q` が
拒否されて `rc=16` となり、テストを 1 件も走らせられなかった。
**5 名とも `closed` と申告せず、正直に「実装済み・未実走」と書いた。** 実走はすべて親が行った。
F964 と同じ型である。

段 6 の fix 子 1 名は、指示された修正が**同じ wave で書かれたテストの期待値と衝突する**ことを
見つけ、「既存テストの期待値を変更しない」契約に従って何も編集せずに停止した。
親がその期待値を誤りと裁定し、変更を許可する範囲を名指しして投げ直した。
この停止は正しい判断である。握り潰されていたら、旧 3 系列の終了コード集合を広げる変更が
黙って land していた。

## 6. 検査の限界 (主張しない範囲)

- **job script の中間区間はどのテストも実行しない。** 入力検査から driver 起動までをすべて
  走らせるには PBS と実測が要る。テストは実 source から断片を抜いて連結している。
  中間へ `exit 2` を入れる改変は検出できない。
  **この穴は本 wave 以前から同型で存在する** — 既存 2 系列のテストも同じ形で断片を抜いている。
  本 wave が作った欠陥ではない。補いとして、新しい 2 つの環境変数が中間区間で壊されないことを
  静的に検査した (出現位置の集合を固定する形。静的検査であることは test 本体に明記してある)。
- **本走を実際に投入した実績は無い。** 手順は配線と CLI の実物から書いた。
  計算ノードで driver が事前登録 commit を解決できるかは、`git` が job script の必須 command
  一覧に既に入っていることと、`load_preregistration()` が使う git 操作
  (`rev-parse --verify` / `merge-base --is-ancestor` / `show <commit>:<文書>`) を読解で辿り、
  fetch を伴わないことを確かめたところまでである。

## 7. 既存 3 系列を変えていないことの根拠

- 既存テストが逐語で pin している文字列 (行継続を含む 2 行の条件式 2 本、環境変数の組み立て行、
  finalizer の分岐と genome 数、`run_kind` の出現回数 3) は 1 byte も変えていない。
  新種別の分岐は既存の条件式へ足さず、別の条件式として書いた。
- 既存テストで変えたのは出現回数 2 箇所だけ。新 driver が cache と被験木を指定するので
  2 から 3 になる。理由を各 1 行のコメントで書いた。
- 旧 3 系列の qsub argv と投入 receipt を、可変値を検証しながら完全一致で比較するテストを新設した
  (M11 と M6 がこれを裏づける)。
- テスト関数名の集合が基底と一致することを親が突き合わせた (既存テストの削除・改名はゼロ)。

## 8. 実測した数字

- 基底 (`test_backoff_extended_sweep.py` + `test_hooks.py`): 523 passed / 1 skipped
- 配線実装後の焦点走 (上記 + 新規 2 file + `test_plain_runner_coverage.py`): 685 passed / 1 skipped
- 段 6 fix 後の同じ焦点走: **702 passed / 1 skipped** (rc=0)
- 変異本走: 11/11 KILLED、基底 PASSED
- 受入全走: `verdict = child-green`、red 0 / flake 0、tested main `8daf52cfb` / tip `200fa7ed9`
- `python3 tools/check_docs.py` rc=0、全史 provenance 監査 9811 件で新規違反なし (docs commit 時点)

## 9. エージェント工数

Codex 子 11 本 — plan 1 / consult 2 / author 2 / review 2 / fix 3 / focus 1。すべて `gpt-6-astra`、
`reasoning=medium`。fix の 1 本は既存期待値との衝突を報告して編集ゼロで停止し、
親が許可範囲を名指しして投げ直した (工数としては 3 本のうち 1 本が空振り)。
