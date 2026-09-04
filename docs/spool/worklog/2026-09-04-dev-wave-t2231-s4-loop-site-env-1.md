---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2231-s4-loop-site-env
seq: 1
title: [T-2231]/[T-2199] 段 4 loop へ site-aware な環境契約配線を移植した — 親の前提 2 件を実測が覆し、実装は縮小した (コード + テスト + insight、branch worktree-dev-wave-t2231-s4-loop-site-env、変異 13/13 KILLED)
---

## 本文

- 移植元 `p3_s4_loop_trigger_gating.py` の site 対応配線を `p3_s4_loop.py` へ写した。新設ではない。
  計測用 env bytes を生成してよい site が無条件から `{OTHER, PEGASUS_COMPUTE}` の exact set へ縮小した。
  site=OTHER の campaign identity は不変で、PEGASUS_COMPUTE だけが `measurement_env` marker 付きの
  別 identity に分かれる。一次資料 = `output/insights/2026-09-03_t2231-s4-loop-site-env/`。

- **親 brief の前提を実測が覆した (1 件目)。** 親は「この機体が Pegasus login node なので、
  site 注入なしでは既存テストが壊れる」と書いたが誤りだった。`orchestrator/tests/conftest.py` の
  autouse fixture `_declare_default_test_site` がテスト中の hostname を無効化するため、
  `_current_site()` は機体によらず常に `OTHER` を返す。焦点 3 件と `test_p2_2_site_aware.py` 21 件の
  実走で確認した。この訂正により**公開入口へ注入引数を足す新設 seam が不要になり、実装が縮小した**。
  段 3 レンズ B が挙げた「この機体で赤になるテスト 26 件」も同じ根拠で refuted。

- **親の段 4 裁定 C3 を段 6 で訂正した (2 件目)。** 「公開 `run_campaign` seam は移植元にもある
  性質で本 wave 起因ではない」は不正確だった。base 版では `default_cfg` が契約を bind 済みで、
  異なる契約の再 bind を `ident.py:113` が拒否していた。未束縛化でその拒否が消えたので、
  base に対しては**実際の受理拡大**である。ただし `p3_s4_loop.run_campaign` へ `default_cfg()` を
  直接渡す production caller は repo 内に実在しないことを親が実測した。よって {{D:s4-loop-site-guarantee-scope}}
  に従い新 gate は足さず、保証範囲を明示して閉じた。

- **段 6 の両レビューの推奨を 1 件採らなかった。** 既存テストが期待する B4 gate の boundary 文字列
  `"base run_one_iteration"` と実装が食い違ったとき、両レンズとも「テスト側の regex を更新するのが
  最小修正」とした。`DW-S06-B` は既存テストの期待値変更を禁じ赤なら実装側が誤りとするので採らず、
  実装側の命名を移植元と同型 (公開 = 従来名、内部 = `resolved` 付き) へ変えて期待値を保った。

- **段 6 の赤 4 件の帰属を base 対照で決めた。** 1 件は未 commit の作業ツリーが原因の衛生テストで
  commit 後に緑 (欠陥ではない)。残り 3 件は base commit へ 4 file を戻すと全て緑になったので
  本変更に帰属する real な回帰と判定した。真因は gate の弱化ではなく、`drive_iteration` の
  呼び先が内部 resolved 実装へ変わった結果、公開 seam を差し替えていた既存テストの fake が
  呼出し経路から外れ実コードが走ったことだった (両レンズが独立に特定)。

- **変異は 13/13 KILLED。** 期待 node は probe 走行の実測から機械生成し、手で転記していない。
  単一理由と確認できたのは 8 件 (M5〜M8、M10〜M13) で、M1〜M4 と M9 の 5 件は複数層が同時に
  反応する過剰決定。`DW-M03` / `DW-M04` に従い単独変異の証拠から外し冗長 gate と明記する。
  段 6 レビュー B が静的に見抜いた過剰決定の判定が、実測 (M2=39 node、M4=21 node) で裏付けられた。

- **セッション異常 1 件。** 親が焦点走を `timeout 570` で包んだため、計算ノードの投入待ち中に
  自分で SIGTERM した。orphan hold が 2 file 残り次の投入を全部止めたので、hold 自身の復旧手順
  (qstat で対象不在を確認 → source の clean/HEAD を確認 → 手動削除) に従って解除した。
  待ち手を timeout で包まない規律の違反。

- **計算ノードの混雑で変異本走が 1 度止まった。** M2 で `rc=16` が出たが、job stdout が 1 byte も
  生成されておらず投入自体が受理されていなかった (並行 wave と枠を取り合う状況で izdw job が
  8 本待機・実行中ゼロ)。M2 固有ではない。キュー深さを見て空いてから `--resume` する経路へ
  切り替え、36 分待って完走した。

- **main 取込みの合成監査を Codex `role=author` が行った。** 受入が `merge-message-provenance`
  (rc=70) で止まった。両側で変更された実装面は `p3_b4_wiring_probe.py` の 1 file だけで、
  merge 結果が両親のいずれとも異なるため Codex 起草の merge message が要る。子は両 hunk が
  別関数・別実行段階で両立すること、main の 93 commit に親の裁定の前提を覆す変更が無いこと
  (親の触った 3 file は merge base と main で blob 一致) を確認した。

- **agent 工数**: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 1、merge author 1)。
  受入全走 1 回 (child-green)、変異走 probe 1 + 本走 1 (resume 2 回)。

## 次の一手差分

### 完了

- [T-2231] 段 4 loop へ site-aware な環境契約配線を移植した。受理集合は
  `{OTHER, PEGASUS_COMPUTE}` の exact set へ縮小し、OTHER の campaign identity は不変。
  変異 13/13 KILLED、受入全走 child-green。
  remaining: none
  base: a88be36b37ae0fce8380b1bd8b585f8f422b306ccb6121e678aa4f682166d843

### 更新

- [T-2199] **P1・部分完了**: 実行場所の択一は Pegasus で決着済み (D59 の 4 前提をこの job に
  ついて満たす方向)。段 4 loop 側の環境契約配線は本 wave で着地した。残るのは [T-2232] の
  Pegasus job script と、その先に出る未実測の障害 (attestation の exact 照合、reservation と
  claim root の束縛)。preprocess の `config.h` 不在は job script 側で解けるが PATH wrapper で
  解いてはならない。
  base: c83b7fbbcbab1f8a03b5853db7a2af06a07e15eedbeb47d8201cb7c79c3d9139

### 新規

- {{T:base-b4-launcher-site-projection}} **P2・新規**: base の B4 launcher へ site 射影を入れる。
  `orchestrator/campaign/p3_b4_launcher.py:165-170` は `driver_kind == "trigger"` のときだけ
  site 射影するため、PEGASUS_COMPUTE では base の campaign ID が launcher context と食い違い
  正式 B4 経路が build へ到達しない。段 6 の両レンズが独立に発見した。OTHER では ID 不変なので
  現に動いている経路の回帰ではなく、[T-2232] 着地までは到達不能。

- {{T:s4-loop-layout-match-port}} **P3・新規**: 段 4 loop へ `_assert_layout_matches_campaign` と
  `_with_campaign_location` を移植する。既存検査は `do_build=True` にしか効かず、production は
  `layout=None` なので露出は dry/test 注入だけ。compute でしか差が出ないため `DW-G02` に従い
  1 cycle 後へ送った。

- {{T:s4-loop-sort-site-aware}} **P3・新規**: `p3_s4_loop_sort.py` の site 対応。同 driver は
  依然として linux-baremetal の定数と契約を直接使う。段 4 loop と同型の移植で足りるかは未検証。
