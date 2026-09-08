## 1. 既知違反登録は正しさゲートの弱体化か

### 所見 1A — refuted

- file:line: `tools/check_ai_provenance.py:1976-2028`、`docs/decisions.md:10422-10449`、`main:tools/known_violations/c12e25078...json:2-6`
- 判定: 受理集合は広がるが、対象は full SHA `c12e25078ad155486c19eae633fde14e59753272`、種別 `missing-codex-author`、entry 1件につき finding 1件に限定される。entry は当該 commit の同種 finding を1件消費すると再利用されず、別 commit、別種、同種2件目、将来 commit は通さない。これは D221 の意図した限定そのもの。
- `value=""` は当該 SHA の同種 finding 本文を限定しないが、`missing-codex-author` では D221 が定めた「SHA + 種別 + 1件」と一致する。
- 影響: 放置しても他 commit や将来の同型違反が吸収される経路はない。
- 推奨: **取り込んでよい**。

### 所見 1B — refuted

- file:line: `main:tools/known_violations/c12e25078...json:6`
- 判定: `git diff-tree --no-commit-id -r --raw c12e25078` は110行すべて `:000000 160000 A` で、全 path が `.codex/worktrees/` 配下だった。mutation ledger や通常 file は含まれない。entry 本文の SHA-256 も filename の `e71feba7...89904b` と一致した。
- 影響: `note` が対象外成果物を隠して台帳登録を正当化している事実誤認はない。
- 推奨: **取り込んでよい**。

### 所見 1C — real

- file:line: `docs/decisions.md:10424-10425,10448-10458`、`tools/check_ai_provenance.py:733-747`、`main:tools/known_violations/c12e25078...json:5`
- 判定: 機械 schema は「非空 ruling」しか要求しないため通るが、「ユーザー承認は事後報告」は D221 の原文が求めるユーザー裁定への明確な出典ではない。後発 D662 は事前承認を不要とし、登録後に裁定へ送る経路を認めているため、未批准だったこと自体は違反ではない。さらに `main:docs/spool/worklog/2026-09-08-dev-wave-research-gate-1.md:35-36` にはユーザーの是正指示が記録されている。ただし entry 自身の参照は曖昧。
- 影響: 放置すると、将来の監査者がどのユーザー裁定で批准された entry かを entry 単体から特定できない。
- 推奨: **裁定パッケージ候補**。entry は append-only なので変更せず、今回の報告に対するユーザー裁定を worklog へ明記する。

## 2. 是正 commit 自身の provenance

### 所見 2A — refuted

- file:line: `docs/ai-provenance.md:44-55`、`tools/check_ai_provenance.py:1536-1582`
- 判定:
  - `48837186c`: Claude manager と `product=codex; ...; role=author` を持つ。
  - `cf837838a`: test-only だが同じ Codex author trailer を持つ。
  - `c9c97525e`: `role=author; scope=untrack-codex-worktrees` を持つ。
  - 3件とも trailer は最終 block で Git parser に認識された。
  - `c9c97525e` は現 main の祖先ではない。main が採用した除去は `48837186c`。
- 影響: Codex author 欠落により新たな `missing-codex-author` が生じ、DW-O25 が rc=29 になる問題はない。
- 推奨: **取り込んでよい**。

pytest と全史 provenance の実走はしていない。ここでの結論は指定どおり静的検査である。

## 3. gitlink 除去の完全性と安全性

### 所見 3A — refuted

- file:line: `.gitmodules:1-3`、`main:tools/known_violations/c12e25078...json:6`
- 判定: `git ls-tree -r main` の mode 160000 は `external/ccbench` 1件だけで、これは `.gitmodules` に正規登録されている。`.codex/worktrees/` は0件。
- 影響: 未登録 gitlink が残って submodule 列挙を rc=128 に戻す経路は現 main にない。
- 推奨: **取り込んでよい**。

### 所見 3B — refuted

- file:line: `/usr/share/man/man1/git-rm.1.gz:195-226`、`main:tools/known_violations/c12e25078...json:6`
- 判定: `48837186c` の `git rm --cached` は index だけを変更する。主 checkout の実 directory は現在も populated で、`git status` では `?? .codex/worktrees/` として残っている。別 worktreeで superproject 更新が gitlink を削除しても、非空 checkout を再帰削除せず stale directory として残す。今回の wave worktree 内の110 directory はすべて空であり、消えるとしても空 placeholder だけ。
- 影響: 稼働中 Codex 子 worktree の内容が merge によって消失する危険は認められない。非空残存物は untracked になり、後段 clean gate が拒否する。
- 推奨: **取り込んでよい**。

## 4. 受入 preflight が本当に通るようになるか

### 所見 4A — real

- file:line: `tools/dev_wave_wait.py:360-369,2224-2255,2568-2583`
- 判定: gitlink 除去済みの主 checkout で、実コードと同じ
  - `git submodule foreach --recursive --quiet 'git ls-files -v -z'`
  - `git submodule status --recursive`

  はともに rc=0だった。対象は正規 submodule `external/ccbench` だけになるため、除去後の木では当初の rc=128 原因が消える。
- 影響: 除去を取り込めば `preflight-index-flags`、`preflight-submodule-ready`、fingerprint の submodule 呼出しを止めた直接原因は解消する。
- 推奨: **取り込んでよい**。

### 所見 4B — real

- file:line: `tools/dev_wave_wait.py:3752-3785,3817-3837`
- 判定: 現 wave の HEAD はまだ c12e25078 を含むため、受入は自動 merge より前の `preflight-index-flags` で現在も rc=128になる。仮にそこを越えても、既知違反 entry をまだ持たない状態で `preclaim-history-provenance` が先に走る。したがって「受入に任せれば是正を自動 mergeする」は成立しない。
- 影響: 放置すると受入は main の修復 commit へ到達せず、同じ preflight で停止し続ける。
- 推奨: **取り込む前に直す**。親が先に main を手動 mergeする必要がある。

### 所見 4C — refuted

- file:line: `tools/dev_wave_wait.py:3889-3907,3968-3989`
- 判定: `prerun-clean` と `postrun-clean` は `--untracked-files=all --ignore-submodules=none` を使う。非空 `.codex/worktrees/` が残れば黙って fingerprint に混入せず、その場で拒否される。現在の wave 側110 directory は空なので、空 directoryが残っても Git status と fingerprintには現れない。
- 影響: `.codex/worktrees/` 由来の非空残存物が検査をすり抜ける追加経路はない。
- 推奨: **取り込んでよい**。ただし merge後に porcelain が空であることは通常どおり確認する。

## 5. 本 wave の記録の重複

### 所見 5A — real

- file:line: `docs/spool/failures/2026-09-08-dev-wave-t2423-floor-protocol-identity-1.md:11-24`、`main:docs/spool/failures/2026-09-08-dev-wave-research-gate-3.md:11-28`
- 判定: 同じ c12e25078 の110 gitlinkを別の新規 F として二重登録している。さらに本 wave の見出しは「111件」と誤記している。worklog の新規 T も `48837186c` と `cf837838a` により既に完了した作業を再起票している。
- 影響: 放置すると同じ事故へ F と T が二重採番され、未了作業が存在するように台帳が偽る。
- 推奨: **取り込む前に直す**。

選択肢の評価:

- (a) failures fragment を削除して散文だけにする: 意味上は重複を避けられるが、今回は fragment が既に commit 済み。`docs/spool/README.md:95-98` と `tools/dev_waves/git_state.py:973-985` により削除 commit は `landed-fold-owned-path` で拒否される。**現状では通らない**。
- (b) 別 wave の F へ `再発` 追記: 正しい最終形。`preflight-index-flags rc=70 source_rc=128` を再発 payload に書けば、peer の `prerun-fingerprint` 観測と本 wave の観測を両方保存できる。ただし peer F は未 fold で literal ID がなく、他 wave の placeholder は参照禁止である。**peer fragment の fold 後なら通る。現時点では通らない**。根拠は `docs/spool/README.md:63-67`、`docs/spool/failures/README.md:43-45,58`。
- (c) `supersede 追記`: 後続事実で既存記述が古くなった場合の形式であり、今回の別段での観測には不適切。literal F もまだない。**通らない**。解消済みであることを後日補記する用途なら別途成立するが、本 wave の観測保存を代替しない。
- (d) そのまま両方登録: parser が異なる slug の新規 F として機械的に畳む可能性はあるが、同型再発を新規番号にしてはならない規則に反する。**規則上通してはならない**。

取るべき形は、peer fragment が先に fold され literal F が確定した後、現在の failures fragmentを削除せず **(b) の再発 fragmentへ書き換える**こと。worklog は自 wave の F placeholder と `{{T:remove-codex-worktree-gitlinks}}` を除き、literal F、独自の preflight 観測、`48837186c` / `cf837838a` で解消済みという散文にする。

## 6. 取り込みの順序と手順

### 所見 6A — real

- file:line: `tools/dev_wave_wait.py:3752-3785,3817-3837`、`docs/dev-wave/operations.md:121-129,150-161`
- 判定: 自動 merge は early preflight より後なので、この bootstrap 状態では利用不能。親が最新 main を `--no-ff --no-commit` で先に取り込み、DW-O17 の message preflight と commit後全史監査を行う必要がある。
- 影響: 受入任せでは修復 commitを取得できず、同じ rc=128 を再現する。
- 推奨: **取り込む前に直す**。親による手動 mergeを選ぶ。

### 所見 6B — refuted

- file:line: `tools/dev_wave_wait.py:2801-2825`、`tools/check_ai_provenance.py:1635-1707`、`docs/dev-wave/operations.md:123-129`
- 判定: `c12e25078..HEAD` の wave 変更21 pathと `c12e25078..main` の122 pathの交差は0。本 wave の実装3 pathもすべて交差0。競合なしの機械 mergeなら結果が両親と異なる pathはなく、merge messageの Codex `role=author` は不要。Claude `role=integrator` の `AI-Agent` trailerは必要。
- 影響: 不要な Codex authorを付けると機械統合を実装著作と誤記する。一方、実装面を競合解決で両親と異なる内容にすれば Codex authorが必要になる。
- 推奨: **取り込んでよい**。自動 messageや `--no-edit` は使わず、DW-O17 の明示 messageを使う。

順序は、peer F の foldを待つ、親が最新 main を手動 mergeする、failure/worklogを上記 (b) へ改訂する、その記録 commit後に受入へ進む、である。

## 総括

是正 commit群そのものは取り込んでよいが、現状のまま受入・landへ進んではならない。
最大の実行上の懸念は、自動 mergeより前の preflight が旧 gitlinkで停止する bootstrap 問題である。
記録は peer F の fold後に literal F への `再発` とし、独自の `preflight-index-flags` 観測を残し、重複 T は除く。
既知違反の scopeと trailerは適正だが、`ruling` の曖昧な出典は裁定パッケージ候補として残る。
pytest、全史 provenance、実 mergeは実行していない。