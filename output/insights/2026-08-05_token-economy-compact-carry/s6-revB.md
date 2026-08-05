## 総括

- must-fix は **5 件**。現状は **NO-GO**。
- 最重要 1: class 3 / rulings の末尾読者は compact stub の参照先を認識できない。
- 最重要 2: docs の「直前 entry」と正本所在が ordinal-gap 契約を一意に表していない。
- 最重要 3: 親実測の 3 赤は production 回帰ではなく、互いに異なる fixture 不備。ただし全件修正必須。

## MF-1 — class 3 と rulings の読者契約が未充足

[CLAUDE.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/CLAUDE.md:38) は class 3 に末尾 entry だけを読ませる一方、compact 書式の意味は [worklog.md:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/worklog.md:26) の冒頭にしかない。[dev-wave/SKILL.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/.agents/skills/dev-wave/SKILL.md:13) もその末尾から対象を選ぶ。

具体入力:

```text
末尾:
- [T-316] (181)

entry (181):
- [T-316] **P1・ユーザー裁定要**: ...
```

末尾行には `carry`、`参照`、`ユーザー` のどれもなく、`(181)` が worklog ordinal だと末尾だけからは確定できない。実際の旧形は [worklog.md:1757](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/worklog.md:1757) のように自己説明的だった。

[rulings.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/.claude/commands/rulings.md:13) の置換は、概念上は新旧両 stub を覆う。しかし compact 予約形を識別する文法が同 command にないため、[rulings.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/.claude/commands/rulings.md:15) の「ユーザー」抽出前に参照を解決できる保証がなく、単独では収集漏れを防げない。byte 数は旧版・現版とも **4,988** で、net-neutral 条件自体は満たす。

CLAUDE.md 以外の最小是正は、[spool_fold.py:1385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1385) が生成する各末尾 heading に固定 legend を付けること:

```text
### 次の一手 — `- [T-NNN] (N)` は worklog/archive の entry (N) を実体まで遡る
```

heading suffix は [spool_fold.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:54)、[check_docs.py:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:537)、[dev_waves/checker.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/dev_waves/checker.py:41) が既に受理する。固定 1 行のため、削減の大半も維持できる。これをしないなら CLAUDE.md の読取範囲変更が必要であり、冒頭 docs の追記だけでは tail-only reader に届かない。

**成果物影響:** 裁定待ち T が rulings 索引と次 wave の候補から脱落し、誤ったタスク選択・未裁定扱いを生む。

## MF-2 — `prior_ordinal` の docs 契約と正本所在が曖昧

[worklog.md:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/worklog.md:27) と [spool/README.md:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/spool/README.md:86) は N を「直前エントリ番号」とだけ説明する。しかし実装は、最初の fragment では現行 worklog 末尾、同一 fold の後続 fragment では直前に生成した entry を使う。[spool_fold.py:1806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1806)、[spool_fold.py:1825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1825)

具体入力:

```text
current latest = (5)
archive max    = (9)
new ordinal    = (10)
正しい carry  = - [T-001] (5)
ordinal-1 解釈 = - [T-001] (9)
```

この差は事前登録 M05 の本体である。[s4-ruling.md:74](/work/1/SFC/tanab/dev-wave-jobs/token-economy/s4-ruling.md:74)

正本所在も、[CLAUDE.md:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/CLAUDE.md:156) と [docs/README.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/README.md:22) は worklog 冒頭を指すのに、[worklog.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/worklog.md:17) は「形式の正本」を spool README に戻している。

是正は次のように一意化すべきである。

- 描画済み worklog の読取・carry 書式は worklog 冒頭を正本にする。
- spool README は fragment 文法と fold producer 契約の正本、と範囲を限定する。
- N は「行内に明示された参照先 ordinal」であり、最初は current tail、同一 fold 内では直前生成 entry、`new ordinal - 1` や global max から導出しない、と一度だけ定義する。

4 面の現在の文章に直接の新旧書式矛盾や全文複製はない。問題は、正本ラベルと「直前」の重複した曖昧さである。

**成果物影響:** gap 入力で `(9)` を出す実装が docs 適合に見え、T-001 不在なら次 fold が `carry-reference`、同 ID があれば誤本文 digest に束縛される。

## MF-3 — 既存 rotation 赤は fixture の byte 依存

判定は **(a) 無害な表現短縮に露出した fixture 不備**。rotation 契約の real 回帰ではない。

[test_spool_fold.py:1852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:1852) は limit 320 を固定する。親ログでは compact 後の projected bytes が **317** である。[s6-focused-tests.log:34](/work/1/SFC/tanab/dev-wave-jobs/token-economy/s6-focused-tests.log:34)

具体入力:

```text
limit = 320
compact projected = 317  → rotation なし
旧 carry projected = 317 + 22 = 339 → rotation あり
```

production の発火条件は従来どおり `len(rendered_worklog) > limit` のまま。[spool_fold.py:1867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1867) rotation 分割本体 [spool_fold.py:1631](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1631) にも差分はない。

正しい fix は、archive 側へ移動される seed entry (1) に十分な filler を加え、`全体 > 320` かつ `entry (1) 移動後 <= 320` を fixture で保証すること。current 側 entry (2) を膨らませると分割点が変わるため不適切。assert、閾値、skip は触らない。

**成果物影響:** 未修正では land が赤で止まり、迂回すれば D70 の archive/current 境界保存テストが失われる。runtime rotation 契約自体は壊れていない。

## MF-4 — ordinal-gap 新設テストは dirty canonical で apply を拒否される

[test_spool_fold.py:771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:771) で base commit 後に worklog と archive を書き換え、そのまま [test_spool_fold.py:782](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:782) で apply している。

具体入力:

```text
git base commit
→ docs/worklog.md を (5) に変更（dirty）
→ archive (9) を追加
→ plan は正しく `- [T-001] (5)` を生成
→ apply_fold は dirty target を拒否
```

実際の失敗は rotation assert ではなく `TransactionError` である。[s6-focused-tests.log:60](/work/1/SFC/tanab/dev-wave-jobs/token-economy/s6-focused-tests.log:60) 拒否は正しい fail-closed 動作。[spool_fold.py:2013](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:2013)

canonical gap fixture を commit してから fragment を作るのが正しい fix。clean preflight は変更しない。

**成果物影響:** baseline が赤のままでは M05 の ordinal-gap kill を受入証拠にできず、明示 `(5)` の次 fold 解決が未証明になる。

## MF-5 — rotation-chain 新設テストの limit が第 2 entry を収容しない

[test_spool_fold.py:885](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:885) は limit を第 1 rotation 後 current の長さそのものに設定している。親ログでは **126 bytes**。[s6-focused-tests.log:151](/work/1/SFC/tanab/dev-wave-jobs/token-economy/s6-focused-tests.log:151)

具体入力:

```text
limit = compact carry entry (3) 単体の 126 bytes
第1 fold: entry (1),(2) を archive、entry (3) は 126 bytes → 成功
第2 fold: より長い更新 entry (4) を追加
entry (3) を移しても header + entry (4) > 126 → rotation-capacity
```

第 1 rotation、archive `[1,2]`、current `(3)`、compact `(2)` はすべて通過済みで、失敗は第 2 plan の capacity 判定である。[s6-focused-tests.log:119](/work/1/SFC/tanab/dev-wave-jobs/token-economy/s6-focused-tests.log:119)

正しい fixture は、単独の entry (3)/(4) が収まる余裕を持つ limit を選び、entry (2) を十分大きくして「entry (1) だけ移動では不足、(1),(2) 移動なら収まる」を保証すること。production 閾値や assertion は触らない。

**成果物影響:** 未修正では rotation→archive→compact chain の end-to-end 受入証拠が成立せず、archive 越し resolver の退行を防げない。

## 旧書式 consumer の全数確認

歴史記録を除く `git grep` の旧書式関連 match は以下だけだった。

| 面 | 判定 |
|---|---|
| [spool_fold.py:1153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1153) | 意図した legacy parser。残す必要あり |
| [test_spool_fold.py:286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:286)、[同:575](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:575)、[同:2015](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:2015) | legacy 互換・混在・golden の意図した fixture |
| [spool/README.md:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/spool/README.md:88)、[spool/worklog/README.md:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/spool/worklog/README.md:83) | 凍結 legacy 互換の説明 |
| [spool/worklog/README.md:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/spool/worklog/README.md:27) | fragment の `carry` 操作本文で、canonical 旧書式ではない |
| hooks、phase doc、他 tools | 旧書式 literal の生存 consumer なし |

`tools/dev_waves/checker.py` は [checker.py:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/dev_waves/checker.py:153) で ID だけを抽出するため compact 形でも安全。literal grep では見えない semantic consumer が MF-1 の class 3 / rulings である。

## 実装子報告の波及候補

- `tools/dev_wave_land.py`: runtime 波及はあるが追随編集は不要。[dev_wave_land.py:1196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/dev_wave_land.py:1196) で同 checkout の engine を読み、[同:1800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/dev_wave_land.py:1800) と [同:1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/dev_wave_land.py:1440) で plan/apply を委譲する。旧 literal はない。実 fold integration test は最終受入で再走対象。

- `check_docs` import: carry 意味への波及なし。[spool_fold.py:1589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1589) が import するのは rotation 定数 [check_docs.py:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:104)。D70 は [check_docs.py:521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:521) で compact 行の先頭 ID を既に抽出する。

- real-repo 共有 fixture: 波及あり、差分内で追随済み。[test_spool_fold.py:1933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:1933) が実 corpus を読み、[同:2014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:2014) が凍結 legacy golden だけを期待 compact 形へ変換する。archive bytes 自体は書き換えていない。

現行 worklog + archive の exact compact 予約形は静的検索で **0 件**。pytest は実行しておらず、テスト結果は親提供ログだけを根拠にした。