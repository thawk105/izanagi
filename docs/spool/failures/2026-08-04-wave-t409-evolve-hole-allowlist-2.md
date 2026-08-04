---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-04
wave: wave-t409-evolve-hole-allowlist
seq: 2
---

## 新規

### {{F:adversarial-prompt-refused}}. 敵対レビュー prompt が攻撃者視点だったため上流分類器に拒否された [コンテキスト浪費]

- 事象: [T-409] 段 3 のレンズ A で `codex exec` が `rc=1` で終了し、出力ファイルが 1 件も
  残らなかった。ログ末尾は `This content was flagged for possible cybersecurity risk`。
  `reasoning=max` の走行が丸ごと無駄になり、レンズ 1 本を書き直して再投入した。
- 根本原因: prompt が「この関所を通ってしまう入力を構成せよ」「1 つでも作れたら赤である」と
  攻撃者視点だけで書かれていた。izanagi の防壁強化は本質的に自分の関所を破る入力を探す作業なので、
  素朴に書くと exploit 開発と同じ文面になる。実態は自リポジトリの入力検証を厳しくする防御作業である。
- 恒久対応: memory `codex-adversarial-prompt-defensive-framing` — 敵対 prompt の冒頭に
  (a) 対象が自プロジェクトの入力検証であること、(b) 成果物が境界テストの negative ベクタに
  なること、(c) 第三者システムへの侵入手法の調査ではないことを書く。依頼語も「攻撃せよ」
  一辺倒でなく「受理範囲は意図と一致するか」へ寄せる。
  `docs/dev-wave/workers.md` の `DW-S03` へは書かない — dev-wave 系の byte 予算が
  25,196 / 25,200 で残り 4 bytes であり、予算引き上げも dev-wave の外出しも既裁定で禁じられている
  ([T-127] 裁定、D94 却下案 (a))。
- 再発検知: `.done` の rc が非 0 かつ `-o` 出力が不在という組み合わせ。`DW-O01` が既に
  「完了は `.done` の存在と exit code だけで判定する」と定めており、この形の失敗は必ず露見する。
- 補足: 中身 (具体的な入力例を出させること) は削っていない。書き直した版は同じ深さの所見
  (must-fix 3 件) を返したので、防御目的の明記は所見の質を落とさない。
