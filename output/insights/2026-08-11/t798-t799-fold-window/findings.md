# 実測結果 — [T-798] / [T-799]

測定 checkout: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-fold-window`
HEAD `9abd23daa0dd885a9b1121bddd34b7c44c441428` (local main と乖離 0)
probe: 同 wave dir の `probe/` (repo 外)。log は `probe/*.log`。

本番 module は実体を import している (`tools/dev_wave_land.py`, `tools/spool_fold.py`)。
合成なのは (i) 台帳の中身、(ii) `tools/check_docs.py` / `tools/check_ai_provenance.py` の実装、
(iii) repository が tempfile 配下であること — の 3 点である。

**主張の射程 (敵対レンズ A の所見 2 を受けて縮小した)。** 本 probe が示せるのは
**「本番 source の狭い実行順序を通した」**ことまでである。checker の実装・branch 名・
repository tree はいずれも制御フローの**入力**であり、fixture の stub checker は常に rc=0、
probe branch は `wave/codex-*` (非 supervised) である。したがって
「checker に依存する受理結果」や「C2 の一般化」へこの fixture を根拠として使ってはならない。
なお実運用の wave branch (`worktree-dev-wave-*`) も非 supervised なので、
supervised 検査に関する限り fixture と同じ family にある。

**本文書は敵対レンズ 2 本 (`consult-sol.md` / `consult-luna.md`) の指摘を反映して改訂してある。**
撤回・縮小した主張には、その旨をその場に書いた。

---

## 0. 制御群 — fixture 上で land が正常完了する (`probe_smoke.py`)

```
rc = 0 / status = landed
main log: <fold> "Fold landed documentation fragments" ← "add fragment" ← "canonical ledgers"
pending fragments: ['README.md']            # GC 済み
worklog: "## 2026-08-11 (2) — fold probe" が追記されている
FOLDED.md: {"allocations":{},"authored":"2026-08-02","content_sha256":"5f2c…","seq":1,"wave":"wave-a"}
```

fixture は ff-only → `apply_fold` → `check_docs` → staging → commit → postcondition →
`verify_declared_fold_commit` の全経路を実際に通る。

---

## 1. [T-798] — 窓の再現 (`probe_t798.py`)

### 注入点

crash は本番 land が `_validate_generated_docs` から subprocess 起動する `tools/check_docs.py`
(fixture 側) が `os.kill(os.getppid(), SIGKILL)` することで起こす。
この時点は `tools/dev_wave_land.py:1872` の `fold.apply_fold(...)` が**返った直後**、
`:1873` の `_validate_generated_docs` の内側であり、[T-798] が主張する窓の内側である。
land 本体には monkeypatch を一切当てていない。

**「窓の入口」ではない (レンズ A の所見 1、妥当)。** 論理上の入口は
`tools/spool_fold.py:2357` の `state_path.unlink()`、電源断に対する耐久境界ならその直後の
directory fsync である。注入点はそれより後で、fsync・関数 return・checker path 検査・
subprocess 環境構築を挟む。**また窓は commit で終わらない** — commit 成功後から postcondition
検査の途中で死ぬと、残るのは「fold commit あり・state 無し・land 成否未報告」で、
本節が測った残骸とは**別の相**である。本 wave はこの post-commit 相を測っていない。

### 測定値

```
child returncode      = -9   (SIGKILL)
check_docs 到達        = True
--- crash 後の main ---
main HEAD             = a8cd1de   (== wave tip。ff-only は完了している)
fold commit           = 無し (HEAD は "add fragment" のまま)
transaction state     = False        ← journal は消えている
load_active_plan      = None         ← 復旧材料が無い
worklog に fold 反映   = True         ← canonical は書かれている
FOLDED.md に receipt   = True         ← receipt も書かれている
fragment GC 済み       = ['README.md'] ← fragment は消えている
git status            = " M docs/spool/FOLDED.md
                         D docs/spool/worklog/2026-08-02-wave-a-1.md
                         M docs/worklog.md"
```

**[T-798] の主張はそのまま再現した。** canonical・`FOLDED.md`・fragment GC は反映済みで、
commit も journal も無い。

**訂正 (レンズ A の所見 2、妥当):** 本 probe の fragment は worklog ledger 1 本なので、
実測した変更は **3 path** (`docs/worklog.md`、`docs/spool/FOLDED.md`、fragment の削除) である。
「canonical 3 台帳が反映済み」は**この測定の値ではない** — decisions / failures / phase3 を含む
plan でも同じ形になることは、別 probe (`probe_resume_hard_plan.py`、crash なし) で
6 target まで確認しているが、crash 残骸としては測っていない。

### 復旧経路の実挙動 (ここが本題)

| 経路 | rc | 出力 | 評価 |
|---|---|---|---|
| 1. `python3 tools/spool_fold.py` (引数なし = 正規の resume CLI) | **0** | `{"status":"noop","transaction_id":"","written_paths":[],…}` | **黙って成功を返す。** 復旧しないし警告も出さない |
| 2. land を同じ request で再投入 | 20 | `rejected` / `main tracked/index/submodule dirt is forbidden` | fail-closed。ただし理由語は fold を一言も指さない |
| 3. `git checkout -- docs` してから land 再投入 | (再び窓へ) | — | 復旧はできるが、**fold の適用結果を捨てて作り直す**手順 |

要点は経路 1 である。`validate_spool_tree` は state がある間だけ
`transaction-active — 引数なし CLI で resume が必要` を出すが、state が消えた後は
**この CLI が「やることは無い (noop)」と rc=0 で答える。**
つまり crash 後に運用者が最初に叩く道具が、窓に落ちたことを教えない。

経路 2 の理由語 `main tracked/index/submodule dirt is forbidden` から運用者が取る自然な次手は
`git checkout -- docs` (経路 3) であり、これは**適用済みの fold を破棄する**。
破棄しても fragment は tip の commit から復元されるため復旧可能だが、
「捨てた」ことは台帳のどこにも残らない。

逆に運用者が「もう反映されているのだから commit すればよい」と手で commit すると、
`verify_declared_fold_commit`・fold author identity・`AI-Agent:` trailer・`_FOLD_MESSAGE` の
どれも通らない commit が main に載る。これが [T-798] の言う
「proof chain を main history へ帰属できない」の具体形である。

### 窓の幅 (実 repo で実測、`probe_window_width.py`)

窓の中身は `_validate_generated_docs` → `_pending_spool_paths` → `git add` →
`git diff --cached` → mkstemp+fsync → `_preflight_fold_message` → `git commit` である。
実 repo での中央値 (2 つの HEAD で独立に測った。**worklog の rotation を挟んでも変わらない**):

```
HEAD 9abd23da (rotation 前、worklog 大)     HEAD 974207ae (rotation 後、worklog 小)
tools/check_docs.py            2.694 s      2.702 s   ← 窓の主項
check_ai_provenance --msg      0.089 s      0.090 s
git status -- docs             0.027 s      0.027 s
git diff --cached -z           0.012 s      0.011 s
-----------------------------------------------------------------------
commit 自体を除く合計            ≈ 2.82 s      ≈ 2.83 s
```

### この数値の射程 (レンズ A の所見 3 を受けて大幅に縮小した)

**「窓は約 2.8 秒」「96%」「land 1 回あたり」は撤回する。** 正しくは次のとおりである。

- これは**窓の実測ではなく、pre-commit 部分の代替小計**である。除外・代替されているものは
  state unlink 後の fsync と return、`_pending_spool_paths`、**staged fold を持つ index 上の
  実 `git add` (clean tree への `git status -- docs` で代替した)**、message tempfile の
  作成・fsync、**`git commit` 全体**、commit 後の HEAD / parent / ref / wave / clean / pending /
  declared-fold 検査である。
- したがって定義された窓に対しては**強く過小**である。`git status` が実 `git add` より速いとは
  限らないので、**厳密な下限ですらない**。3 つの独立した中央値の和は end-to-end の中央値ではない。
- 「96%」は不完全な小計に対する比 (2.702 / 2.831) である。commit と postcondition を足せば
  分母が変わる。
- **「land 1 回あたり」も誤りである。** fragment が 0 件なら plan は `noop` で、
  `apply_fold`・checker・fold commit のいずれにも入らない (`tools/spool_fold.py:1951`)。
  `already-landed` + `noop` も同様である。**露出の分母は land 回数ではなく non-noop fold の回数である。**
- 監査上の注意: probe runner が log を毎回上書きするため、`9abd23da` の標本列は log file には
  残っていない。値は本文書と `output/insights/.../verbatim/probe-logs.md` に逐語で凍結してある。

**end-to-end の窓幅は本 wave では測っていない。** 裁定に幅の正確な値が要るなら、実 main 相当の
post-fold tree で実 `git add`・実 commit・全 postcondition を含めて測り直す必要がある。
言えるのは「**pre-commit 部分だけで秒オーダーであり、その大半が `check_docs.py` である**」までである。

### 発火条件も広い (レンズ A の所見 8、妥当)

当初「例外ではなく process 死に限る」と書いたが、**狭すぎた**。`apply_fold` は返る前に state を
消しているので、その後の**通常例外 + rollback 失敗**の二重故障でも同じ残骸になる。
例えば `check_docs` が赤で `_rollback_fold` の ref CAS が失敗すると、
HEAD = wave tip・canonical after・GC 済み・state 無しのまま `fold-rollback-failed` を返す。
本 wave はこの二重故障経路を測っていない (既存テストは `_rollback_fold` 側の各失敗を
固定しているが、[T-798] の残骸としての観測はしていない)。

---

## 2. [T-799] — 窓の再現 (`probe_t799.py`, `probe_t799c.py`, `probe_t799_after.py`)

state は本番 `apply_fold` に書かせている (plan 構築後に fragment 本体を 1 行増やすと
GC 照合で `TransactionError` になり、state だけがディスクに残る)。その後 fragment を戻して
tree を清浄にしてから測っている。

**訂正 (レンズ A の所見 4、妥当): これは [T-766] が増やす残存 state と「同じ形」ではない。**
本 probe の state は **canonical 変更前 (pre-mutation)** で、`_rollback_fold` を一度も通っていない。
[T-766] が増やすのは rollback の ref CAS 失敗・read-tree 失敗・path 復元例外で残るもので、
それぞれ「HEAD と worktree が戻っていない」「index/worktree が残る」「第三状態の path が残る」と
形が違う。**それらの形からの resume は本 wave では測っていない。**
以下の B1 / B3 の結論は「pre-mutation の清浄な残存 state」に対するものである
(schema に HEAD / 起源が無いこと自体はどの形でも共通である)。

### A. state は worktree ごとに独立している

```
main worktree state = <repo>/.git/izanagi-spool-fold-state.json
wave worktree state = <repo>/.git/worktrees/one/izanagi-spool-fold-state.json
同一 path か         = False
```

`_state_path` は `git rev-parse --git-path` で解決するため per-worktree である。
つまり land が main に残した state は、main checkout から `tools/spool_fold.py` を叩いたときだけ見える。

### B. state が束縛する field

```
['fold_date', 'fragments', 'gc_paths', 'projected_worklog_bytes',
 'rotation_path', 'targets', 'transaction_id', 'version']
HEAD / land 起源 / base / tested tip / rollback ref の記述 = 無し
```

`transaction_id` も `_plan_transaction_id` (`tools/spool_fold.py:1919`) が
`fold_date` + fragment (path, content_sha) + target (path, before_sha, after_sha) だけから作る。
**どの HEAD で計画したかは transaction_id にも入らない。**

### B1. canonical を 1 byte も変えない commit で HEAD を進めてから resume → **成功する**

```
planned 時の HEAD = 9fe8369
その後 base.txt だけを変える commit → HEAD = bb98be2
planned..HEAD の変更 path = base.txt   (docs は 1 byte も変わらない)

standalone rc     = 0
standalone output = {"status":"resumed",
                     "written_paths":["docs/spool/FOLDED.md","docs/worklog.md"],
                     "gc_paths":["docs/spool/worklog/2026-08-02-wave-a-1.md"], …}
fold commit       = 無し (HEAD は "code-only commit" のまま)
git status        = " M docs/spool/FOLDED.md / D <fragment> / M docs/worklog.md"
```

**[T-799] の主張はそのまま再現した。** 唯一効いている歯止めは
`apply_fold` の before/after hash 照合であり、これは「canonical 6 file の bytes が同じか」しか見ない。
コードやテストだけを変える commit は canonical を変えないので、この歯止めを素通りする。

**ただし、この B1 単独では「誤った結果」は示していない (レンズ A の所見 5、妥当)。**
挟んだ変更が `base.txt` だけなので、元 HEAD で再計画しても同じ台帳 bytes になる。
残る dirty tree は HEAD を動かさなくても standalone resume が必ず作るものである。
また、この HEAD の動き自体は**協調 land 同士では作れない** (共通 lock で直列化され、
active state があって `main != tested_tip` なら停止する) — main への非協調な直接 commit が要る。
**B1 が示すのは「歯止めが無いこと」であって「値が壊れること」ではない。**
値が壊れることは次の §D で別に測った。

### B2. 対照 — canonical を変える commit を挟むと拒否される

```
standalone rc     = 2
standalone output = {"error":"docs/worklog.md: before/after 以外の第三状態","status":"transaction-error"}
```

検出力は「canonical bytes が変わったか」に等しい。HEAD 同一性ではない。

### B3. resume は `_git_clean_preflight` を通らない

`apply_fold` は state が**無い**ときだけ `_git_clean_preflight` を呼ぶ (`tools/spool_fold.py:2290-2291`)。
同じ dirty 条件 (`git rm --cached docs/worklog.md` = index 上は削除、worktree の bytes は不変) で:

```
state 無しの apply = 拒否: "actual fold 対象に未追跡または dirty path がある"
resume の apply    = rc=0 / status=resumed   ← 同じ条件を通す
```

**resume 経路は新規 apply より弱い。**

### B4. standalone resume は必ず [T-798] の残骸に着地する (`probe_t799_after.py`)

standalone CLI は commit を作らない。したがって resume が成功した直後の tree は

```
git status = " M docs/spool/FOLDED.md / D <fragment> / M docs/worklog.md"
commit     = 変わらず
その後の land rc = 20  "main tracked/index/submodule dirt is forbidden"
```

で、**[T-798] の crash 残骸と 1 文字も違わない。**
正規の復旧手段を正しく使っても、成功したその瞬間に [T-798] の窓の中に立っている。

**「必ず」の射程 (レンズ A / B の所見 7、妥当):** これが成り立つのは
**現行コードが commit 前に残した non-noop state** に限る。選択肢 (b) を採ると
「commit 済み・state 残存」という新しい正規状態が生まれ、そこからの standalone resume は
全 target を skip して state だけ消し、**健全に終わる**。つまり (b) 採用後は反例が存在する。

### D. 採番の入力は束縛されていない — resume が重複 T 番号を作る (`probe_plan_input_closure.py`)

**本節はレンズ A の所見 5 を受けた追加測定であり、[T-799] の性質を「帰属の問題」から
「値の問題」へ変える。**

`_max_task_number` は `docs/worklog.md` の rotation 以降・`docs/phase3.md` の見送り台帳・
**`docs/archive/worklog-*.md` の全部**から最大 T を採る (`tools/spool_fold.py:1316-1323`)。
一方 state が hash で束縛するのは「出力が変わる target」だけである。
**archive worklog は plan の入力でありながら target ではないので、state に一切現れない。**

```
planned allocations = [('wave-a/T:probe-new', '[T-052]')]
plan targets        = ['docs/spool/FOLDED.md', 'docs/worklog.md']
archive は target か  = False

→ archive worklog へ "- [T-052] 別 wave が先に取った" を足して commit
  (canonical target は 1 byte も変えていない)
archive 変更後の _max_task_number = 52 → 再計画なら [T-053]

== 残存 state から standalone resume する
rc     = 0   status=resumed   written=[FOLDED.md, worklog.md]

worklog へ入った番号   = ['[T-052]']
archive にある同じ番号 = True
同じ T 番号が 2 箇所に存在するか = True
```

**resume は古い採番 `[T-052]` を適用し、archive に既にある同じ番号と衝突した。**
再計画していれば `[T-053]` だった。同型の未束縛入力は少なくとも次がある。

- `docs/archive/worklog-*.md` (採番と carry 解決の入力。上で実測)
- `docs/phase3.md` の見送り台帳 (target になるのは見送り操作を含む plan のときだけ)
- `tools/check_docs.py` の `WORKLOG_ROTATE_BYTES` (`_load_rotate_limit` 経由の plan 入力。
  **コードだけを変える commit で rotation の結果が変わる**)

**下流で捕まるか (静的確認、未実測):** `tools/check_docs.py` の T 重複検査は
`### 次の一手` の**1 エントリ内**で `seen` 集合を作る形 (`tools/check_docs.py:1144-1172`) で、
archive を跨いだ大域一意性は検査していない。見送り台帳の重複検査 (同 `:1552`) も別枠である。
したがって land 経路の `_validate_generated_docs` もこの重複を止めないと読めるが、
**実 checker での実測はしていない** (fixture の checker は stub である)。

**射程:** 本測定は standalone resume で行った。land 経路で同じことが起きるには、
残存 state を持つ main が `locked_main == tested_tip` を満たす必要があり、
そこは C2 と同じ条件である。

### C. land 経路の検出力 (`probe_t799c.py`)

| 状況 | rc | 結果 |
|---|---|---|
| C1: main が別 wave の tip、残存 state あり、別 wave の tip を宣言して land | **27** | `fold-recovery-failed` / `active fold transaction requires main at the tested wave tip` |
| C2: main が宣言 tip と一致、別 HEAD で計画された残存 state あり | **0** | `landed`。**別 HEAD で作られた plan をそのまま resume し、fold commit を作った** |

**採用した測定と、採用しなかった初回測定 (erratum)。** 権威は `probe_t799c.log` である。
先行する `probe_t799.log` の C 節は同じ構成で **rc=20 (`main tracked/index/submodule dirt is forbidden`)**
を返しており、値が食い違う。原因は本番の挙動ではなく **fixture の誤り**で、
2 本目の wave worktree を作った**後**に main で `git add -A` したため
`.codex/worktrees/two` が tracked に入り、main が dirty になっていた
(`probe_t799c.log` の切り分けで `M .codex/worktrees/two` を実測した)。
worktree 作成を commit の後ろへ移して再走したのが `probe_t799c.log` である。
**初回 log は消さずに残している。**

C2 が [T-799] の land 側の実体である。plan は `b5718b1` (main_head) で計算され、
land は `81e99a0` (wave B tip) の上で resume して `bb25ccd` を fold commit として作った。
**land が持っている唯一の歯止めは `locked_main == tested_tip` という付随的な不変条件**であり、
`tested_tip` は呼び出し側 argv の申告値である。state 自身は何も束縛していない。
`_verify_supervised_fragment_wave` は `refs/heads/dev-wave/dw-` namespace 以外では
先頭で `return` する no-op なので (`tools/dev_wave_land.py:1599-1600`)、
`worktree-dev-wave-*` の通常 wave には wave 同一性の束縛が一切かからない。

**C2 の解釈は縮小する (レンズ A の所見 6、妥当)。** 測った C2 は**欠陥の実演ではない**。
fragment は main に pending だったもので、wave B はその main commit を祖先に無関係な file を
1 つ足しただけである。採番の入力は変わらず、receipt は正しい `wave-a` を保持し、
fold commit の parent は実際の wave B tip を記録し、`verify_declared_fold_commit` も通る。
**同じ pending fragment を現在の main 上で fold する正常動作**と読むのが妥当である。
「計算時 HEAD を記録せよ」という契約は `docs/spool/README.md` にも無い。

したがって C2 が示すのは**「resume が計画時の文脈に束縛されていない」という事実**までであり、
それが実害になるのは**採番の入力が変わったとき**である。その実害は §D で別に測った。

---

## 3. 選択肢の前提として実測したこと

### (T-798 の (b)) 「state 削除を postcondition 後へ移す」の前提 (`probe_option_costs.py`)

```
state 無し: validate_spool_tree → issues = []
state 有り: validate_spool_tree → [('transaction-active',
             'fold transaction が active — 引数なし CLI で resume が必要')]
```

`tools/check_docs.py:830` がこの `validate_spool_tree(REPO)` を呼ぶ。
`_validate_generated_docs` は窓の**先頭**で `check_docs.py` を走らせる。
したがって (b) を素で入れると、**窓の間ずっと state が生きているので check_docs が必ず赤になり、
fold が毎回 rollback する**。(b) は「`validate_spool_tree` を active-aware にする」を
同時にやらない限り成立しない — 選択肢の文言どおりであり、それが必須である裏が取れた。

### (T-798 の (b)) 「窓の形からの resume」は難しい plan でも冪等か (`probe_resume_hard_plan.py`)

(b) の窓では「全 target が after・gc 削除済み・state 残存」という形が続く。この形から
`apply_fold` を呼び直しても壊れないことを、単純な追記だけでなく
**既存 bytes の間へ挿入する操作**と**ローテーション**を含む plan で確かめた。

```
A. ローテーション無し + failures 再発 + supersede 追記 + 見送り追記
   targets = [failures.md, phase3.md, spool/FOLDED.md, worklog.md]
   1 回目 = applied (written 4) / 2 回目 = resumed (written 0, resumed 4)
   全 target が byte 単位で不変 = True
   再発 payload = 1 / supersede 行 = 1 / 見送り追記 = 1   ← 二重挿入なし

B. ローテーション発火 + 同じ挿入・追記
   targets = [archive/README.md, archive/worklog-phase3-0801-1.md,
              failures.md, phase3.md, spool/FOLDED.md, worklog.md]
   1 回目 = applied (written 6) / 2 回目 = resumed (written 0, resumed 6)
   全 target が byte 単位で不変 = True
   再発 payload = 1 / supersede 行 = 1 / 見送り追記 = 1
   worklog エントリ見出し = 1 / archive の見出し = 1        ← 二重移動なし
```

機序は「変換の再実行」ではなく **content-addressed な収束**である。`apply_fold` は各 target の
現在の sha256 を `after_sha256` と比べ、一致していれば書かずに `resumed` へ積む
(`tools/spool_fold.py:2305-2307, 2333-2336`)。plan が何を挿入するかに依存しない。

**erratum:** 先に書いた `probe_post_apply_resume.py` の「canonical は不変」行は、
同じ `git status` を左右で 2 回呼んで比べる**恒真な検査**だった (レンズ B の所見 3-B、real)。
適用後の bytes を捕まえて比較する形へ直して再走し、同じ結論を得ている。
上表の A / B (`probe_resume_hard_plan.py`) は最初から捕捉した bytes で比較しており、
この誤りを含まない。

### (T-798 の (b)) 残余の窓 — 「commit 済み・state 残存」は既存 recovery で閉じない (`probe_option_b_wedge.py`)

**この節は敵対レンズ B の所見 1-B を受けて追加測定したものである。親の当初の
「(b) は新しい recovery 機構を要らない」は、この測定で縮小した。**

(b) は state の削除を postcondition の後ろへ動かすので、窓は消えず**移動する**。
新しい残余窓は「fold commit 済み・state 未削除」である。本番は変えられないので、
land を正常完了させた後に同じ state を置き直して、その形を後から作って測った。

```
1 回目の land        = rc=0 landed / fold commit c7bf2c8 (親 3a08cd5 == tested tip)
(b) が残す形を作る    → state 残存 True / load_active_plan True
                       main HEAD (c7bf2c8) == tested_tip (3a08cd5) は False
この形から land 再投入 = rc=10 stale-main
                       "main moved outside the tested audited closure while locking"
standalone CLI       = rc=0 status=resumed / written 0 / resumed 2 / state 削除 / tree 清浄
```

読み方は次のとおり。

- **land はこの形を閉じられない。** `_main_is_allowed` の判定が `_locked_preflight` の中にあり、
  `active_plan` を見る分岐 (`tools/dev_wave_land.py:2203`) より**前**で返るためである。
  次 wave が新しい `tested_main` で来た場合は代わりに
  `active fold transaction requires main at the tested wave tip` (rc=27) になるが、
  **どちらにせよ land は finalize しない。**
- **閉じられるのは standalone CLI だけである** — しかもそれは Q2 (b) が封鎖したい経路である。
- ただし残余窓の**幅は桁違いに小さい**。現状の窓が `check_docs` を含む約 2.83 秒であるのに対し、
  (b) の残余窓は `commit` 直後の `unlink` + `fsync` だけである。
  また残るのは**journal そのもの**なので、現状の「痕跡が git dirt しかない」状態と違って
  何が起きたかを機械的に言える。
- したがって (b) を採るなら、**land の active-plan 分岐へ「main が tested_tip の子である fold commit で、
  plan が全 target after」を受理して state を finalize する経路**が要る。
  必要な比較は land が既に `_rollback_fold` (`tools/dev_wave_land.py:1757-1765`) で書いている
  「現在の HEAD の親が expected_tip か」と同型である。

### 変更面の大きさ (静的に数え直した)

**親の初回の数え方は誤りだった。** `state_path.exists()` だけを grep したため、
`spool_fold._state_path(repo).exists()` 形を落とし、逆に dry-run のテストを
「apply 後の pin」と誤って数えていた。レンズ B の指摘 (9 行) も過大で、
rollback と dry-run の pin を含んでいる。全部開いて分類した結果は次のとおり。

- `apply_fold` の本番呼出し口は **2 箇所だけ** — `tools/spool_fold.py:2515` (standalone CLI) と
  `tools/dev_wave_land.py:1872` (land)。挙動を分けるならこの 2 箇所で足りる。
- state 不在を assert している行は全部で 8 行だが、内訳は
  - **apply 成功後の削除を pin しているのは 1 本だけ** —
    `test_spool_fold.py:1779` (`test_interrupted_transaction_resumes_before_and_after_targets`)
  - dry-run / エラー経路が state を作らないことの pin が 5 本
    (`test_spool_fold.py:2583, 2687, 2730, 2834, 2898`) — (b) は触らない
  - rollback 成功後の削除の pin が 2 本 (`test_dev_wave_land.py:2763, 2765`) — (b) は触らない
- **land 側だけ挙動を分ける実装 (land が `retain_state` を渡す) なら、壊れる pin は 0 本になる。**
- state を触る参照数 (参考): `tools/spool_fold.py` 19 / `tools/dev_wave_land.py` 18 /
  `test_spool_fold.py` 12 / `test_dev_wave_land.py` 56。
- state schema は `version: 1` 固定で、`_load_state` が `value.get("version") != 1` を拒否する。
  `_state_plan` は必須 key を `KeyError` で `TransactionError` にする。
  **field を足すなら「省略可能として読む」か「version 2 + 旧 state の移行」が要る。**
  移行を怠ると、旧 code が書いた in-flight state を新 code が読めず、
  **まさに復旧が必要な瞬間に復旧できない。**

### 排他制御の欠落 (レンズ A の所見 8、静的確認)

land 同士は `_open_lock` の flock で直列化されるが、**standalone CLI は state の読込みから
apply まで land lock を一切取らない** (`tools/spool_fold.py:2497-2517`)。したがって
land と standalone、standalone と standalone が同じ state を同時に読める。
`docs/spool/README.md` の「fold は land lock の中だけ」と、`validate_spool_tree` の
「引数なし CLI で resume が必要」という誘導の**間にある実際の開口部**である。
**本 wave では競合を実測していない** (barrier 付きの同時実行 probe は書いていない)。

### 未測定と明記すること

裁定の前に測るべきだがこの wave では測っていないものを、レンズ 2 本の指摘を含めて列挙する。

1. commit 成功後・postcondition 中の crash (post-commit 相の残骸と復旧)
2. [T-766] の rollback 失敗で残る各形 (ref CAS / read-tree / path 復元) からの resume
3. `WORKLOG_ROTATE_BYTES` や phase3 を変えた場合の rotation 差 (§D の同型、archive だけ実測)
4. land / standalone の同時実行競合
5. commit と postcondition を含む end-to-end の窓幅
6. 実 checker (stub でない `check_docs.py`) が §D の重複 T を止めるか
7. supervised branch (`refs/heads/dev-wave/dw-*`) での C2 相当の受理差

### 付随所見 (本 wave の scope 外、起票候補)

`_load_rotate_limit` (`tools/spool_fold.py:1806-1832`) は `tools/check_docs.py` を
**land process 内で `exec_module`** する。`except Exception` で囲っているが `SystemExit` は
`BaseException` なので抜ける。probe の初回、fixture の `check_docs.py` が module 直下で
`raise SystemExit(0)` していたため、**land process が出力ゼロ・rc=0 で静かに消えた**。
実物の `tools/check_docs.py` は `if __name__ == "__main__":` で囲っているので現状は発火しないが、
「fail-closed に囲ったつもりの `except Exception` が `SystemExit`/`KeyboardInterrupt` を
取り逃がし、しかも rc=0 = 成功に見える」形はここに実在する。
