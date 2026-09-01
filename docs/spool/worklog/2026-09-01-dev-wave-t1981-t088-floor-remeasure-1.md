---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1981-t088-floor-remeasure
seq: 1
title: [T-1981] 消費済み 12 cell を実機で測り直し、一回性撤去の終端条件を満たした (計測 + docs、branch worktree-dev-wave-t1981-t088-floor-remeasure、実装面の差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

- **[T-1981] の残件だった実機証明が取れた。** 2026-08-24 の床値 pilot が一回性 key を
  消費した 12 cell を、D1124 / D1190 の撤去が着地した local main (`2bf9cf387`) から測り直せた。
  request `964035.nqsv`、campaign run id `20260901T014044Z-2c8cf9be`、Elapse 3016S。
  合格条件は前 wave の凍結済み事前登録
  (`output/insights/2026-08-27_t1981-holdout-oneshot-removal/verbatim/s4-adjudication.md` §6-C)
  の 4 点をそのまま適用し、緩めていない。逐語・実測値・台帳の照合結果は
  `output/insights/2026-09-01_t1981-t088-consumed-cell-remeasure/README.md`。
- **依頼文と [T-088] の持ち越し本文が事実と違っていた。** 「2026-08-24 に一度走って途中で死に、
  成果物が残っていない」は誤りである。`docs/archive/worklog-phase3-0825-924.md:1` が
  「床値 pilot が初めて完走し、床値の実測値が得られた (request 945229.nqsv、12 セル 96 attempt
  すべて valid・除外 0・retry 0)」と記録しており、entry 1053 が同じ否認を既に書いていた。
  **D1124 の決定は覆らない** — 論拠「性能測定は繰り返しても何も無効化しない」は run の生死に
  依存しない。訂正されるのは成果物影響の言い方だけで、正しくは「床値が 1 つも出ない」ではなく
  **「同じ cell を測り直せない」**である。[T-088] の stub は entry 1029 から更新されないまま
  本 wave の依頼文へ伝播していた。本エントリで両項を閉じるとともにこの誤りを台帳側で断つ。
- **同じ課題を別 session が独立に立ち上げ、床値 job を 7 秒差で二重投入した。** 964035 (本 wave、
  Created 10:40:09) と 964044 (相手、Created 10:40:16)。実行ノードは bnode130 と bnode136 で別。
  相手 job には触れていない。分担を合意し、測定は両方走らせ、記録と land は本 wave が持ち、
  相手は締めの fragment を書かず自分の走行を第 2 の独立観測として渡した。D1124 により同じ cell を
  何度測ってもよいので、2 本走ること自体は正しさの問題ではない。**両方とも完走した**
  (相手も driver_rc=0 / 96 session / 除外 0、Elapse 2981S)。
- **二重投入の副産物として D1190 決定 3 の陽性証拠が取れた。** 「別世代からは同じ論理 attempt を
  消費できる」を、2 世代が同じ 12 cell を同時に保持して各 96 attempt を消費する状態として
  実機で観測した。1 本だけでは取れない観測である。
- **相手 session との相互訂正が 2 件あり、どちらも一次資料・実物で決着した。**
  (a) 相手の「`ledger.jsonl` 36 行は投入前と同じ」は誤りで、実測は 60 行だった。D1190 の理由節が
  2026-08-27 時点の 36 行を記録しており、差 24 行はちょうど今日の 2 走行分である。相手は再測して
  受け入れた。(b) 親の「世代 digest = `sha256({observation_role, campaign_run_id})`」は取り違えで、
  その式が与えるのは `measurement_generation_id` である。実装
  (`orchestrator/campaign/s8b_holdout_admission.py:785-814`) を読んで claim 24 件全件を
  数値照合し、三段導出を確定した。帰属は変わらず、insight の導出式だけを直した。
- **床値の「案」は `scalar_alt` の水準では run 間で再現しない。** 3 走行の rr80 は
  45509.145 / 48486.594 / 75975.565 と動くが、非 `p2_2_flag_opt` の pair 値は
  45509.145 / 45692.985 / 45835.665 で 0.72% 以内に収まる。承認済みの式
  `floor_pair(c) = max(u_noise(c), wired_min_rel_floor × m_stock)` のとおり、床値は通常
  3% 相対床に張り付き、最高スループット cell の noise 項がそれを超えたときだけ持ち上がる。
  機構の欠陥ではない。**繰り返し測れるようになったから初めて見えた性質**であり、
  一回性が強制されていた間は原理的に観測できなかった。床値は pilot 案で何も発効していないため
  成果物の値・受理集合・参照は変わらず、本 wave では機構を足さず観測として記録するに留めた。
- **`submit_floor.sh --dry-run` は third-party staging を飛ばす。** 新規 worktree では
  dry-run が rc=0 でも実投入は `floor third-party source root is missing or unsafe` (rc=2) で
  qsub 前に落ちる。`tools/pegasus/fetch_third_party.py hydrate` が要る (runbook §6 の既定手順で
  あって実装の欠陥ではない)。両 session が独立に同じ経路を実測した。
  **dry-run 緑を投入可能性の証拠にしない。**
- 実装面の差分はゼロで、`orchestrator/campaign/s8b_floor_campaign.py` も
  `s8b_floor_attempt_launcher.py` も編集しなかった。実機走行が編集面の欠陥を出さなかったため
  段 5 の Codex author は起動していない。`orchestrator/tests/test_s8b_floor_campaign.py` は
  稼働中の別 wave (`worktree-dev-wave-t2074-a1-estimand-realign`) が所有していたので触れていない。
- 証拠 bundle は repo 外
  (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-t088-floor-remeasure/evidence-bundle-964035/`)
  へ退避した。944 file・61,720,222 bytes、構成 manifest の sha256 は
  `bd5eb9bd489f8edbc567c75189cabf96ca188ce4fc05c448ae502ffa49cc2c27`。
- 床値は pilot の「案」であって何も発効していない (`eligible_for_refreeze=false`)。
  official 解禁 (W-1)・v2 再凍結 (W-3)・oracle 実走 (W-4/W-5) は依然として別項である。

## 次の一手差分

### 完了

- [T-1981] 消費済み 12 cell が再測定を妨げないことを実機で証明した。§6-C の合格条件 4 点を
  すべて満たし、床値の実測値も得た。台帳では 2 つの新しい測定世代が旧 12 cell と同じ座標を
  保持し、旧 namespace は 1 件も変わっていない。
  remaining: none
  base: 6c4250223a524c8918130ac4ab99b906a88be43fac59c7818bf9545caf469fac

- [T-088] 床値 pilot を投入して完走させた。持ち越し本文の「途中で死に成果物が残っていない」は
  誤りで、正しくは「完走したが同じ cell を測り直せなかった」であり、その制約が解けた。
  official 解禁と再凍結は別項として残る。
  remaining: none
  base: 7e2ea3db9134754ba0463f0fd45aa0ba48632113abd16ac02c51776a643a2d11
