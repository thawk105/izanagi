---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t2582-manifest-measurement-sources
seq: 3
---

## 新規

### {{F:child-stops-whole-review-on-self-invented-path}}. read-only 子が自作の推測 path の不在で検査全体を打ち切り、部分レビューが完了形で返った [手順漏れ] [テスト代表性]

- 事象: 段 3 の consult 子が、prompt 禁止節の「読めなければその旨を書いて停止する」を、
  **親が射影した必読 path ではなく自分で組み立てた推測 path** の不在に対して適用し、6 レンズ中
  3 レンズを未実施のまま終了した。総括だけは「plan をそのまま採ってよいとは判定できない」と
  完了形で書かれ、**部分レビューが完了レビューと同じ体裁で返った。** 親が本文の
  「調査を停止した」という自己申告に気づいて再投入するまで、未実施レンズは見えなかった。
- 根本原因: `AGENTS.md` の単独段 dispatch 例外が停止を求めるのは「射影対象を読めない場合」だけ
  である。これを子 prompt の禁止節へ写すときに射程が落ち、子は自分の探索失敗にまで広げて適用した。
  出力形式にレンズごとの実施/未実施欄が無く、欠落が構造的に見えなかったことも効いている。
- 恒久対応: memory `child-stop-rule-scope-projected-files-only` — 射影節の直後に
  「この停止条件は上の射影 file にだけ掛かる。自作 path が不在でも停止せず最後まで続ける」を
  1 行入れる。同 wave で再投入し全レンズが返ることを実証した。
  **`docs/dev-wave/operations.md` の `DW-O05` へ入れるのが筋だが、L1.5 層の byte 予算
  (9696 byte) に余地が無く (追記で 9943 byte)、安全記述を削って空ける形は契約が禁じている。**
  独立実例は本件 1 件で D730 の例外収容 (3 件以上) に届かないため上限は引き上げない。
  同型の予算不足は F964 でも記録されている。
- 再発検知: 子の出力を採る前に、指示したレンズの**件数**と返ってきた所見の被覆を数える。
  本文に「停止した」「未完了」の自己申告があれば、総括の完了形より本文を優先する。

## 再発

### F945

- **再発: 2026-09-14** — docs-only tip の受入で同型が 2 度出た。1 度目は 2 件
  (`git ls-files --others --exclude-standard -z` が 30 秒 TimeoutExpired、load average 87.6、
  他 wave の `run_tests` 22 本同時走行)、単独再走は 2 passed / 7.75 秒で非再現。受入再走は
  23,308 passed・赤 0 で `child-green` を得た。2 度目は land が `stale-main` になった後の
  再走で 32 件 (load 110)。既存の恒久対応どおり、timeout 拡大・fixture の stub 化・除外・
  汎用 gate の新設はしていない。**同じ tip 世代で緑と 32 件が両方出ることを実測した** —
  件数は負荷で決まり、変更には帰属しない。
