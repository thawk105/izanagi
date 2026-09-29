# 活動範囲を新規最適化の創出へ広げる方針 — ユーザー発話と提案の写し (2026-09-29)

- authority: none
- default_effect: no-state-change
- 役割: roadmap の協議改訂 (§2 層2 の段 A・段 B ほか) と決定台帳・worklog の新規 item が参照する一次資料を、repo 内で引けるように bytes 一致で写したもの。
  判断の正本は決定台帳 (本 wave の decisions fragment が fold された D)、後続作業の可変状態の正本は worklog 末尾の「次の一手」である。
  この dir は可変状態を持たない。
- 記録した wave: branch `dev-wave-gen-opt-roadmap-revision` (基準 main `1887f56e4`)。

## 1. 収録物

| file | 原本 (repo 外) | 原本の更新時刻 (JST) | byte 数 | sha256 (写し = 原本) |
|---|---|---|---|---|
| `user-verbatim.txt` | `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/user-verbatim.txt` | 2026-09-29 09:31:49 | 1165 | `74fa8aab89da43ed7f1de37cfd3cd3b010186716b232a6c4be3c8c36e7a8e512` |
| `proposal.md` | `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/proposal.md` | 2026-09-29 09:31:49 | 6466 | `a618c650008daf762b92a109baafed9a1ff7e9852a0a9ff770e621b6d7fcb951` |

- 出所: 2 file とも、ユーザーと相談した親セッション (セッション名 "gen opt") が作成し、並行 wave の指示 (同 dir の `common.txt`、`md_1.txt`〜`md_4.txt`) とともに置いたもの。
  原本の更新時刻は上表のとおりで、写しは本 wave が 2026-09-29 に取得した。
- 写しは `cp` による bytes 一致で、上表の sha256 を写しと原本の両方で計算して一致を確かめた。
- `user-verbatim.txt` のユーザー発話 [1] [2] の時刻は親セッションの記録どおり「09:1x 頃」「09:3x 頃」で、分単位の時刻は記録に無い。
- `user-verbatim.txt` は、ユーザーの発話 (逐語) と親の解釈 (ユーザーの明示確認なし) を分けて書いている。
  特に提案末尾の (b) 優先度には明示の回答が無く、親が推奨どおりと解釈した。決定台帳もこの区別を保つ。
- `proposal.md` は親セッションの回答であり、ユーザーが同意したのはその (a) (roadmap の「(c) ゼロから書かせない」「(b2) は後回し」を、
  編集範囲と正しさ関門を維持したまま改める) である。本文中の数値 (1 候補の評価の所要、差 1.06% と揺れの床 3% など) と
  文献の既知判定は親セッションの記述の写しであり、本 wave は照合していない。

## 2. 何を確かめ、何を確かめていないか

- 確かめた: 写しと原本の bytes 一致 (sha256)、原本の byte 数と更新時刻。
- 確かめていない: `proposal.md` の数値と先行研究の記述の正しさ (親セッションの記述をそのまま写した)。roadmap には、
  既存の決定台帳 (D2212・D2282) に根拠のある事実だけを書き、その他の数値は持ち込んでいない。
