# 段 1 brief — [T-1721] A-1 対測定を formal=false の探索値として投入する

基準 commit: `9463bcbc` (local main と同一)
wave branch: `worktree-dev-wave-t1721-a1-paired-submit`
worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/t1721-a1-paired-submit`

## scope

ユーザー裁定 ({{D:a1-paired-runs-as-exploratory-value}}、2026-08-26 の /rulings 全件) は
「A-1 対測定を `formal=false` の探索値として先に投入し、論文 §8 は据え置く。D510 決定 7 に従い
探索値を後から正式へ昇格しない」である。引数は「装置と事前登録は凍結済みで投入だけが残る」とし、
「この投入は正式 certification ではないので批准 (D905) の gate は通らない (= 適用されない)。
ただし着手時にその前提を probe で確認し、通らないなら理由を構造化して報告すること」と命じている。

本 wave の scope は **(1) その前提の実測、(2) 前提が偽なら投入せず、正当な代替経路の全数探索と
その否定の裏取り、(3) 裁定パッケージと台帳記録**である。計算ノードへの qsub は前提が真の場合だけ行う。

## 確定済みユーザー裁定 (不変条件)

- **D905**: enforcement closure 批准の執行経路は AI が成りすませない実行主体を新設する案だけを採る。
  人間の転記を残す案・平文承認へ移す案は採らない。**設計が着地するまで批准は進めない。**
- **D758 決定 2 / 決定 4**: 行の貼り付け・コマンド実行を人間手番に置く設計は採らない。
  塞いでいるのは AI 側の設計作業であってユーザーの手番ではない。
- **D510 決定 7**: 探索値を後から正式へ昇格しない。
- **絶対規律 2**: 正しさゲートを緩める変異を許さない。
- **絶対規律 1 / 4**: trace-disabled build で計測、レコード数は calibrator の最小値。
- wave 971 の凍結: 反復数 write-heavy 72 / balanced 205 / read-heavy 28、判定規則、policy v2、
  凍結文書 `output/insights/2026-08-26_paper-story-a1-sized-preregistration/README.md` の SHA-256 束縛。
  **凍結は自分が直前に書いたものでも拘束する (DW-O12)。**

## 親の実測 (段 1 前 probe、すべて main 9463bcbc の read-only 実走)

(P1) **A-1 の measure 経路は批准 gate を無条件に通る。** 親の provisional 裁定であり攻撃対象。
呼出し鎖:
- `orchestrator/campaign/paper_story_a1_paired.py:2531` `run_campaign(...)`、
  `:2545` `declared_use_class=DECLARED_USE_CLASS` (`:65` = `"exploration"`)
- `orchestrator/campaign/loop.py:223-229` — `declared_use_class` は layout selector を選ぶだけ
- `orchestrator/campaign/loop.py:288` — `ident.ensure_resumable_wal(cfg, layout,
  admission_policy=..., authorization_contract=...)`。`require_environment_contract` を渡さない
- `orchestrator/campaign/ident.py:370` — 既定 `require_environment_contract: bool = True`
- `orchestrator/campaign/ident.py:443-444` — `if require_environment_contract:
  binding = _capture_current_loader_binding()`
- `orchestrator/campaign/ident.py:239` — `verify_ratified_contract_loader_binding(binding)`
- `orchestrator/campaign/contract_loader_binding.py:396` — `require_ratified_closure(...)`

対照: `orchestrator/campaign/guided.py:196,222` は exploration で
`require_environment_contract=False` を**明示的に渡している**。つまり「exploration だから
自動的に外れる」ということはない。

(P2) **実走 probe の結果。** 親の provisional 裁定であり攻撃対象。
```
capture_contract_loader_binding()          -> commit 9463bcbcb1541625db59abb97cf6a76934b4c80c
verify_live_contract_loader_binding()      -> OK
verify_ratified_contract_loader_binding()  -> ContractLoaderBindingError:
    enforcement-source-ratification: ratification history is not a strict prefix extension
```

(P3) **失敗理由 A — 構造的。digest 比較より前で落ちる。** 親の provisional 裁定であり攻撃対象。
`orchestrator/campaign/enforcement_source_ratification.py:265-327`
(`_committed_ratification_digests`) は
`git log --format=%H --reverse --full-history HEAD --
hooks/enforcement-source-closure-ratifications.v1.jsonl` を辿り、
各 commit の blob が直前 blob の**真の**接頭辞拡張であることを要求する (`:310-314`)。
実測した履歴は 17 commit。先頭 `6188a8d4` (2026-08-25 02:59、台帳開設、1 行 112 bytes) 以外の
16 件はすべて merge commit で blob が不変 (112 bytes)。よって 2 件目で
`len(blob.stdout) <= len(previous_raw)` が成立し例外になる。
**この関門はどの digest に対しても値を返さない。** wave 971 当時の main `f4c2c5de` でも
同型の 16 commit 列であり、新規回帰ではなく既存の破れである。

(P4) **失敗理由 B — digest 不一致。** 親の provisional 裁定であり攻撃対象。
- 現行 closure digest: `6d497998c4b80a186cd9ee3fc98154e29ddd0aa23f82f7da215558b90e32bf5a`
- 台帳の唯一の行: `db511c3d841128bfdbf5ba7c6bbdb2ce4da1fe0fdefe8d52aaacb0906ddeea44`
台帳へ行を足す行為が批准そのものであり、D905 が禁じている。

(P5) **旧批准 commit で走らせる逃げ道は無い。** 親の provisional 裁定であり攻撃対象。
`db511c3d` を批准した commit `6188a8d4` にも `paper_story_a1_paired.py` は在るが、
`STUDY_ID = "paper-story-a1-20260824-exploratory-v1"` であり
`paper_story_a1_paired.v2.json` は存在しない。wave 971 が凍結した sized-v1 事前登録
(反復数 72/205/28) はこの commit に無く、ここで走らせても事前登録した study ではない。

(P6) **候補として却下すべき経路。** 親の provisional 裁定であり攻撃対象。
`run_campaign` へ `require_environment_contract=False` を通す改造は、
`guided.py` の先例があるとはいえ、(a) 凍結済み装置の identity 束縛の姿勢を変え、
(b) 正しさ防壁の適用範囲を AI 判断で狭める形になる。DW-C00 と絶対規律 2 に照らし
親は実装せず、裁定パッケージとしてユーザーへ返す。

## 成果物の形

- 実装差分ゼロ。コード・テスト・policy・job body・凍結文書を 1 byte も変えない。
- `docs/spool/` へ worklog fragment 1 本、failures fragment 1 本 (批准検査が merge commit で
  構造的に通らない件)、必要なら decisions fragment 1 本。
- 段 9 で local main へ land。
- 裁定パッケージをユーザーへ返す。

## DW-G05 成果物影響

この blocker を放置した場合、論文 §8 の A-1 は「D496 の枠組みで測り直した比較。まだ 1 件も無い」
のまま動かない。探索値も 1 件も得られない。逆に blocker を迂回して投入すると、
D905 が守っている「AI が自分にかかる防壁を自分で承認できない」性質を落とす。

## 並列分割方針

実装が無いため実装子は起動しない。段 2 で read-only codex に「投入を成立させうる経路の全数列挙」を
起草させ、段 3 で 2 レンズが親 brief と段 2 プランの双方を攻撃する。
