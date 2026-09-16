# 段 1 brief — [T-1907] 旧 backoff consumer の v1 patch 別名凍結

- 研究前進: 土台。s1/s8b 凍結 3 file が pin する旧 static-backoff sweep 3 WAL (論文材料) を生んだ式 v1 の patch bytes を、git 履歴を掘らずに repo 内の固定 path で参照・再適用できるようにする。止めている研究の実測: 無し (下の P3 実測で再走による pin 破壊経路は既に閉じている)。完了判定 = 別名 file の sha256 が v1 と一致、現行 patch・凍結 3 file・3 WAL が無変更、受入 child-green。
- scope: `patches/` へ v1 patch の bytes を別名で 1 file 追加し、`patches/README.md` に由来 (commit / blob / sha256) と用途を記す。以上。
- 確定済み裁定: D1098 (ユーザー裁定 2026-08-27) 旧版を別名で凍結し既存凍結成果物は 1 byte も動かさない。D1281 (2026-08-29) 移行でなく v1 patch の別名凍結。依頼逐語 (2026-09-16): 「8 件の WAL SHA pin を張り替える移行案は採らない」「対象は既存 v1 の保存に限定する」「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」「規律 2 を緩めない」「実装面は Codex author (D95)」。
- 不変条件: (I1) `patches/silo-backoff-fixed.patch` (v3、sha256 a5e0710c…580a) を 1 byte も変えない — B-10 事前登録・paper story A1 等 15 file が pin、T-2647 もこれを消費。(I2) `output/s1-freeze/{measurement,known_axes}_freeze.json`・`output/s8b-freeze/holdout_freeze.json`・`output/campaigns/backoff-sweep-silo-{balanced-sweep-484c663e,write-heavy-sweep-493813a7,read-heavy-sweep-610004b9}/` を変えない。(I3) 既存テストの期待値・consumer の配線を変えない。(I4) verifier / grammar / condition gate の受理集合を変えない (規律 2)。(I5) 新しい pin テスト・gate・`patches/ledger.json` entry を足さない。
- 成果物の形: 新規 1 file (Codex author が `git show <blob>` の bytes をそのまま書く) + README 節 (親) + insight + spool fragment。
- 分割方針: 実装単位は 1 (素集合不要)。段 2 plan 1 本、段 3 敵対 2 レンズ (設計択一が割れうるため)。
- 受入・実測環境: Pegasus login node の worktree。受入は `tools/dev_wave_wait.py acceptance` (所在 = worklog 1549 の受入形)。
- 実測済み事実 (親、2026-09-16):
  - F1 patch 履歴: 式 v1 の blob は 476a128 (06-22) / 24c8373 (06-29) / 90e83b5 (06-30) / f7a5444 (07-02〜08-26、= `4dfd3785b^`)。v2 = 06d272b (08-26)、v3 = eb319d8 (09-07、HEAD)。hole 式行は v1 4 版で同一。
  - F2 旧 3 WAL は 2026-06-22 cygnus、ccbench 6656e93 で生成。f7a5444 が前提とする元 blob (Options.cmake b9a3c74 / backoff.hh 3db8c08) は 6656e93 と現行 pin 511c953 の双方で一致。
  - F3 v1 系 4 blob の sha256 を pin する箇所は repo 全体 (archive 含む) で 0 件。
  - F4 `patches/*.patch` を glob で走査するのは `orchestrator/tests/test_ccbench_spawn_sites.py:632` と `orchestrator/tests/test_p3_s4_loop.py:7842` (path 検索で確認。key 検索は未了)。
  - F5 T-2647 との重複: 全 128 worktree を committed / dirty / untracked で照合し、`patches/` と凍結 3 file に触れるものは 0 本。backoff 消費側の他 file に触れる 20 本は本 scope の編集面と素集合。
- (P1) 凍結 bytes は f7a5444 (sha256 35237d31…f911、式 v2 に置き換わる直前の v1)。代替は WAL 生成時点の 476a128。親の provisional 裁定・攻撃対象。
- (P2) 別名 path は `patches/silo-backoff-fixed-v1.patch` (patches 直下、既存命名に倣う)。F4 の在庫検査に入ることの是非を含め攻撃対象。
- (P3) 旧 consumer を v1 へ配線し直さない。実測: 現行 `backoff_sweep.config_for` + admission policy bind の campaign id は 3 workload とも旧 3 campaign と不一致 (2899b6a7 / 172b45ad / 57160b6c vs 484c663e / 493813a7 / 610004b9)。旧 hash は旧 lock から再計算で一致。現行 identity は build_admission を必須とする (a21bf413e, 2026-08-03)。起票時の「再走で同じ campaign に別 ID が積まれる」はこの経路では起きない。D1098「旧消費者はそのまま動き」との整合を攻撃対象にする。
- (P4) `patches/README.md` の「旧 campaign へ resume してはならない (同じ campaign に別 ID が積まれる)」は P3 実測と食い違うので、凍結節の追記と同時に実測事実を併記する (警告自体は消さない)。攻撃対象。
- DW-G05: 放置時、式 v1 の bytes は git blob としてのみ存在し repo path から参照できない。certified 選択・台帳の値と受理集合は凍結の有無で変わらない。
