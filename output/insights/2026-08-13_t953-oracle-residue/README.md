# [T-953] SWO oracle 残余 5 件 — wave 逐語一式 (2026-08-13)

wave = `dev-wave-t953-oracle-residue` / branch = `worktree-dev-wave-t953-oracle-residue` /
起点 = `adf7997f`

worklog の該当エントリが要約の正本。ここは機械成果物の凍結先である。

## 何をしたか

[T-316] R2-b が残していた SWO oracle の残余 5 件 (a)〜(e) を閉じた。

- (a) 候補 compile 失敗時に trusted control の**事後** compile (postflight) を行い、
  環境故障との相関を測る。候補成果物は postflight の前に除去し、postflight は専用の
  別一時 directory で走らせる。除去に失敗しても postflight は飛ばさない。
- (b) contract ID を再構成し、公理判定の**実装 bytes** と走査範囲の意味論定数を束縛する。
  変更前は 2 関数 bundle と corpus データ hash だけで、`_CORPORA=(0,)` のように
  検査範囲を半減させても identity が動かなかった。
- (c) critic の oracle finding validator に kind ごとの exact key 集合、閉じた reason_code
  集合、producer 正準形の corpus_id、observations 要素の schema を入れる。
- (d) S1 の oracle REJECT を session ledger へ耐久化する。
- (e) S6 の docstring を実体へ是正する。

## 成果物

| ファイル | 内容 |
|---|---|
| `mutation-spec.json` | 段 4 で事前登録した変異 12 件 (負例 9 + 正例 3) の spec。schema `izanagi-dev-wave-mutation-spec/v1` |

変異の本走結果 (`mutation-ledger.json`) と実測値は段 7 の記録 commit で追加する。
本 commit の時点では**未実走**である。
