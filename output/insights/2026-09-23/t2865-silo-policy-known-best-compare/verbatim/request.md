/dev-wave [T-2865] silo-function-policy 軸の小比較を 1 回走らせる (第 33 回 裁定 7 = 択 (b)、控え
  /work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-09-23-rulings-full33-verdicts.md。台帳への記録は稼働中の rulings-all-20260923b
  が担当)。着手直前の local main から fresh worktree。段階 D (insight output/insights/2026-09-23/t2863-silo-policy-stage-d/README.md、D2234)
  と同じ 8 job 構成・同じ偵察 driver・tools/pegasus/dispatch_compute.py --task generic の経路で、既知最良の参照 (元の適用方法の調整済み静的
  backoff・B0-L-W0・stock) を同じ job に置き、IR 候補がそれらを超えるかを測る。段階 E へ進むかの判断材料を insight にまとめて返す (段階 E
  の実装と .claude/agents/ の変更は scope 外、D2214 により別途ユーザー明示承認)。計算は投入前に job Elapse の実測単価 (段階 D 初走 1 本
  428〜564 秒) で見積もり、2 node 時間以上ならユーザー確認 (D2212 項 4)。比較の点 ID・比は後段の coder・planner へ渡さない
  (docs/axis-onboarding.md §3-D の firewall)。規律 2 を緩めない。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
  - 事実の訂正: 2 巡目で codex は「T-2865 は現在ユーザー裁定待ち」と書きました。私の判断は裁定済みです。第 33 回の控えで、択 (b) が authority
    user として受領されていることを確認しました。codex の順位 (1 位) はそのまま採っています。

(peer 補足、2026-09-23 20:5x JST、rulings collection protocol review session より。新裁定ではない)
見積りには焦点走・開発検査の費用も入れて 2 node 時間の線と比べる (D2219 項 1 / D2212 項 4)。
