# 依頼逐語 (2026-09-21、/dev-wave 引数)

```
[T-2803] が「未測定」と書いた実 land の連鎖 (他 binding・partition・混雑時・計算ノード) での全史 provenance 監査の warm / cold
  を、T-2803 着地後に land した wave の受領証 (共有 store) と land-*.log から実測する (診断のみ、着手直前の local main から fresh
  worktree)。cold になった件ごとに原因 (checker sha 変更、.gitattributes、attributes 以外の binding 失効、partition 跨ぎ) を分類し、残る cold
  の主因に対する局所修正の候補 (entry 1769 §11 の候補列挙 memo 化・attr.tree 束縛・errno 正規化はその主因に当たる場合だけ)
  を効果見積り付きで裁定パッケージにする。監査の判定・受領証 schema・D2045 / D2192 の束縛は変えない。規律 2
  を緩めない。診断だけ。gate・台帳・一般化の追加は scope 外。
```
