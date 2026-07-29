# 6b64d21 復元 provenance の一次証拠

- 対象: `6b64d21753d2cfc790f80caba29df7a40fef3072`
- merge tool event timestamp: `2026-07-29T11:29:17.925Z`
- merge tool event line SHA-256: `6bd12c991bd1f2918e49e149e7dea53b1c1c567df5d71e04b587550a25de069f`
- event field: `message.model = claude-opus-5`
- event field: `effort = xhigh`
- tool command: `git merge main --no-edit`
- tool outputの `MERGE_RC=0` は pipeline 末尾 `tail` の rc であり、Git merge の rc 証拠には数えない。
- merge 成立は、約 5 秒後に作られた対象 Git object が 2 parent を持つ事実で確認する。

role の裁定:

- merge 前に同 session は wave base と current main の worklog 番号衝突を発見し、対象 branch へ
  current main を取り込むと裁定した。
- merge 前に main の前進と番号衝突を調べ、current main を wave branch へ統合すると裁定した。
- merge 後の再採番・cross-reference 編集は子 commit の寄与であり、対象 role の根拠には数えない。
- 対象の操作は Git の機械代行だけでなく並行差分の採否を伴うため `integrator` とする。
- `scope` は当時の観測値ではなく後日分類になるため、復元 payload では省略する。

復元する値:

```text
product=claude; model=claude-opus-5; reasoning=xhigh; role=integrator
```

原 JSONL は repo 外の Claude session store にあり、本記録は session 識別子を除いた構造化抜粋である。
原 commit の message 欠落自体は変更せず、後続 correction から本記録へ到達可能にする。
