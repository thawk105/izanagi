---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-helper-forwarding
seq: 1
title: [T-2901] 止まった tx を別の thread が前進・失効させる形 (HP) を小モデルに足して 6 場面 90 構成を全探索し、代行 thread 自身の参照保護が要ることを見つけ、HP は論文の対象に入れず限界として書くと決めた (コード + test + insight、branch worktree-dev-wave-vhash-helper-forwarding)
---

## 本文

- 依頼: 並行 VHash wave の md_16 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_16.txt`)。ユーザー就寝中の背景 job。一次資料 `output/insights/2026-09-29/vhash-helper-forwarding-model/README.md`、判断は {{D:vhash-helper-forwarding-out-of-scope}}。
- 段構成: 全 9 段 (md_16 が段 2・3・6 を省かないと指定)。段 3 相談 2 本、段 6 レビュー 2 本 + 焦点再レビュー 2 巡、fix 4 回 (fix1 は健全版で新しい反例を観測して停止、fix2 で規則 H11 を追加、fix3 は所要超過の是正、fix4 は恒偽の witness の是正)。判断相談 2 本 (判断役・攻撃役)。
- 実装 commit: e5a825d57 (統合)、51937a301 (fix1〜fix3 の統合)、25a8d957d (fix4、実装 anchor)。
- 素材: 代行 thread が止まった tx の既読版を snapshot して作業している間に tx が再開して終わり参照を外すと、GC が回収した版に代行 thread が触れる。代行 thread 自身も既読版を保護しなければならない (H11)。モデルの接触判定を代行 thread にも広げた段 6 の fix で、健全版に反例が出て見つかった。
- 素材: 世代つき CAS の世代比較だけを外す版 (UH1g) は、単一 WAIT の 6 場面すべてで故障が結果を変える step が 1 度も無く反例なし。待機中の条件が世代の代わりになる。公開の CAS を世代で覆う規則は、再開した tx が未公開の前進を取り消せる実装でだけ効く (UH1p は取消しありでだけ反例)。
- 判断: HP は VHash 論文の対象に入れず限界として書く。CCBench の Cicada の長い tx は `clock_delay` の busy-wait (thread は走り続ける) で SP で扱える、Cicada の GC は全 thread の `GCFlag` がそろわないと `MinRts` を更新せず止まった thread の代理宣言は未検査、実装の費用が大きい。判断役は「本文は SP、HP は設計候補として付録」、攻撃役は「限界として書く」を推し、親が後者に決めた (付録に置くかは論文ストーリーの次の版が決める)。
- 棄却・訂正: 段 1 brief の「段階 B だけでは 1 版も回収が進まない」は言い過ぎ (段 3 レンズ B) → 「次の `MinRts` 更新に反映されない」。段 1 の代理静止宣言の候補規則 (前進の公開成功で代わりに宣言してよい) は段 3 で撤回。段 6 の F4 (H3 の窓の順序指定) は親の過剰で、場面固有の履歴 field を招き test 所要を 42 秒に膨らませた → 状態の述語に戻した。
- 新 test file の関数所要の合計は計算ノードで 13.29 秒 (目安 10 秒を超過)。H3 の健全版の完全探索 (約 4.9 秒) が段 6 の F5・F11 の要求で残るため、DW-G05 により追加の fix はしない。
- 回帰: md_4 の 63 構成と md_10 の 60 構成は、統合・fix2・fix 統合・fix4 の各時点で diffs=0 (照合器は変更前の木でも diffs=0)。
- 変異: MH1〜MH8 を login 自走で 8/8 KILLED (baseline 緑)、計算ノード本走 (束ね経路 1 job) も 8/8 事前登録どおり KILLED (MISMATCH 0。1 回目は待ち行列 900 秒で子を起動せず、`--queue-wait-timeout 10800` で再投入)。
- 受入: 焦点走 (計算ノード、新旧 vhash test 3 file と在庫・収集・campaign 系 6 file) は fix4 後で 698 passed・3 skipped。受入全走はこの記録 commit の tip で行い、受領証は job dir (`/work/1/SFC/tanab/tmp/vhash-helper-forwarding-2026-09-29/`) に残す (受入後にこの fragment を書き足すと受入のやり直しになるため、結果は書き足さない)。
- 異常と救出: 背景 job の最初の `EnterWorktree(name)` が「Could not read the repository git config」で失敗 → 手動 `git worktree add -b` が checkout 完了後に `Could not reset index file to revision 'HEAD'` rc=128 で失敗し、dir は消えて branch だけが残った → 既存 branch を指定して add し直して回復 (同時刻に 16 本の撤去で Lustre が詰まっていた)。16:2x〜16:3x に land 調整役からユーザーの push のための git 書き込み一時停止を受け、再開まで commit・branch 作成を止めた。

## 次の一手差分

### 完了

- [T-2901] HP (代行による前進・失効) を小モデルに足して 6 場面 90 構成を全探索し (健全版 30 構成は違反なし、危ない版 9 種の反例と反例なしの理由を一次資料に記録)、代行 thread 自身の参照保護 (H11) が要ることを見つけ、HP は論文の対象に入れず限界として書くと決めた ({{D:vhash-helper-forwarding-out-of-scope}})。再審するときの C++ 規則は一次資料 §8。
  remaining: none
  base: e93e535b17ef6a40d89fc1d3965b38c163a270a4f1a0b4b7d2b6bf4fff1306c7

### 新規

- {{T:vhash-story-hp-limitation}} **P3・新規**: 論文ストーリーの次の版で、止まった thread への代行による前進を「限界」として書く。文案は `output/insights/2026-09-29/vhash-helper-forwarding-model/README.md` §7.3、必要条件の表は同 §8。付録に置くかをその版で決める。SP の評価には CCBench の待機ループ (`clock_delay`) に要求の確認を入れた安全点が要ることも併記する。
