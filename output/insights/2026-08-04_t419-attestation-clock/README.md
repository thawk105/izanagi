# [T-419] 実行時 attestation の effective_clock — 逐語と一次資料

wave branch `worktree-wave-t419-attestation-clock`。ユーザー裁定 (2026-08-04、一次控え =
`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-03-task-def-rulings.md` §4) を受けた
封じ込め wave の逐語。

## 何が分かったか (要旨)

`/proc/cpuinfo` の `cpu MHz` を読む attestation probe は、**読み取っているプロセス自身が
走っているコアが turbo にいる**ため、必ず 1 個以上の帯外サンプルを生む。
これは較正 (expected) 側にも実行時 (observed) 側にも同じように乗る。

- **23 の相異なる観測すべてが 2% 帯外要素を 1〜2 個持つ** (`output/` 配下の JSON 成果物由来 21 +
  実行時 observed 列 2)。重複排除後の数である — 登録済み較正の標本列は attempt の複製と
  実行時 message 内の expected 列を合わせて 4 箇所に現れるため、出現回数 24 のうち相異なるのは 23。
  実行時 2 脚の帯外位置は index 34 と 27 で互いに異なり、登録済み較正の index 40 とも異なる。
  位置が毎回変わることは「特定コアの個体差」仮説を弱める。
- ログインノードで `/proc/cpuinfo` と `/proc/self/stat` の processor field を同時に採ると、
  6 回中 6 回、**自分が走っている CPU が帯外側に現れた**。ただし計算ノードの成果物は
  probe の走行 CPU を保存していないため、**計算ノードでの因果は未立証**である (段 3 レンズ A の反証)。

したがってユーザー裁定の期待効果「較正を取り直せば Pegasus の campaign が開く」は、
**現行の probe と config では達成されない**。取り直した較正も同じ観測者効果を焼き込み、
かつ observed 側も毎回帯外要素を出すためである。

## この wave がしたこと

- **した:** 取得時 (CLI publish 経路) の自己整合 gate、registry 全走査の不変条件、
  canonical 述語の golden vector。**受理集合は狭める方向にしか動かない。**
- **していない:** probe の是正、較正の再取得、凍結 bytes と pin の更新。
  **Pegasus の campaign は開いていない。**

## ファイル

| ファイル | 中身 |
|---|---|
| `brief.md` | 段 1 brief と前提実測 |
| `s2-plan.md` | 段 2 プラン起草 (codex, read-only) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対相談 2 レンズ |
| `s4-adjudication.md` | 段 4 裁定 (real/refuted、plan v2、変異事前登録) |
| `s5-impl.md` | 段 5 実装子の報告 |
| `s6-revA.md` / `s6-revB.md` | 段 6 敵対レビュー 2 本 |
| `s6-fix.md` / `s6-fix2.md` | 段 6 fix 2 巡 |
| `s6-refocus.md` / `s6-refocus2.md` | 段 6 焦点再レビュー 2 巡 (1 巡目 NO-GO → 2 巡目 GO) |
| `mutation-spec.json` | 変異事前登録 (実行結果は worklog) |

`s2`〜`s6` は codex worker の出力そのままである (逐語)。親の裁定は `s4-adjudication.md` が正本。
