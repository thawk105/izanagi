---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-04
wave: dev-wave-t287-checkpoint-values
seq: 3
---

## 新規

### {{F:nonutf8-evidence-blob-lands-red}}. 非 UTF-8 の証跡 blob が land され local main の受入全走が赤のままになった [手順漏れ]

- 事象: [T-287] wave が段 9 直前の受入全走で 1 件の赤を観測した
  (`orchestrator/tests/test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo`、
  5392 passed / 1 failed / 19 skipped)。赤は本 wave の差分
  (`orchestrator/campaign/p3_s4_loop.py`、`orchestrator/tests/test_p3_s4_loop.py`) が到達しない
  ファイルで起きており、`DW-O18` に従って単独再走したところ**決定的に再現**した
  (1 failed / 82 passed)。フレークではない。
- 根本原因: `tools/ruleops.py inventory` が repo の全 blob を UTF-8 として読むため、
  `output/insights/2026-08-03_t361-t362-cluster-probes/evidence/.../home/home-read-write.probe.raw`
  (`file` の判定は `data`) で rc=2 になる。**この blob は本 wave の差分に 1 件も含まれず、
  取り込んだ local main 側に既に存在した。** main のチェックアウトで
  `python3 tools/ruleops.py inventory --repo .` を直接実行しても同じ rc=2 になることを実測した。
  gate 側 (`8976c14`、2026-07-29) は blob の land (`9b0f044`、2026-08-04) より**先に存在した**ので、
  当該 wave は機械 gate が赤の状態で land したことになる。
- 恒久対応: 未定 — 既存の [T-407] が択一を持つ (本 wave は重複起票しない)。
  候補は (1) `ruleops.py` の走査を binary-safe にする (証跡は生 bytes を保つのが本来)、
  (2) 証跡 blob を base64 等のテキスト表現で保存する規約にする、
  (3) `output/insights/**/evidence/**` を inventory の走査対象から外す。
  **(3) は gate の射程を縮めるので、他 2 案が不可能なときだけの最後の手段とする。**
- 再発検知: `test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo` 自体が
  検知器である。今回それが機能したが、**赤のまま land された**ため、検知と land 阻止が
  繋がっていないことが露見した。land 経路 (`tools/dev_wave_land.py`) は tested main/tip の
  SHA を受け取るだけで受入結果を検証しないため、親の自己申告に依存している。
- 混入経路: 当該 wave は「probe と login 側 controller だけ」を理由に**変異 matrix と受入全走を
  対象外と自己裁定**しており、全走を一度も回していない。証跡ファイルを 1 個足すだけの commit でも
  **repo 全体を走査する型の gate** は壊れるため、「自差分が触らないなら全走は要らない」という
  射程判断がこの型の gate と噛み合っていない。恒久対応の候補として、受入全走を省略してよい条件の
  見直しか、land 経路が受入結果を自己申告でなく検証する形かを裁定へ返す (裁定パッケージ §6)。
- 暫定運用: 本 F の赤に限り、ユーザー裁定で**既知赤 waiver W1** を新設した (条件と失効は worklog
  末尾エントリが正本)。対象 node と原因を釘付けし、他の赤が 1 件でもあれば適用せず停止する。
  [T-407] の land で自動失効する。
