# 依頼の逐語 (2026-09-21、`/dev-wave` の引数)

1 wave あたりの焦点走 (計算ノード) の本数と各 wall (queue / RUN / collection) を直近 landed wave 12 本の dispatch job log
  から集計し、DW-O26 (inventory 4 群) と DW-S05 / DW-M07 が契約で要求する回数 (fix 前・fix 後・main 取り込み後・単独走) と照合する
  (診断のみ、着手直前の local main から fresh worktree)。実測例 = [T-2803] 7 本、[T-2344] 4 本。契約外に増えた本数とその理由 (fix
  巡ごとの再走、merge 後の再走) を分け、契約を変えずに減らせる分 (同一 tip での重複、単独走と inventory 群の同 job 化)
  を効果見積り付きで裁定パッケージにする。焦点走を login へ移す案は D289 / rc=16 の設計どおり採らない。受理集合・inventory 4
  群・変異の完全一致要件は変えない。規律 2 を緩めない。診断だけ。gate・台帳・一般化の追加は scope 外。
