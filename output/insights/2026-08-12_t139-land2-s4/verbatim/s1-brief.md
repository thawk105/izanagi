# 段 1 brief — dev-wave [T-139] land 2 session 4 (最終 session・land する)

- wave: `dev-wave-t139-manifest-land2-s4` / 2026-08-12
- branch: `worktree-dev-wave-t139-manifest-w2`、起動 tip `738eadfc` → main 取り込み後 `7467aa90`
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-land2-s4`
- job artifact: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2-s4/`
- 受入・実測環境: Pegasus。受入全走は dispatch recipe (計算ノード)。lease slug =
  `dev-wave-t139-manifest-w2`、`IZANAGI_WAVE_LEASE_DIR=/work/1/SFC/tanab/dev-wave-jobs/land-lease`

## 確定済みユーザー裁定 (authority: user、一次控え `rulings-inbox/2026-08-12-second-batch-11rulings.md`)

- **Q1 = 機構を新設しない。** 受理述語の入力欠落 4 件 (B1〜B4) を閉じる canonical decision は
  起こさない ({{D:coarse-provenance-standard}} = bytes 級 provenance の新設は既定で見送り)。
- **Q2 = 機構を新設しない。** approval manifest の新表現 (role 別 namespaced projection 等) は作らない。
- **Q4 = 本 wave の scope。** 「投入の実務経路 (`submit_pilot`・PBS driver・collector) +
  D292 を上書きする解除 decision + 束縛検査」だけを 1 session・同一 land で組む。
  **解除 decision だけを先に land しない。**
- **Q6 = (a)。** S6 (a) 維持。本 session が最終 → **land する**。
- 第 1 束: pilot / 本走の投入禁止を解除 (Q3 (b) 上書き)、追補 P の blob 凍結は実施しない。

**既決の統べる decision:** D292 (解除できるのは canonical fold された decision だけ)、
D308 (認可の解禁と束縛検査は同一 land)、D310 (発行者権威の受領証を作らない)、
D316 (生きた台帳への検査は伸びる集合を literal で固定せず fail-closed 方向だけ釘付け)。

## 段 1 の実測 (現 worktree tip `7467aa90` で測った。既存 docs を根拠にしていない)

1. **`submit_pilot` のコード実体は 0。** hit は insights の散文と、`preregistration` の docstring
   および `test_module_exports_no_admission_api` の**禁止リスト**だけ。
2. **`orchestrator/preregistration/` に `submit_pilot` を置くことは既存テストが名指しで禁じている**
   (`orchestrator/tests/test_t139_preregistration_binding.py:903-915`。`__all__` と `hasattr` の両方)。
3. **既存の T-126 族が投入経路の完成した雛形を持つ** — `orchestrator/qualification/submission.py`
   (`O_EXCL` + `fsync` + 親 dir fsync の durable intent)、`qsub_binding.py`
   (`submission_intent_sha256` ↔ `job_id` を stdout 由来で束縛、exact 8 key)、`collector.py`。
4. **`pilot_submission = "forbidden"` は直値**である —
   `orchestrator/publication/report.py:230` と `approval_d291.py:478` (型は `Literal["forbidden"]`)。
   テスト 4 箇所が pin する。**production の consumer は 0 件** (テストと自 CLI のみ)。
5. **D291 supersession scan は既に `possible_supersession`** (`D292, D305, D313, D316`)。
   新 decision が `D291` に言及しても status は変わらない (テストは fail-closed 方向だけを固定)。
6. **canonical `docs/decisions.md` は D319 まで。解除 decision も
   `{{D:coarse-provenance-standard}}` も canonical に無い** (grep 実測)。
7. **pilot の規模** = `consumed_cluster_slots` exact `[1..8]` × 36 run = **288 planned run**
   (2 workload × 6 permutation block × 3 arm)。allocation あたり直列 2400 秒
   (`record-items-v2.md` §4.8 / §6.8 / §6.9)。
8. 起動時 `spool_fold.py --dry-run` = `planned` rc=0、`check_wave_startup.py --mode resume` OK、
   全史 provenance rc=0。

## 不変条件 (緩めない)

- **規律 2:** 投入を通す gate を、入力が無いことを producer 申告値で埋めて成立させない。
  未充足前提では fail-closed で拒否する。session 3 が却下した「休眠 validator」を作らない。
- **D292 / D308:** 解除は canonical fold された decision だけが与える。解除 decision と
  投入経路と束縛検査は**同一 land**。
- **D264 維持:** `orchestrator/preregistration/` は投入 gate ではない。同 package の `__all__` に
  投入 API を 1 名も足さない (上記実測 2)。
- **Q1/Q2 の帰結:** approval manifest / resolver / `PreregBinding` / 固定 semantic validator /
  conformance vectors / 受領証 writer は**作らない**。本 wave はこれらに依存しない形で経路を組む。
- 既存 `pilot_submission = "forbidden"` の直値と型は**触らない** — D291 の fold 時点の履歴であり、
  生きた権威ではない (下記 (P3))。

## 親の provisional 裁定 (攻撃対象。段 3 で潰してよい)

- **(P1) 本 wave は pilot job を投入しない。** Q4 が名指したのは「経路 + 解除 decision + 束縛検査」で
  あって投入ではない。実際の qsub は前提充足後の別手番。
  **成果物影響:** 実装しなければ certified 選択・材料レポート・試行台帳のいずれにも値が入らない
  (pilot 実行なし) が、本 wave で投入すると未充足前提のまま 288 run 分の試行台帳が生まれる。
- **(P2) 既存 T-126 族の pattern を踏襲し、新しい機構族を作らない。** Q1/Q2 の「新設しない」は
  T-139 固有の承認機構 (manifest・受理述語の bytes 級入力) を指し、既存の実務 pattern の再利用は
  新設ではない。`submission_intent` / `qsub_binding` の形を T-139 へ写す。
  **成果物影響:** 独自形式を作ると試行台帳の identity 規約が族ごとに二重化する。
- **(P3) 解除は新しい gate が担い、D291 の deny-only report は履歴として不変にする。**
  report は「grant できない」ことが設計 (docstring `deny-only`)。生きた権威は
  「canonical decision の HEAD 実在 ∧ 前提充足」を検査する新 gate 1 本に集約する。
  **成果物影響:** 二重権威を残すと、解禁後も `forbidden` を返す孤児 report を読んだ consumer が
  誤った受理集合を得る。孤児のまま残す場合は履歴である旨を機械可読に固定する。
- **(P4) 束縛検査 = 3 本。** (i) 解除 decision が canonical `docs/decisions.md` に fold 済みで
  あることを HEAD bytes から検査 (D292 の要求。D316 に従い fail-closed 方向のみ釘付け)、
  (ii) 前提が 1 つでも未充足なら投入を拒否、(iii) 投入は `submit_pilot` 経由でしか起こせない
  (直接 qsub 経路を通る抜けを塞ぐ)。
  **成果物影響:** (i) が無いと handoff の記載で解除されうる (D292 が禁じた形)。(ii) が無いと
  未検証 gate のまま試行台帳と公表 entry が生成される (D292 の理由欄そのもの)。
- **(P5) 受領証は `record-items-v2.md` の exact 閉包を満たす形では作らない。** Q1/Q2 の直接帰結。
  collector は raw 成果物の回収と粗い run record までを担う。
  **成果物影響:** 材料レポートの proof chain が bytes 級でなく粗い provenance になる
  (= {{D:coarse-provenance-standard}} が既に認めた水準)。
- **(P6) `a12` stress check と `a09` schedule 生成の扱い。** `a12` は実装も実行結果も 0 件で
  pilot 1 本目の前提。`a09` schedule は driver が消費する。親の暫定裁定は
  「`a09` は driver が消費する以上 scope 内、`a12` は gate の拒否条件として扱い本 wave では実装しない」。
  **成果物影響:** `a12` を gate 条件にしないと、stress check 未完走のまま pilot が走りうる。

## 成果物の形

1. `submit_pilot` (投入経路。`preregistration` 以外の場所)、durable submission intent、qsub binding
2. PBS driver (計算ノード側の実行体) と collector (回収)
3. **解除 decision の spool fragment** (`docs/spool/decisions/`) — D292 を上書きし、
   解除の範囲を「`submit_pilot` 経由の pilot に限る」と定める
4. 束縛検査 3 本 (P4) と、その負例を含むテスト
5. worklog / failures fragment、insights (逐語 + 変異台帳)、裁定パッケージ (残る設計択一があれば)

## 並列分割方針

- 段 2 プラン起草 1 本 (codex read-only)、段 3 敵対相談 2 レンズ (sol → luna)。
  **軽量版は採らない** — 正しさ防壁 (投入禁止) に触れ受理集合を変えるため (`DW-C00`)。
- 段 5 実装は所有を分離して 2 lane を上限: lane A = 投入経路 (`submit_pilot` + intent + binding)、
  lane B = driver + collector。docs (解除 decision fragment) は親が書く。
- 段 6 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走 (記録 commit 込みの最終 tip)。
