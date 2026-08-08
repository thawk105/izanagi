# 裁定パッケージ — [T-659] activation 発行から配備までの分裂窓

2026-08-09 / wave = `dev-wave-t659-activation-deploy-window` / 起点 main = `ee2da0bf`。
**実装差分ゼロの設計 wave。** 本番コードは 1 行も変えていない (ユーザー指示)。

読み方: §1 が前提事実 (実測)、§2 が設問 R0〜R4 (各問に推奨と見送り時の影響)、§3 が採用時の
不変条件、§4 が本 wave が扱わないもの。**根拠はすべて静的読解と leaf 検証の実測であり、
実機の並行実行・race・PBS wrapper 全分類は測っていない。**

---

## 1. 前提事実 (本 wave の実測)

### 1.1 いま何が起きるか

activation record の発行 tool (`tools/issue_env_contract_activation.py`) は record を live
directory へ create-only で公開するが、`orchestrator/campaign/env_contract.py` の head 定数
(`_ACTIVATION_HEAD_SERIAL` / `_ACTIVATION_HEAD_STATE_SHA256`) を更新しない。

親が temp copy 上で実測した (live は不変):

- **発行後・head 未更新**: 新しく読み込む process は `activation head serial 不一致:
  expected=1 observed=2` で拒否する。
- **head 更新後**: 受理する。
- **逆向き (定数だけ先に進め record 未配備)**: 同じく拒否する。

**どちらの向きの分裂も安全側に倒れる。fail-open の経路は見つからなかった。**
ただしこの実測は leaf の検証関数 (`load_activation_state`) に期待値を直接渡したものであり、
production の読み込み経路 (cache、fork、root 解決、較正検証) を通した実測ではない。

### 1.2 窓は 2 つではなく 3 つ

段 2 プランと段 3 レンズが親の「窓は 2 つ」を訂正した。運用上は 3 段の壁がある。

1. **発行 worktree の中**: record 発行 → head 更新 → 同一 commit まで。
2. **配備**: その commit を main・各実行 checkout・source-stage へ行き渡らせるまで。
3. **旧世代の掃け残り**: 旧 process、fork 系列、投入済みの計算 job が終わり、`exec` で
   起動し直すまで。

親の 2 分法が成立するのは「対象 checkout が 1 つ」「投入済み job を既存 process に数える」
前提のときだけで、現状 (worktree 複数・計算ノードの job) ではその前提を書かない限り不足する。

### 1.3 新しい record は Git の追跡下に無い

`git ls-files` で確認したところ、追跡されている record は `00000001.json` の 1 件だけ。
発行 tool は次の serial の**新しいファイル名**を作るため、**発行直後の record は untracked** である。
帰結:

- `git commit -a` / `git add -u` は head の編集だけを拾い、新 record を落とす。
- 素の `git stash` は head 編集だけを退避し、record を残して分裂状態を作る。
- **逆に、発行後に中断したときは untracked の record を消すだけで元に戻せる** (回復が安い)。

### 1.4 混在した世代は事後に追いきれない

durable な成果物に載る環境識別子は execution receipt の `contract_sha256` だけである。
`activation_serial` は process の中だけの値で、成果物には残らない。さらに、activation は
**一部の env を据え置いたまま**進められる (D245) ため、据え置かれた env の成果物は新旧の
activation を区別できない。**並行 [T-657] がまさにその形** (linux-baremetal 据置、pegasus g1→g2)。

なお段 1 で親が「`evidence_contract_sha256` で識別できる」と書いたのは**誤り**だった。これは
段 8c の事前登録 evidence 文書の hash であり、環境世代の識別子ではない (段 2 が指摘、親が確認)。

---

## 2. 設問

各問は独立に裁定できるよう組み直した (段 3 レンズ B の指摘による)。依存がある箇所は明記した。

### R0 — 「全 process」の範囲をどう定義するか

活性化のとき「全 process を再起動した」と言える対象範囲。

- **(a) 推奨 — 列挙できる閉集合に限る。** certified / official な成果物を書く launcher を
  名指しで列挙し、その起動 root と投入済み job だけを対象にする。**「全 process」という
  言い方はやめる。**
- (b) repo に関わる全 process を文字どおり対象とする。

**推奨の理由**: (b) を保証する入力が存在しない。process の名簿も、全ノード共通の予約機構も、
generic dispatch の投入記録に source commit も無い。login ノードの `pgrep` は 1 ノードの
瞬間値で、投入待ちの job を含まない。無い入力に依存する検査は作らない (`DW-O13`)。

**見送り時の影響**: 数値も受理集合も変わらない。ただし「全 process 再起動」が検証不能な
言葉のまま runbook に残り、活性化のたびに解釈が揺れる。

### R1 — 発行と head 更新を結びつける機構を作るか

- **(a) 推奨 — 作らない。** runbook の手順 + 発行 tool の handoff 文の補強だけで済ませる
  (概算: runbook 30-50 行、tool 3-5 行)。
- (b) land の直前に「record と head が同じ commit に入っているか」を機械検査する
  (概算 300-500 行: checker + land 配線 + テスト)。
- (c) 発行 tool に head 定数まで書き換えさせる。**選択肢から落とすことを推奨** (下記)。

**推奨の理由**: (b) が防ぐのは「分裂した履歴が main に残ること」であって、「分裂した状態で
成果物が出ること」ではない。後者は runtime が既に両方向で拒否している (§1.1)。certified
選択・レポート・試行台帳のどの値も受理集合も変わらないため、研究最優先 (D205) に照らして
300-500 行は正当化できない。

**(c) を落とす理由 (段 3 レンズ A、確度 high)**: 発行 tool が head も書き換えると、
「発行」が commit 前の「有効化」になる。runtime は Git を見ずに作業ツリーの record と定数の
一致だけを見るため、**review 前・commit 前の作業ツリーから成果物を書けてしまう**。
承認された head という信頼の根が、発行者が選べる値に置き換わる。

**(b) を選ぶ場合の必須条件** (段 3 レンズ A、いずれも確度 high):
- 検査を呼ぶ側 (land ツール) も main に land 済みのものへ束縛する。候補 branch 側の
  ツールが検査呼び出しを外せる形にしない。
- 1 つの activation commit で追加できる record を **1 件ちょうど**に固定する。現在の
  読み込みは複数 record の連鎖を受理し、**連鎖の途中の世代まで「かつて有効」に入る**ため、
  一度も配備されていない世代が歴史的成果物の検証を通してしまう。
- 「検査導入 commit 以降に適用」は実在する値ではないので、別の実在値で定義し直す。

**見送り時の影響**: (a) では runtime の受理集合は変わらず、人手の手順漏れが残る。ただし
漏れた場合の帰結は fail-closed (fresh process が止まる) で、壊れた成果物は出ない。
(b) は land 可能な Git 履歴を狭めるだけで、成果物の値は変えない。

### R2 — 活性化時の旧 process / job をどう扱うか

- **(a) 推奨 — 活性化専用の作業窓を手順として置く** (機構は作らない)。`contract_sha256` に
  よる事後分類は補助の診断として使う。
- (b) 手順も置かず、事後分類だけに委ねる。

**(a) の手順に必ず含めるもの** (段 3 レンズ B の指摘を反映):
1. 新規投入・再開の凍結と解除の順序。
2. 投入済み job の照合先 (`qstat` と各 wrapper の投入記録)。
3. **どこで止めるか** — 照合できない job があれば活性化しない、という abort 条件。
4. **中断からの復帰** — 発行後に落ちた場合は untracked の record を消して元に戻す (§1.3)。
   これを書いておかないと、担当者が record 削除や head 手編集という未定義の操作へ流れる。
5. 覆えない範囲の明示 — 全ノードの証明にはならない、と手順自身に書く。
6. 既存の受入 lease (`tools/wave_land_window.py`) を流用しない。あれは並行 dev-wave の
   受入予約であって campaign process や計算 job を排除しない。

**発行 tool に「動いている process が無いか」を検査させる案は提案しない** — 名簿が存在せず、
login ノードの `pgrep` が 0 件でも他ノードの旧 process を見逃すため、偽の保証になる。

**見送り時の影響**: (a) は活性化を実施できる時刻を狭めるだけで、成果物の schema も数値も
変えない。(b) では混在が起きた場合、D195 により全 leg の再走が必要になり、certified 値が
確定しない時間が延びる。しかも据置 env と receipt を持たない書込み口は事後分類もできない (§1.4)。

### R3 — 2 回目以降の活性化をいつ許すか

[T-657] の serial 2 は並行 wave が手動の同一 commit 手順で実施中で、これは前提として動かさない
(ユーザー指示「実装は [T-657] の land 後の次弾」と整合)。問いは **serial 3 以降**である。

- **(a) 推奨 — R1/R2 の採用分が land するまで、次の活性化を始めない。**
- (b) 材料が先に揃った場合、もう一度だけ手動で許す。
- (c) 以後も手順のみで反復する (= R1(a) を選んだ場合はこれが既定になる)。

**補足**: 現在の登録は linux-baremetal g1 と pegasus g1/g2 だけで、発行 tool は未登録世代を
拒否し、全 env 据置の no-op も拒否する。**したがって今の材料だけでは serial 3 を発行できない。**
この問いは「新しい較正世代が登録されたとき何を先に済ませるか」という順序の話である。

**見送り時の影響**: (a) は将来の活性化時期を遅らせるだけで、現在の値も受理集合も変えない。

### R4 — 記録の置き場

- **(a) 推奨 — `docs/pegasus-runbook.md` に activation 専用の新しい節を作る** (§7.3 の受入
  lease とは別契約として、混同しないよう節を分ける)。
- (b) 既存の §7.3 付近へ追記する。

**補足**: `docs/dev-wave/**` の byte 予算 ([T-664] で逼迫中) は**本件では消費しない** —
runbook に `tools/check_docs.py` の byte 上限は無く、現状 `check_docs: 違反なし`。
段 3 レンズ B の予算超過懸念はこの点で当たらないが、節境界を切らずに §7.3 へ混ぜると
受入 lease と activation 窓が同じ契約に見える、という指摘は当たっている。

---

## 3. 採用時に守る不変条件

1. head の exact pin (serial + state hash) を保つ。観測した head を信じる設計にしない。
2. 自動 reload を入れない。新しい head の適用は `exec` による起動し直しだけとする。
3. 分裂の両方向は拒否のままにする (発行済み・head 未更新 / head 更新済み・record 未配備)。
4. 診断の構造化 (expected / observed) を保つ。
5. [T-658] の見送り範囲を復活させない — receipt の無い書込み口を新たに拒否しない、全書込み口へ
   activation の field を配線しない、land 側で混在を機械拒否しない。
6. 事後分類は補助の診断に留める。混在を検出したら D195 どおり同一 commit で全 leg を再走し、
   新しい hash で古い値を書き換えたり混在を許容したりしない。
7. 手順の中で「保証」と書けるのは列挙した閉集合についてだけとする (R0)。

## 4. 本 wave が扱っていないもの

- **実装**: runbook の執筆も tool の handoff 文も書いていない。実装は [T-657] land 後の別 wave。
- **[T-658]**: receipt の全書込み口配線 (見送り済み、復活させない)。
- **[T-660]**: head=2 での末尾巻き戻し検出力 — 並行 wave `dev-wave-t657-t660-g2-activation` が担当。
- **全 process の名簿 / fencing token**: 入力が存在しないため設計しない。必要なら別 wave。
- **実機の並行実行 probe**: main 更新中の読み取り競合と SIGKILL 残骸は制御フローからの推論で、
  実走していない。
- **PBS wrapper の全分類**: T126 と generic dispatch の差は確認したが、全 wrapper は未監査。

## 5. 親が段 3 の指摘で訂正した自分の記述

- 「窓は 2 つ」→ 3 段の壁 (§1.2)。
- 「record と head はどちらも git tracked」→ **新 record は untracked** (§1.3)。実測で確認。
- 「receipt の serial で混在を追える」→ **追えない**。durable には `contract_sha256` しか
  載らず、据置 env は区別できない (§1.4)。
- 「probe で live 経路に fail-open が無いと実測した」→ 実測したのは leaf の検証関数の範囲まで。
- P1 の親案 (発行 tool に head も書かせる) は**取り下げ**、選択肢から落とすことを推奨 (R1)。
- 段 2 プランの推奨 (機械検査を作る) も**採らない**。理由は成果物の値が変わらないこと (R1)。
