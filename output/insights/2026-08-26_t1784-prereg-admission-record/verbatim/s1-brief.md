# 段 1 brief — [T-1784] 事前登録 §5 の事前 commit を機械で要求する admission record

wave: dev-wave-t1784-prereg-admission-record / base main 9463bcbc / 環境 pegasus02 (login node, nproc 96)

## scope

B-4 還流 ablation の実走を、**実走前に commit された admission record 無しには開始できなくする。**
実装側だけを担う。事前登録文書は 1 byte も触らない (併走 wave の編集予約。下記「編集面重複の実測」)。

- (A) **admission record の新設。** 実走前に確定できる期待値
  (`projection_sha256` / `effective_prompt_sha256` / `model_snapshot`) と、それを束縛する
  事前登録文書の commit を持つ record を新モジュールで定義する。canonical bytes と検証は
  そのモジュールが持つ。
- (B) **controller の必須入力化。** 閉じた critic invocation の生成経路が admission record を
  **必須引数**として要求し、実走時の実測値が期待値と一致しなければ停止する。
  record 不在・束縛不能は「実行しない」に落とす。

実走 (B-4 標本採取)、§5 の欄を埋める作業、段 4 driver への配線は本 wave の scope 外。

## 確定済みユーザー裁定・引数の裁定

- **command 引数の裁定** — 併走 wave と重なるなら scope を admission record の実装側
  (controller の必須入力化) に寄せ、文書側の編集は最小にする。**実測の結果、重なりは
  文書側 §5 表・§5.1 で確定したので、文書編集は 0 byte とする。**
- **D904** — 閉じた critic 起動は既存 role file を 1 byte も変えず別形として足す。
- **D824 決定 5** — `docs/phase3-main-experiment.md` を 1 byte も変えない。
- **規律 2** — 充足していない前提条件を緑に見せる書き換えをしない。本 wave は
  「§5 が埋まっていない」状態を**実走停止として機械に表明させる**のであって、埋まったことにしない。

## 不変条件 (破ったら停止)

1. **`docs/phase3-b4-reflux-ablation-preregistration.md` を 1 byte も変えない。**
   併走 wave `dev-wave-b4-prereg-enactment` が §5 表 (150-163) と §5.1 (165-192) を編集予約済み。
2. **併走 wave の変更面を触らない** — `orchestrator/campaign/p3_s4_loop.py`、
   `p3_s4_loop_sort.py`、`p3_s4_loop_trigger_gating.py`、`orchestrator/tests/test_p3_s4_loop.py`、
   `docs/phase3-s4b-runbook.md`。
3. `.claude/agents/critic.md` を 1 byte も変えない (D904)。role file を触ると `review_ledger.py` の
   role 名 key pin 群・`codex_roles/manifest.json`・originless baseline が一斉に発火する。
4. `docs/phase3-main-experiment.md` を 1 byte も変えない (D824 決定 5、F78)。
5. **admission record の file を `projection_closure_manifest()` の entries に加えない。**
   同 manifest は `p3_b4_closed_critic.py` 自身を含むため、record を閉包へ入れると
   「自分の hash を自分が宣言する」自己参照になり、充足不能になる (F36)。
6. 切替点を動かさない。アームの切替は `p3_s4_loop.make_critic_digest(reflux=)` のまま (§3.1)。
7. 新 gate は署名で禁止を書き、**通る正例を 1 つ添える** (DW-S04)。恒真な関門にしない。
8. 事前登録の発効宣言をコードにも docstring にも書かない。§0 が「本書に書かれた宣言では
   発効しない」と定める。

## provisional 裁定 (親の暫定。攻撃対象)

- **(P1) 期待値 3 つのうち、事前に「計算できる」のは 2 つ、「宣言するしかない」のは 1 つ。**
  `projection_sha256` と `effective_prompt_sha256` は repo の bytes だけから実走前に確定する
  (実測済み。下記 DW-O13)。`model_snapshot` は実走の `modelUsage` からしか観測できないので、
  record は**期待値の宣言**を持ち、controller が実測値と照合して不一致で止める。
  「予測」ではなく「事前宣言 + 実行時照合」がこの欄の正しい意味である。
- **(P2) record は事前登録文書の commit を束縛する。** record は (a) 文書 path、(b) その版の
  blob sha256、(c) その版を含む commit を持ち、controller は record の宣言する blob が
  実際にその commit に存在することを確かめる。**§5 の欄が埋まっているか否かの判定を
  controller に持たせるかは段 2 の課題** — 文書の書式へ機械が依存すると、併走 wave が
  §5 を書き換えた瞬間に壊れる。
- **(P3) 必須入力の置き場所は `create_b4_closed_critic_pair` の必須キーワード引数とする。**
  既定値を持たせない。既定値を持たせた瞬間、既存の呼び手が黙って record 無しで通る。
  `main` の CLI も必須オプションにする。
- **(P4) `create_b4_closed_critic_pair_for_test` は record を要求しない。**
  test 経路は `evidence_class="test-only"` を焼くので正式標本にならない。ただし
  **test 経路から certified を作れないことは既存テストが固定済み**であり、その固定を弱めない。
  段 2 はこの非対称が抜け道にならないか攻撃対象として扱う。
- **(P5) 不一致時の挙動は例外による停止**とし、警告・環境変数・CLI flag の逃がし道を作らない。

## 成果物影響 (DW-G05)

- **(A)(B) を実装しない場合:** B-4 の実走は、走らせてから receipt に現れた model / prompt /
  projection の値を §5 へ書き写せてしまう。事前登録 §1 が自ら書いた穴 —
  「§5 が空の版を祖先に持つだけで ancestry 条件を満たし、結果を見てから埋めた版を後で
  commit できる」— がそのまま残り、論文 §8 の B-3 / B-4 を「事前登録された実験」として
  報告できない。台帳に載る値そのものは変わらないが、**その値に事前登録の効力が付かない。**
- **(P3) を既定値付きで実装した場合:** 既存の呼び手が record 無しで通り、gate が恒真になる。
  受理集合は現状と 1 件も変わらず、実装した意味が消える。

## 実アンカー表 (変更面候補。分類文は置かない)

|path|anchor|現状|
|---|---|---|
|`orchestrator/campaign/p3_b4_admission_record.py`|(新設)|不在|
|`orchestrator/tests/test_p3_b4_admission_record.py`|(新設)|不在|
|`orchestrator/campaign/p3_b4_closed_critic.py`|`create_b4_closed_critic_pair` 944|admission 引数なし|
|`orchestrator/campaign/p3_b4_closed_critic.py`|`_prepare_b4_closed_critic_pair` 904、`_seal_b4_closed_critic_pair` 929|`closure_sha256 = projection_sha256()` を 925 で取り controller へ渡す|
|`orchestrator/campaign/p3_b4_closed_critic.py`|`B4ClosedCriticController.invoke` 668、provenance 束縛 779-786|`model_snapshot` / `effective_prompt_sha256` / `projection_sha256` を receipt へ書く。期待値との照合なし|
|`orchestrator/campaign/p3_b4_closed_critic.py`|`main` 1443|CLI。admission 引数なし|
|`orchestrator/campaign/p3_b4_closed_critic.py`|`projection_closure_manifest` 501|**触らない** (不変条件 5)|
|`orchestrator/tests/test_p3_b4_closed_critic.py`|`create_b4_closed_critic_pair` を呼ぶ既存テスト|必須引数化で呼び手全数の追随が要る|

## 編集面重複の実測 (F606 の 3 面 + 稼働 process)

走査面 4 つ。(a) 稼働 process の cmdline 全走査 (`ps -eo pid,lstart,args`)、
(b) repo 外 job dir の brief / plan / prompt、(c) 登録済み全 worktree (38 本) の branch tip、
(d) 作業ツリーの未 commit 差分。(c)(d) は同一 worktree へ `git status` を同時に当てない (F615)。

**hit 1 件。** `dev-wave-b4-prereg-enactment` (job dir `/home/SFC/tanab/.claude/jobs/8b5f61ea`、
2026-08-26 09:38 起動、段 2 plan 実行中、branch `worktree-dev-wave-b4-prereg-enactment` は
main と同一 tip)。その段 1 brief の scope が

- (A) §6 前提条件 3 の「段 4 driver への必須配線」— `p3_s4_loop.py` / `p3_s4_loop_sort.py` /
  `p3_s4_loop_trigger_gating.py` / `test_p3_s4_loop.py` / `p3_b4_closed_critic.py` の
  receipt seam / `docs/phase3-s4b-runbook.md`
- (B) **§5 の欄を実走前に埋めて commit する** — `docs/phase3-b4-reflux-ablation-preregistration.md`
  §5 表 (150-163)・§5.1 (165-192)・§6 項 3・§7.2・§8・§10

**(B) は T-1784 の文書側と完全に同じ場所である。** よって本 wave は文書を 0 byte とし、
「値を書く側」を併走 wave に、「値を機械が要求する側」を本 wave に分ける。この分割は
競合ではなく合成になる — 併走 wave が §5 へ書いた値を、本 wave の gate が実走時に要求する。

**残る重なりは `p3_b4_closed_critic.py` 1 file。** 併走 wave の anchor は
`_read_verified_terminal_receipt` (1120) / `B4ClosedCriticReceipt` (182) / `main` (1443)、
本 wave は `create_b4_closed_critic_pair` (944) / `invoke` (668) / `main` (1443)。
`main` だけが共通する。両者とも加算的な hunk であり、後着側が merge で解く。
段 3 のレンズにこの境界を明示的に攻撃させる。

落ちた面: 未起動 wave の意図、3 日より古い job dir、ignored untracked、stash。

## pin 閉包 (DW-O09)

`orchestrator/campaign/p3_b4_closed_critic.py` を `tools/ orchestrator/ hooks/` の `*.py` 全文で
検索。自モジュールと自テスト以外の**呼び手・pin は 0 件**。docs の hit 3 件
(`phase3-b4-...-preregistration.md:204`、`phase3-s4b-runbook.md:112`、`decisions.md:33851`) は
いずれも散文で bytes を pin しない。

`output/insights/2026-08-26_t1697-closed-critic-invocation/mutation-spec.json` が同 path と
test node 名を持つが、これは T-1697 の変異台帳 (歴史記録) であって live な bytes pin ではない。
本 wave の変異 spec は新規に起こす。

**同名識別子の二義化に注意 (D75):** `docs/freeze-permanent-design-s2.md:335,347` の
`projection_sha256` は freeze-permanent の report key であり、本件の
`p3_b4_closed_critic.projection_sha256()` とは別物。record の field 名はこの衝突を避ける。

## gate 入力の実在と値域 (DW-O13)

|入力|存在|実走前に確定するか|実測|
|---|---|---|---|
|`projection_sha256()`|`p3_b4_closed_critic.py:536`|する (repo bytes のみから決まる)|`df37ca0d1e98b4fb2346db751fed0ddf7fc169dd9b863a7ce9ff3b1d87efff46`。閉包 entry 10 件 (module 自身 / provider / `p3_s4_loop.py` / `artifact_admission.py` / `s8b_prediction_runner.py` / `role_session_isolation.py` / `critic/digest.py` / `critic/identity_projection.py` / `.claude/agents/critic.md` / mediated contract)|
|`effective_prompt_sha256`|`claude_projected_provider.py:169`|する (critic.md の body + 固定 contract 文字列の sha256。LLM 呼出し不要)|構成要素を実測済み|
|`model_snapshot`|`claude_projected_provider.py:353` = `opus_slugs[0]`|**しない。** `modelUsage` から実行時に観測|値域 = `claude-opus-` で始まる slug **ちょうど 1 個** (`:327` が `len != 1` を拒否)。実 receipt は repo に未保存のため具体 slug は未実測 — 段 2 はこれを「宣言 + 照合」で扱う|

**閉包が自分を含むことの帰結:** 併走 wave が `p3_b4_closed_critic.py` か `p3_s4_loop.py` を
1 byte でも変えれば `projection_sha256` は変わる。よって admission record は
「実走直前に、凍った code に対して」作られるものであり、開発中に作り置きできない。
この性質を record の docstring と検査へ明示する。

## 環境

- 開発・軽量検査: pegasus02 (login node)。build/bench を伴う計測は本 wave では行わない。
- 受入全走: `tools/dev_wave_wait.py acceptance` 経由。

## 分割方針

受理集合が変わる (record 無しの実走を拒否する) ため軽量版にしない。
段 2 plan 1 本 (codex read-only)、段 3 敵対 2 本 (レンズ: 「gate が恒真になっていないか /
逃がし道はないか」と「併走 wave との境界と自己参照 hash が壊れていないか」)、
段 5 author 1 本、段 6 review 2 本 + fix。docs 本文は親が編集する (本 wave では
worklog / decisions / failures の fragment のみ)。
