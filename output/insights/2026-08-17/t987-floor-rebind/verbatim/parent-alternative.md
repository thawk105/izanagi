# 親の対案 (段 4 で段 2 案と比較する) — 2026-08-17 09:36 JST

段 2 案は「専用の記録付き再測定 lane」を新設し、production 9 file
(shell wrapper 2 本を含む) と test 8 file を触る。環境変数 marker
(`IZANAGI_FLOOR_REMEASUREMENT_NONCE`) で correctness authority の経路を切り替える。

親はこれを**過大**と見る。以下は同じ性質をより小さい面で満たす対案である。
採否は段 4 で敵対レンズの所見と併せて裁定する。

## 対案の骨子

### C1. `_authority()` の path を定数から**文書自身からの導出**へ変える

現状 (`orchestrator/campaign/s8b_holdout_admission.py:463-476`):

```
_PROTOCOL_REL = "output/s8b-freeze/floor_protocol.json"   # :64
...
_protocol_oid, protocol_raw = _head_blob(root, _PROTOCOL_REL)
protocol_document = _strict_json(protocol_raw, "floor protocol")
if protocol_document != dict(protocol):
    raise HoldoutAdmissionError("fixed protocol bytes do not match the supplied protocol")
```

対案: 渡された protocol 自身の `(contract_sha256, ccbench_pin)` から canonical path を
**機械導出**し (legacy anchor path も後方互換で許す)、その path の **HEAD blob** が
渡された文書と byte 一致することを要求する。

保たれる性質: 「受入の正本は commit 済み blob である」。
caller は path を選べない (導出のみ)。widening は path 定数の解除だけ。

### C2. C1 が開ける穴を、**発行時の継承検査を受入時にも再実行**して塞ぐ

C1 単独だと、`output/s8b-freeze/floor-protocols/` へ commit できる者が
自由欄 (master_seed / stock_configuration / wired_min_rel_floor 等) の異なる
protocol を正本にできる。これは受理集合の実質的拡大である。

塞ぎ方: versioned path を authority に採る場合に限り、受入時にも
`validate_ai_reseal_inheritance(legacy_anchor_document, supplied_document)`
(`orchestrator/campaign/s8b_floor_campaign.py:1057`、実体は
`s8b_floor_contract.validate_ai_reseal_inheritance`) を再実行し、
**legacy anchor からの継承 (可変 2 field 以外は同一)** を要求する。

これで versioned protocol の自由度は
`contract_sha256` と `ccbench_pin` の 2 field に限定され、
どちらも活性 env 契約と実 gitlink に束縛される。受理集合は実質広がらない。

### C3. 再測定の事実と入力を記録する (裁定の literal な要求)

記録先は段 2 案の
`output/env/<env_tag>/floor/attempts/submissions/<nonce>/floor-remeasurement-attempt.json`
と schema をそのまま採る (妥当と判断)。ただし
**env 変数 marker による lane 切替は採らない** — 記録は常に出す。
記録が作れなければ fail-closed で測定へ進まない。

### C4. wrapper の決め打ちを解く

`tools/pegasus/floor_campaign.sh` が legacy path を固定で渡す残留 (D471) を、
resolver が返した path を渡す形へ変える。

## 段 2 案との差

| | 段 2 案 | 親の対案 |
|---|---|---|
| authority | 既存 entrypoint 維持 + 専用 entrypoint 追加 (二重化) | `_authority()` の path 導出化 1 箇所 |
| lane 切替 | 環境変数 marker で分岐 | 分岐なし (単一経路) |
| widening の塞ぎ | 専用 entrypoint の 4 重束縛 | 受入時の継承検査再実行 |
| production 編集面 | 9 file (shell 2 本含む) | 3〜4 file |
| 攻撃面 | env 変数 1 つで correctness 経路が変わる | env 依存なし |

## 未検証 (段 4 までに詰める / レンズへ問う)

- `validate_ai_reseal_inheritance` が受入時に呼べる形か (legacy anchor document の入手経路)。
- 段 2 案が env marker を選んだ理由が、親が見落とした制約に基づくのかどうか。
- C1 の後方互換 (legacy anchor path) を残すと、legacy と versioned の両方が
  authority になりうる。resolver が exact 1 件を保証するので実害は無い、が要裏取り。
