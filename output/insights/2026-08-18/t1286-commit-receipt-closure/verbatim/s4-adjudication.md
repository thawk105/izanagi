# 段 4 裁定 + plan v2 — wave t1286-commit-receipt

親 (Claude) / 2026-08-18 14:40 JST / base main a160f4aa (main は 221ec6da まで進行、docs のみ)

段 3 は 2 レンズとも NO-GO。以下、所見ごとに real/refuted と採否を裁定する。

## 0. 裁定 inbox 再走査 (DW-S04)

`rulings-inbox/` の最新は `2026-08-18-rulings-full7-15rulings.md` (12:06)。
[T-1286] / [T-1287] / [T-762] / [T-1252] への言及なし。wave 開始後の裁定更新はない。

## 1. 所見の裁定

| # | 分類 (親) | 採否 | 理由 |
|---|---|---|---|
| A-1 批准台帳の自己批准 | **部分 refuted** | 一部採用 | 下記 §2 |
| A-2 closure 20 から receipt 実装面が漏れる | real | 採用 | closure は「批准対象が enforcement の実体を覆う」ことが目的。receipt issuer/検証面が外なら目的を達しない |
| A-3 receipt が verifier 発行でない | real (plausible → real へ格上げ) | 採用 | `res.certified` を入力にすれば規律 2 の reward hacking をそのまま通す。issuer は verifier entrypoint 内 |
| A-4 layout 横断の single-use 破れ | real | **scope 外 → 裁定へ返す** | 下記 §3 |
| A-5 負対照は production sink を直接駆動せよ | real | 採用 | producer 経由だけの負対照は恒真 |
| A-6 serial-2 fixture は経由化の負対照にならない | real | 採用 | serial-1 + calibration 破損の fixture を新規作成 |
| A-7 current/prefix の二重 wrapper | real (plausible → real) | 採用 | head wrapper を prefix へ流用すると正当な旧 lock を誤拒否する。実コードで確認済み |
| A-8 `guided.py` は `cmd_evaluate` で無防備 | real | 採用 | **親 brief の「上流 assertion が守る」を撤回する** |
| A-9 変異事前登録の不在と帰属不成立 | real | 採用 | §5 で事前登録 |
| A-10 lock は 32 件・v2 witness 0 | real | 採用 | 親の「30 件」を「WAL 付き live 30 / lock のみ凍結 2 / 計 32、全 v1」へ訂正 |
| A-11 同一 WAL 内の再消費 | refuted | — | flock 内走査で閉じる。設計維持 |
| A-12 S8C exact 3 の導出 | refuted | — | plan の 3 module を採る |
| B-1 producer 5 件 | refuted (独立導出で一致) | — | 5 件で確定 |
| B-2 certified report/read 層が receipt を再検証しない | real | **scope 外 → 裁定へ返す** | 裁定は producer 面。consumer 面は別問題 (§3) |
| B-3 qualification schema/replay 閉包 | real | 採用 | 「全 producer」に qualification 2 件が入る以上、schema 更新は同 land 必須 |
| B-4 receiptless test helper の未列挙 | real | 採用 | legacy raw writer と新 helper を明示分離。bypass flag は作らない |
| B-5 14-key fixture/golden は独立に存在 | real | 採用 | **親の「pin は 2 本」を撤回**。closure 専用 fixture だけを 20 へ、無関係な `14` は触らない |
| B-6 consumer census 12 file | refuted (一致) | — | plan の列挙を採る |
| B-7 判定器 exact 3 | refuted | — | A-12 と同じ |
| B-8 段 5 は test file で重なる | real | 採用 | §4 の所有割当で解消 |
| B-9 順序 762→1286→1287→1252 は必須でない | real | 採用 | 親 (P5) を撤回。plan の「批准は全 enforcement bytes 確定後」を採る |
| B-10 既存 AST assertion を変えるな | refuted (= 採用すべき助言) | 採用 | `len==2` / `len==4` は維持し、全数 census は別テストで新設 |
| B-11 T-396 と closure pin で実衝突 | **real** | 採用 | §6。**親 brief の「重複なし」を撤回する** |

## 2. A-1 の裁定 — 部分 refuted、ただし主張を弱める

レンズ A は「repo 内 JSONL 台帳は弱化した本人が同じ commit で批准行を足せるので自己批准を防げない。
D287 / D414 が repo 内 JSON を authority と認めていない」とし、
「用意できなければ T-1287 の機械保証を land せずユーザー裁定へ戻せ」と勧告した。

**親の独立判定: 脅威モデルを取り違えている。**

規律 2 が名指しする reward hacking の主体は、最適化圧力を受ける **AI 実装者**である。
親は実測した — `hooks/` 配下への書き込みは Write/Edit でも Bash リダイレクトでも
**機械的に拒否される** (`guard_bash` が `hooks` を防護ツリーに含む。
`echo test > hooks/_probe.txt` が実際に拒否されることを確認済み)。
したがって台帳を `hooks/` 下に置けば、**AI 主体による自己批准は機械で塞がる**。

残る真実 (採用する制限):

- これは hook 側の障壁であって暗号学的証明ではない。git を直接叩ける人間は追記できる。
- よって本 wave は「人間が批准したことの証明」を**謳ってはならない**。
  謳えるのは「AI 実装者が追記できない集合との比較」だけである。
- D287 / D414 が却下したのは「同一主体が書ける承認 JSON を**人間承認の authority** と見なすこと」。
  ここで必要な性質は「**AI が書けない**」であり、より弱く、実測で成立している。

**裁定: T-1287 の比較機構を land する。** 台帳は `hooks/` 下、初期状態は 0 行 =
新 v2 lock 生成は fail-closed。外部 trust root と署名の要否は裁定パッケージへ返す (§3)。
land する文書・コメントに「人間が批准したことの機械的証明」と書かない。

## 3. scope 外として裁定パッケージへ返すもの

1. **A-4 layout 横断の一回限り。** 同じ lock bytes を 2 つの layout root へ置けば、
   各 WAL の消費済み集合は空なので同じ receipt が各 1 回通る。外部状態を持たない限り
   「全 layout 横断で一回限り」は証明できない。裁定文の「一回限り」を
   **(a) ledger 単位**と読むか **(b) 全 layout 横断**と読むかで必要な機構が変わる。
   本 wave は (a) を実装し、(b) の要否を返す。
2. **B-2 consumer 面。** `s1_report.py` / `tools/plotting/plot_backoff.py` / `p2_2_report.py` /
   `backoff_repro.py` は `STAGE_COMMIT` の存在だけで sample を採る。裁定は producer 面を
   名指しており、consumer 面の receipt 再検証は別裁定。
3. **A-1 残余。** 外部 trust root / 署名の新設要否。
4. **luna の裁定パッケージ候補 4 件** (歴史 raw の型分離、qualification identity root の閉包収載、
   将来 `s8c_result_judge.py` の scope、hooks 文書の「唯一経路」記述の訂正) をそのまま返す。

## 4. plan v2 — 段 5 の所有 (素集合)

### 単位 A — activation wrapper (T-762)

- 所有: `orchestrator/campaign/env_contract.py`、`orchestrator/campaign/ident.py`、
  `orchestrator/tests/test_env_contract_activation.py`、新規 `orchestrator/tests/test_t762_ident_wrapper.py`
- `env_contract` に 2 つの verified wrapper を公開する。
  - current: `_load_authority_snapshot` の 4 検査を保持した head 検証 (`ident.py:294` 側)
  - historical-prefix: `(activation_serial, activation_state_sha256)` を取り、
    同じ 4 検査を prefix へ適用する (`ident.py:303-314` 側)
- `ident.py` は `env_contract_activation` を直接 import しない。AST テストで固定する。
  **AST テストだけを完了根拠にしない** — serial-1 で catalog/hash は整合するが calibration blob が
  壊れた fixture を作り、「現行 direct は通る / 新 wrapper は拒否」を runtime で固定する (A-6)。
- 正例 3 本: current serial-2 正常、recorded serial-1 正常、旧 v2 lock の prefix 検証が通る (A-7)。

### 単位 B — COMMIT receipt (T-1286)

- 所有: `orchestrator/verifier/` の issuer 面、`orchestrator/campaign/wal.py`、
  `orchestrator/campaign/pipeline.py`、`orchestrator/campaign/guided.py`、
  `orchestrator/campaign/replay.py`、`orchestrator/qualification/artifacts.py`、
  `orchestrator/qualification/t126_driver.py`、
  `orchestrator/qualification/t126_evaluation_event_schema.json`、
  `orchestrator/tests/test_campaign.py`、`orchestrator/tests/test_guided.py`、
  `orchestrator/tests/test_t674_qualification_contract_lanes.py`、新規 receipt test/support
- issuer は **verifier entrypoint の内側**に置く (A-3)。`res.certified` を入力にしない。
  receipt は PID / process seal 付きの capability object を返し、
  `wal.append` と qualification sink は直列化 dict だけでは受理しない。
- chokepoint は 2 つ: `wal.append` (flock 内、write 前) と `QualificationEventSink.emit`。
  `_append_records_locked` は `STAGE_ABORT` 以外を明示拒否する (恒真 assert でなく runtime gate)。
- 一回限りは **ledger 単位** (A-4 の (a))。同 ledger 内は flock 下走査で閉じる。
- `guided._log_eval` は bare `GenomeResult.certified` を authority にしない。
  `cmd_evaluate` 経路にも source proof 検査を置く (A-8)。
- 既存 AST assertion (`len==2` / `len==4`) は**変えない**。全数 census は別テストで新設 (B-10)。
- 既存 receiptless test fixture は legacy raw writer と新 helper に明示分離する。
  production に bypass flag を作らない (B-4)。

### 単位 C — 批准比較 + closure (T-1287 / T-1252)

- 所有: `orchestrator/campaign/campaign_lock.py`、`orchestrator/campaign/contract_loader_binding.py`、
  `orchestrator/campaign/artifact_admission.py`、
  新規 `orchestrator/campaign/enforcement_source_ratification.py`、
  `hooks/` 下の台帳 file (**親も AI 実装子も書けない。0 行のまま land する**)、
  `orchestrator/tests/test_t671_source_binding.py`、closure 専用 fixture (`test_artifact_admission.py` の
  closure 部分のみ)
- 比較は `ident.py:248-258` の capture / live verify 直後、lock encode 前。
  ただし `ident.py` は単位 A の所有なので、**単位 C は `ident.py` を編集しない** —
  比較関数を新 module に置き、単位 A が呼び出し 1 行を入れる (B-8 の解消)。
- closure は現行 14 + S8C 判定器 3 + 批准比較の自己保護 + **単位 B の receipt 実装面** (A-2)。
  exact 集合は単位 C が実装時に再導出し、親が段 6 で照合する。
- closure 専用 fixture だけを更新し、無関係な `14` (`approval_d291.py`、
  `test_s8c_preregistration_predicates.py`) は触らない (B-5)。

## 5. 変異事前登録 (DW-M01)

各変異は「無効化時に赤になる専用 nodeid が 1 本」であることを実装後に確認してから確定する。
**wave 前の実コードの形**を必ず含める。隔離実行では closure pin / 批准を意図的に再固定し、
generic な drift 失敗が semantic gate より先に出ないようにする (A-9)。

| # | 変異 | wave 前の形か | 期待 kill |
|---|---|---|---|
| M1 | `wal.append` の receipt 検査を削る | ○ (現行に検査なし) | 直接 append 負対照 |
| M2 | receipt 検査を v2 枝の内側へ移す | ○ (現行 `wal.py:1054-1061` の形) | v1 lock 負対照 |
| M3 | 消費済み集合の走査を落とす | — | 同 ID 二回目 |
| M4 | `_append_records_locked` の stage 制限を外す | ○ | COMMIT 注入 |
| M5 | issuer を verifier 外の caller 側へ戻す | ○ (現行 `res.certified`) | 偽 evidence 負対照 |
| M6 | qualification emit の receipt 検査を落とす | ○ | emit 直接負対照 |
| M7 | `guided._log_eval` の source proof を落とす | ○ (現行 bare bool) | `cmd_evaluate` 負対照 |
| M8 | `ident` を direct `load_activation_state` へ戻す | ○ | serial-1 calibration 破損 fixture |
| M9 | prefix wrapper を head wrapper へ差し替える | — | 旧 v2 lock 誤拒否の正例 |
| M10 | 批准比較を落とす | ○ (現行に比較なし) | 未批准 digest 負対照 |
| M11 | closure を exact 14 へ戻す | ○ | S8C 判定器改変・receipt 実装面改変 |
| M12 | 台帳の strict prefix 検査を落とす | — | 行の削除・置換・並替え |

過剰拒否の正例 (DW-M01): 批准済み digest での新 lock 生成成功、正常 receipt での COMMIT 成功、
既存 v1 receiptless WAL の replay/recovery 成功、旧 v2 lock の prefix 検証成功。

## 6. T-396 との衝突 (B-11) — 親 brief の撤回と運用裁定

親 brief は「branch 差分ゼロゆえ重複なし」と書いた。**撤回する。**
`dev-wave-t396-hole-allowlist/s2-plan.md:256-260,368` は
`campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS`、`contract_loader_binding.py`、
`test_t671_source_binding.py` を編集する計画である。単位 C と同一の編集面である。
(T-396 の plan は closure を「8 path → 9 path」と書いており現行 14 と食い違う =
T-396 の plan 自体が古い state に対して起草されている。)

**運用裁定 (可逆なので諮らず実施):** 単位 A・B を先に走らせ、単位 C の closure pin 編集は
段 6 受入直前に T-396 の land 状況を再測してから確定する。T-396 が先に land していれば
その pin へ rebase して exact 集合を再導出し、していなければ本 wave が先に取る。
どちらでも「exact 集合の再導出」は段 6 の親照合項目に含める。

## 7. 撤回した親 brief の主張

1. 「COMMIT producer は pipeline 2 + guided 1」 → **5 件** (qualification emit 2 を含む)。
2. 「`guided.py:141` は上流 assertion が守るので実効的に無防備でない」 → **誤り**。
   `cmd_evaluate` は `assert_complete` を経ない (A-8)。
3. 「pin は 2 本 + consumer 6 file」 → **production 3 + test/support 9 = 12 file**、
   さらに closure と無関係な `14` 契約が別に存在する (B-5)。
4. 「live lock 30 件」 → **32 件** (WAL 付き live 30 / lock のみ凍結 2)、全 v1 (A-10)。
5. 「(P5) 順序 762→1286→1287→1252」 → 撤回。批准は全 enforcement bytes 確定後 (B-9)。
6. 「(P4) 判定器候補に `s8b_oracle_judge.py`」 → 撤回。S8C exact 3 が正しい (A-12/B-7)。
7. 「[T-396] と編集面の重複なし」 → **撤回**。同一 closure pin を編集する (B-11)。
