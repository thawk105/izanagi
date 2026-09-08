単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair

必読事項の射影:

- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/s1-brief.md`
  — 親の段 1 brief。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/verbatim-d1625.md`
  — 確定済みユーザー裁定 D1625 の逐語。読めなければ即停止。
- `/home/SFC/tanab/.claude/jobs/0ef29ace/tmp/dev-wave-t2314-inert-reason-pair/verbatim-carry-t2314.md`
  — worklog の [T-2314] 持ち越し逐語。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/tools/pegasus/probes/t316_sandbox_backend_probe.py`
  — 変更対象の production file。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/campaign/condition_meaning_gate.py`
  — gate 本体 (**読むだけ。変更しない**)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_t316_sandbox_probe.py`
  — 変更対象の test file。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2314-inert-reason-pair/orchestrator/tests/test_condition_meaning_gate.py`
  — gate 側の既存正例 (root-location-only の緑を作る手順の参考)。読めなければ即停止。

## 依頼

`file:line` 粒度の実装プランを起草せよ。実装はするな。書込み可能な tmp が無いので pytest 緑は
要求しない。静的検査で足りる。テストの実測は親が行う。予算が尽きそうなら、途中結論を下記の
出力形式どおり書いて終われ (無出力が最悪)。

## 変更の中身 (裁定済み・変更不可)

probe の `_condition_gate_family_valid` は現在、supply arm の緑を
`reason_code == "stock-inert-preprocess-identical" かつ evidence["comparison"] == "stock-inert-identity"`
という **1 組の exact 一致**でしか受理しない。これを、gate の `status_contract` 表が定める
**inert 比較の 2 組**

1. (`stock-inert-preprocess-identical`, `stock-inert-identity`)
2. (`stock-inert-preprocess-root-location-only`, `stock-inert-root-location-only`)

の**どちらか 1 つに exact 一致**する場合だけ受理する形へ変える。さらに、**どちらの組が発火したかを
probe の記録 (`condition_gates` の受領証) に残す**。

## 決めてほしいこと

1. `_condition_gate_family_valid` の書き換え方 (受理する組の定数をどこにどう置くか、
   組を跨いだ交叉を確実に弾く形か)。gate の第 3 の理由コード
   `requested-default-preprocess-different` を受理してはならない。
2. 発火した組の記録形。親の provisional 裁定は「`_condition_gate_receipt_summary` の supply entry へ
   `comparison` を明示 field として足す」。この案の是非と、代替案 (理由コードだけで足りるとする案) の
   比較。受領証の各 entry に `evidence` という key を出すことは既存 test が禁じている。
3. 追加する test の nodeid と file:line。最低限、2 組それぞれの正例と、組を跨いだ交叉
   (reason=identical × comparison=root-location-only、およびその逆) の負例を含めること。
   既存 fixture `_condition_gate_family(comparison)` は reason_code を
   `stock-inert-preprocess-identical` に固定しているので、2 組目の正例を作るには何が必要かを
   実コードから読み取って書け (gate の `require_condition_gate_family` は組の不一致を
   `admission-contract-invalid` で弾くので、evidence を含めた本物の record が要る)。
4. 波及する既存 test の列挙 (参照関係で引く。名前の推測をしない)。

## 禁止

- gate 本体 (`orchestrator/campaign/condition_meaning_gate.py`) の変更を提案しない。
- 新しい gate・検査・台帳・互換層・一般化を提案しない。仮想リスク向けの防壁を足さない。
- 既存テストの期待値の変更・緩和・反転・skip・削除を提案しない。
- 受理集合を D1625 の 2 組より広げない。exact 一致検査を外さない。
- commit・git 操作・docs 編集をしない。ファイルを書き換えない。

## 出力形式

```
## プラン
（file:line 粒度。変更前後の断片を示す）

## 決めた点と根拠
（上の「決めてほしいこと」1〜4 に一対一で答える）

## 追加・変更する test
（nodeid、置き場所、正例か負例か、何を殺すか）

## 波及と未解決
（参照関係で引いた consumer、判断できなかった点）

## 総括
（3〜6 行）
```
