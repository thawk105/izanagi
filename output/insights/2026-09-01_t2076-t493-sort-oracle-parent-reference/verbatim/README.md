# 逐語 — 正規化の erratum

子の成果物をそのまま置いている。ただし 3 file は Markdown の行末 2 空白 (hard line break) を
含み `git diff --check` に抵触したため、**行末空白の除去だけ**を行った。可視文字は 1 文字も
変えていない。復元は各行の該当位置へ空白を戻すことで行えるが、意味の読み取りには不要である。

| file | 原文 sha256 | 原文 bytes | 現行 sha256 | 現行 bytes | 差 |
|---|---|---|---|---|---|
| `s2-plan.md` | `40675913d5139e6ba5f32939debb45b65d44f0341c5862b6a690b6cad1aff585` | 20651 | `a7a8af8bba6fa637563e4c7a203a0833ee3b0d85a40702fae5bb96f303b4bedd` | 20641 | -10 |
| `s3-consult-a2-sol.md` | `ebf406ddabde296c4fb69661d8d75a83869d2b26c1f0e52e1557d66b1b010ef2` | 12955 | `690e0921de9ab21a6b8bfcf6bc4ed399b88088f5bb6789cccee1ef55db4a3d5e` | 12953 | -2 |
| `s3-consult-b-luna.md` | `bc903db308079fd92197e0ae6da1667b38fbdd64c61f5693482b223fbe57a495` | 19987 | `1031435e6a8ab5cc8acff02f2809624554ea2671156830d0a97ed6269bd53ab6` | 19967 | -20 |

正規化コマンドは各 file への `sed -i 's/[ \t]*$//'` で、除去したのは行末の空白と tab だけである。

## 段 3 レンズ A について

最初の投入 (`s3-consult-a-prompt.md`) は upstream の内容フィルタで turn ごと失敗し、
成果物が 0 bytes だった。ここに置いてあるのは書き直して通った 2 回目 (`a2`) である。
経緯は failures 台帳の F45 再発を参照する。
