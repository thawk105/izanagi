## 攻撃した箇所

- §5.1 と既存の「両アームで同一」— 矛盾は成立しない。追加文が driver 別値とアーム間同一性を区別している。
- §0 の配置規約— 違反なし。§5 の値セルに規範は漏れていない。
- §10 の不足記述— 一部攻撃成立。「未登録」は正直だが「残るのは値の指名だけ」は狭すぎる。
- D1060 との関係— 同一ではないが、値セルを維持して §5.1 に解除条件を置く統治形式は同じ。
- 新しい権限主体— 攻撃不成立。承認者の枠は追加したが、主体を捏造せず未指名の blocker として残している。
- 文書と実装の行 grammar— 攻撃成立。tag・順序・区切りは一致するが、model と hex の字句集合が一致しない。
- T-2005 への正直さ— 未登録・record 未発行の明記は成立。ただし残作業の記述が不足する。

## 所見

### 1. `<slug>` と `<64 hex>` は実装の受理集合より広い

- **逐語または file:line**  
  文書は `expected_claude_model_snapshot=<slug>` と `<64 hex>` を要求する。[事前登録:222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:222)  
  実装は model を `claude-opus-[^;\r\n]+`、hash を `[0-9a-f]{64}` に限定する。[author patch:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2005-b4-projection-registration/s5-author.patch:38)

- **なぜ問題か**  
  tag の綴り、順序 `base; sort; trigger`、区切り `; ` は完全に一致する。しかし文書上は任意の slug や大文字 A-F を含む 64 桁 hex が許されるように読めるのに、実装は拒否する。逆に regex は `claude-opus-` 後の空白なども受理し、通常の「slug」より広い。

- **成果物の値・受理集合がどう変わるか**  
  文書どおりに作った行が verifier に拒否される場合と、slug と呼べない文字列が受理される場合がある。文書を `claude-opus-` 始まり・64 桁 lowercase hex と明記するか、実装側を文書の slug 定義へ合わせる必要がある。

### 2. 「残るのは値の指名だけ」は T-2005 の残作業を過少に述べる

- **逐語または file:line**  
  §10 は「3 driver の projection closure hash は…未登録」と認めた直後、「残るのは値の指名だけ」とする。[事前登録:787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:787)  
  一方、§5 は対象セルを含む多数の欄が `未記入` であり、発効には全欄・§6・commit が必要である。[事前登録:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2005-b4-projection-registration/docs/phase3-b4-reflux-ablation-preregistration.md:34)  
  裁定も値セルと admission record artifact を明示的に対象外としている。[段4裁定:65](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2005-b4-projection-registration/materials/s4-adjudication.md:65)

- **なぜ問題か**  
  model 値の指名だけでは足りない。先に 4 点の規範を別 commit で固定し、model・prompt・projection 3 件を原子的に記入し、発効可能な文書を commit し、さらに admission record を発行する必要がある。raw record schema は依然として projection 1 値であり、3 値の拘束は文書 binding と実走前照合による間接構成である。

- **成果物の値・受理集合がどう変わるか**  
  現状は §5 の値も JSON record も増えておらず、実走の受理集合は開かない。「残るのは値の指名だけ」を残すと、T-2005 がほぼ完了し record 発行だけが自動的に続くように誤読される。「本項の機構実装は完了したが、値の記入・発効 commit・record 発行は未了」と限定すべきである。

## 反証できなかった懸念

- 「両アームで同一」は、各 driver の hash を相互に同一にせよという意味ではない。続く driver 別規範で解消されている。
- 規範は §5.1 に置かれ、§5 の値セルは維持されている。§0 違反はない。
- patch は固定順の 3 tag を `fullmatch` し、verified admission がある pair 生成点で全 3 件を live 値と照合する。
- 「承認する人間」は未指名の要求であり、既存の記入者・レビュー者や実行責任者へ勝手に権限を付与していない。
- §5.1.1 の raw pin は編集範囲外であり、analysis consumer の切出し境界にも影響しない。

## 総括

grammar の字句集合不一致と、§10 の残作業過少記述の 2 件が成立する。  
機構は段4裁定の限定範囲では実装されているが、3 hash は未登録で record も存在しない。  
したがって T-2005 を完了扱いにはできない。  
pytest は実行しておらず、結論は指定資料と patch の静的検査による。