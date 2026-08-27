# 段 1 brief — dev-wave-t1721-noncertifying-a1

repo root (worktree) = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1`
base = local main `dd66213978d3d30eed567484ec013216bff6926b`

## scope

[T-1721] + [T-1818] を D1028 に従い **1 変更単位**で作る。

1. **非認証成果物型の確定** — 批准 authority を持たない成果物型を、環境契約と live source
   束縛を保ったまま定義する。着手条件 (D1038) = **認証済み consumer へ昇格できないことを
   鍵・記録・schema・consumer の全層で固定できること**。field の除去や付け替えで昇格できる
   作りしか取れないなら **作らずに停止して報告する**。
2. **A-1 投入器の実装** — F634 が名指しした欠落。`tools/pegasus/paper_story_a1_paired.sh`
   を直接 qsub し、その後 create-only で acquisition receipt
   (`paper-story-a1-paired-submission/v1`) を書く親側の実行器を作る。

## 確定済みユーザー裁定 (逐語の出所 = docs/decisions.md)

- **D1028** — 型の確定と投入器を同じ変更単位で行う。投入器のみ先行は不採用。D905 着地待ちも不採用。
- **D1038** — 非認証成果物型を新設する。着手条件は上記の全層固定。取れないなら作らない。
- **D1027** — 現行 A-1 は凍結どおり走らせる。論文採用 estimand は別 study。**差し替えない。**
  この wave が開けるのは現行 A-1 の投入経路であって estimand の変更ではない。
- **D1070** — 批准検査を artifact 受入と dispatch へ広げる。ただし
  **D1028 の非認証成果物型は対象に含めない。** 本 wave が作る型はこの除外の受け皿である。
- **D526** — 批准台帳への追記経路は AI に閉じている。解除は人間手番。

## 実測した前提 (brief 前の測定。すべて base dd66213 で観測)

| # | 測ったこと | 結果 |
|---|---|---|
| M1 | 投入器の実在 (F634 の再検査) | `tools/pegasus/submit_*.sh` は 8 本あるが A-1 用は **0 本**。`SUBMISSION_SCHEMA` を **書く**実装は tracked file に 0 件 (定義・検証・test fixture のみ)。F634 は現在も成立 |
| M2 | 批准 gate の実発火点 | `orchestrator/campaign/ident.py` の `_capture_current_loader_binding` が `contract_loader_binding.verify_ratified_contract_loader_binding` を**無条件**で呼ぶ。呼び手は production では**ここ 1 箇所だけ** |
| M3 | gate の現行挙動 | probe 実走で `ContractLoaderBindingError: enforcement-source-ratification: enforcement-source-closure-unratified: closure digest is absent from the read-only ledger`。`capture` と `verify_live` は OK、落ちるのは批准検査だけ |
| M4 | 閉包の構成 | `CONTRACT_LOADER_RELATIVE_PATHS` = **25 path**。`ident.py` **含む**、`pipeline.py` **含む**、`paper_story_a1_paired.py` **含まない**、`layout.py` **含まない** |
| M5 | gate 入力の実在 (DW-O13) | **`declared_use_class` は `CampaignConfig` に無い。** `pipeline.py` の引数と `layout.py` の出力 root 選択にしか存在せず、campaign 同一性 hash に入らない。すなわち **現状の use class は昇格不能性の根拠にできない** |
| M6 | test の gate 迂回路 | `orchestrator/tests/conftest.py` の `ratified_enforcement_source` は autouse でない opt-in fixture。合成 repo の台帳を `monkeypatch.setattr(ratification, "_REPO_ROOT", repo)` で差す |
| M7 | 重複検査 | 下記「編集面と非接触境界」 |

**裁定要約と食い違った点 (F31 に従い本文優先):** `docs/failures.md` の 2026-08-26 再発記録は
観測例外を `ratification history is not a strict prefix extension` (F600) と書いているが、
base dd66213 での実測は `enforcement-source-closure-unratified` である。**塞がれている事実は
不変だが、落ちる層が違う。** 段 2 以降は実測側を使う。

## 編集面と非接触境界 (実アンカー)

**編集してよい面 (稼働 wave と 1 file も重ならないことを全 branch で実測済み):**

| path | 何をするか |
|---|---|
| `orchestrator/campaign/ident.py:233` `_capture_current_loader_binding` | 批准検査の適用可否をここで決める。閉包メンバー |
| `orchestrator/campaign/model.py:67` `CampaignConfig` | 型の宣言を同一性入力へ入れる (M5 の穴を塞ぐ) |
| `orchestrator/campaign/pipeline.py` | COMMIT と certification の経路。閉包メンバー |
| `orchestrator/campaign/paper_story_a1_paired.py:70` `SUBMISSION_SCHEMA` 周辺 | 投入器が書く receipt の producer 側 |
| `tools/pegasus/` (新規 submit script) | 投入器本体 |
| `orchestrator/tests/` の対応 test | |

**触ってはならない面 (稼働中 `dev-wave-t1629-ratification-broker` の所有):**

`orchestrator/campaign/artifact_admission.py` / `campaign_lock.py` / `contract_loader_binding.py` /
`ed25519_verify.py` / `enforcement_source_ratification_receipt.py` / `tools/ratification_broker.py` /
`orchestrator/tests/test_artifact_admission.py` / `test_ratification_broker.py` /
`test_enforcement_source_ratification_receipt.py`

## 不変条件

1. **正しさゲートを緩めない (規律 2)。** 本 wave は受理集合を**広げる**方向の変更である。
   広げてよいのは「非認証と宣言した成果物が批准 gate を通らずに走れる」ことだけで、
   **certified 成果物の受理条件は 1 つも緩めない。** 変異事前登録に過剰許容の正例を必ず含める。
2. **昇格経路を 1 本も残さない (D1038)。** 非認証成果物が後から certified の証拠として
   再解釈される経路が 1 本でもあるなら、型を作らず停止する。
3. **新規 module を enforcement source closure へ足さない。** (P1)
4. **閉包の membership と件数を変えない。** 25 path のまま。`ident.py` の bytes は変わるが
   path 集合は不変。件数を変えると `artifact_admission.py` 等の "25 path" 逐語 4 箇所を
   触ることになり、t1629 と衝突する。
5. **A-1 の estimand・事前登録・凍結値を 1 つも変えない (D1027)。**
6. 実装面は Codex `role=author` が書く。親は docs 本文だけ編集する。

## 親の provisional 裁定 (攻撃対象。段 3 はここを狙え)

- **(P1)** 新規 module を閉包へ足さず、判定を既存閉包 file の中で閉じる。
  → 反証されうる点: 昇格不能性を既存 file 内で固定しきれないなら、閉包を増やすしかない。
     その場合 t1629 と衝突するので本 wave は段 4 で停止すべきかもしれない。
- **(P2)** 判定の座は `ident.py` の `_capture_current_loader_binding` である。
  → 反証されうる点: 批准を通さない経路が他にもあるなら座が足りない。M2 は production の
     呼び手を 1 件と測ったが、`artifact_admission` 側の consumer 経路 (D1070) は別軸である。
- **(P3)** 型の宣言は `CampaignConfig` の同一性入力へ入れる。既存の `declared_use_class`
  (layout selector) は昇格不能性の根拠にしない。
  → 反証されうる点: 同一性入力を増やすと既存 campaign id が全部変わりうる。既存凍結成果物の
     id を壊さない形になっているかは実測が要る。
- **(P4)** 投入器は `tools/pegasus/` の submit script + receipt writer の 2 部構成とし、
  既存 8 本の `submit_*.sh` の作法に揃える。
- **(P5)** 本 wave は**実 qsub を行わない**。装置の着地までとし、A-1 の実投入は land 後の
  別作業とする。
  → 反証されうる点: 投入器が実機で動くことを確かめずに「実装した」と言えるか (DW-O16 の
     「実行環境依存の実装はレビュー通過だけで closed にしない」に抵触しうる)。

## 成果物の形

- 非認証成果物型: 型の定義 + 昇格不能性を固定する 4 層 (鍵 / 記録 / schema / consumer) の実装 + 負例 test。
- 投入器: `tools/pegasus/` の script + acquisition receipt の producer + 契約 test。
- 変異 matrix: 事前登録どおりの kill 表。過剰拒否の正例を含む。
- 記録: worklog / decisions / failures の spool fragment + insight。

## 成果物影響 (DW-G05)

- **型を作らない場合:** A-1 対測定は `enforcement-source-closure-unratified` で 1 回も起動できず、
  paper-story の A-1 系列は値が 1 つも増えない。批准 gate が着地するまで探索的計測が全部止まる。
- **投入器を作らない場合:** 型を作っても A-1 の job body は acquisition receipt を 60 秒待って
  `refuse` するので、投入は 1 回も成立しない (休眠 capability)。
- **昇格経路を残した場合:** 非認証で走った試行が後から certified 成果物の証拠として再解釈され、
  certified 選択結果と proof chain の受理集合が事実上広がる。

## 並列分割方針

編集 file 所有が素集合になる 2 単位に分ける。

- **単位 A (型):** `ident.py` / `model.py` / `pipeline.py` と対応 test。
- **単位 B (投入器):** `paper_story_a1_paired.py` / `tools/pegasus/` と対応 test。

単位 B は単位 A が決める型の宣言 field に依存するため、**A を先行**させ、所有パス限定 patch を
展開してから B を投入する。

## 受入・実測の環境

- 受入全走: `tools/dev_wave_wait.py acceptance` 経由 (親のみ)。
- codex 子は本 repo で pytest を実走できない (`run_tests.py` の実行場所判定が `qstat -Q` を
  叩き、隔離環境は socket を拒否して `rc=16`)。**テストは親が毎回実走し、赤の本文を子へ貼る。**
- A-1 の実測環境は Pegasus compute (`gen_S`, elapstim 06:00:00)。本 wave の scope 外 (P5)。
