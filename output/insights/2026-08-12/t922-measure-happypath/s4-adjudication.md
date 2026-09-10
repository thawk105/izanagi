# 段 4 裁定 — [T-922]

2026-08-12 22:08 JST。入力 = `s1-brief.md` / `s2-plan.md` / `s3-luna.md` (NO-GO, BLOCKER 2) /
`s3-sol2.md` (NO-GO, BLOCKER 7)。親が一次資料で検算した結果だけを real とする。

## 0. 両レンズを貫く一本の事実 (親の裁定の土台)

**T-810 測定装置には production producer が存在しない。**
`launch_intent` / `validator_kwargs` / `admission_policy_path` を**書く**非 test コードは repo に
1 つも無く、`.sh` / `.pbs` / `.json` からの coordinator 呼び出しも 0 件 (親が実測、21:52)。
これは事故ではなく設計である — D331 が「本 wave は witness の発行経路を実装しない、実体は
§9.1 item 6 の人間による第 1 段承認 ID」と明記し、T-923 (policy の ratify) はユーザー deny 中。

**帰結:** 「呼び出し側の申告を信じるな」という T-922 の全項目は、
**信頼の根 (authority) を誰が持つのか**という 1 つの未裁定問題に帰着する。
producer が無い以上、caller config の外に根を置くには
「coordinator 自身が置かれている場所」しか残っていない。
両レンズの BLOCKER 7 件のうち 5 件はこの 1 点の別表現である。

## 1. real / refuted

| # | レンズ | 所見 | 判定 | 検算 |
|---|---|---|---|---|
| B1 | sol | S-B の live roots も caller の `repo_root` を `resolve_git_identity` するだけで caller 由来 | **real** | `s2-plan.md:111` の述語がまさに caller 値を渡している |
| B2 | sol | 対案 X の `pbs_wrapper.__file__` は PYTHONPATH shadowing で汚染可能 (`tools/pegasus` は `__init__.py` を持たない namespace package) | **real (A)** / **real (B)** | `ls tools/pegasus/__init__.py` 不在を親が確認。依存閉包 (B) も別問題として real |
| B3 | sol | 再 hash を `_scheduler_effect()` にだけ置くと `_subprocess_scheduler()` から迂回。qsub 後〜node 読取までの置換も束縛できない (TOCTOU) | **real** | D331 が private 名を能力境界でないと明記。luna の BLOCKER 2 と同一 |
| B4 | sol | 計画 S-D は `argv[1]` の wrapper path を捨てて import 済み `W.main` を呼ぶので staged artifact を実行しない | **real** | `s2-plan.md:215-216` の逐語どおり |
| B5 | sol | budget verifier は receipt が指す caller 選択の ledger と自己整合するだけ。policy に canonical path が無い | **real** | `t810_budget.py:412` は external 判定のみ |
| B6 | 両 | guard producer は現 API では未解決 (config に transcript/owner/phase 無し、B identity は submit 後) | **real** | `t810_coordinator.py:473-492` / `:686` / `:807` |
| B7 | sol | wrapper を閉じても binary は自己整合で任意のまま。prereg に binary hash の値が無い | **real** | 親が prereg を走査済み — hash field 不在 |
| M1 | sol | budget の「current ledger = receipt after」条件は正当な並行 reservation を殺す (過剰拒否) | **real** | 受理集合を縮小する wave の典型 |
| L1 | luna | S-D は最上位 `coordinate()` / CLI を通らず headline 過大 | **real** | 0 節と合わせ、最上位を通す道はそもそも塞がれている |
| L2 | luna | fixture 波及に 3 site 漏れ | **real** | 実装子へ渡す |
| L3 | luna | 変異の単独帰属が 4 件不成立 (後段先取り) | **real** | 事前登録で照準し直す |
| L4 | luna | author-2 先行は必須でない | **moot** | guard/budget を scope 外にしたので author は 1 人 |
| — | sol | D328 判定 (P1) は維持可能。ただし対案 X を裁定へ返す理由は D328 でなく authority | **採用** | (P1) は維持。返す理由を差し替える |
| — | 両 | 受理を広げる変更・skip/xfail・期待値緩和は無し。規律 1 違反も無し | **確認** | — |

## 2. 裁定 — 実装する (scope in)

**S-A′ 宣言と実体の不一致を拒否する (T-922 (2) の部分)**

- `_read_regular_bytes` を使う `_assert_declared_file_identity()` を coordinator へ置く。
- 置く場所は **`_subprocess_scheduler()`** (最内の effect adapter。B3/D331 への対応) と
  `publish_wrapper_request()` の 2 点。`_scheduler_effect()` だけに置く案は却下。
- **anchor の形 (B2-A への対応):** 比較の相手は `pbs_wrapper.__file__` ではなく
  **`Path(t810_coordinator.__file__).resolve().parent / "t810_pbs_wrapper.py"`** とする。
  import 解決ではなく coordinator 自身の設置場所から**パスで**導くため、
  PYTHONPATH shadowing で差し替えられない。
- **主張してよいこと:** 「申告 hash と実 bytes の不一致」「prepare 後の改竄」「同梱 wrapper と
  異なる wrapper」を拒否する。
- **主張してはいけないこと:** 「任意 wrapper を拒否する」。staged package の依存閉包 (B2-B)、
  binary (B7)、node 読取時点の bytes (B3-B) は**開いたまま**である。

**S-B′ repo anchor を caller から奪う (T-922 (4)。完全実施)**

- roots の authority を **coordinator 自身の設置場所**から取る:
  `resolve_git_identity(Path(t810_coordinator.__file__).resolve().parents[2])`。
- caller 提供の `repository_roots` は**削除せず和集合**にする。caller は roots を
  **増やすことしかできない** (検査を厳しくする方向にしか動かせない) ので、
  過剰拒否のリスクだけを負い、迂回はできない。
- 置く場所は **`prepare_group()` 内、最初の `_ensure_external_root()` より前**
  (`coordinate()` だけに置く案は luna BLOCKER 2 で却下)。
- これで sol B1 の具体入力 (`repo_root=/tmp/fake-repo` + 実 repo 内 `work_root`) は
  最初の mkdir より前に拒否される。

**S-D′ coordinator artifact → staged wrapper CLI の統合 (T-922 (1)(6) の達成可能部分)**

- **名前を実態に合わせる。**「production 正例経路」とは呼ばない。
  呼称 = 「coordinator が生成した script から staged wrapper CLI へ到達する統合経路」。
- **B4 への対応:** import 済み module を呼ばず、**生成された script が指す staged wrapper file を
  subprocess で実行する。** `argv[1]` の path を捨てる実装は却下。
- 到達点は「`--request` の parse → 静的 request の decode → PBS 環境変数からの runtime identity
  補完」まで。node 固有の probe は既存単体テストが担う。
- 具体入力 `exec python3.10 /tmp/evil.py --request <req>` で**失敗する**ことを同時に検査する
  (B4 の攻撃例をそのままテストにする)。

**fixture 実体化** — `package/wrapper.py` に同梱 wrapper の実 bytes を置き、
`wrapper_sha256: H` 等の定数を実 hash にする。**期待値は 1 つも緩めない。**
luna が挙げた 3 site (`test_t810_coordinator.py:702-714`、
`test_t810_pbs_wrapper.py:269-364`、同 `:421-597`) を波及一覧へ追加。
`test_mutation_fanout_contract.py:306` は別 schema・別責務なので**除外し、理由を明記**する。

## 3. 裁定 — 実装しない (裁定パッケージとして返す)

いずれも「形だけ結線して実施済みと書く」ことを禁じる。**台帳に「実施済み」と書かない。**

- **R1 wrapper/binary の authority (T-922 (2) の完全形、(5))** — 自己整合した任意
  wrapper/binary を拒否するには caller 外の authority が要る。prereg に hash field は無く、
  producer も無い。**返す理由は D328 ではなく authority の不在**である ((P1) は維持)。
  選択肢: (a) prereg へ wrapper/binary hash を追加、(b) staging producer を実装して
  そこを authority にする、(c) 承認 ID (§9.1 item 6) に hash を含める。
- **R2 staged package の依存閉包 (sol B2-B)** — staged 側の `tools/pegasus/*` が
  同梱と異なる実装でも wrapper 自身の bytes 一致は通る。
- **R3 node 読取時点の bytes 束縛 (sol B3-B、TOCTOU)** — qsub 直前の一致は node が実際に
  読む bytes を束縛しない。node 側での自己検証が要る。
- **R4 guard producer の 2 相結線 (T-922 (3) の guard 側)** — snapshot provider、
  submit 後の B identity 取得、pre-release 再評価、deny 時 withdraw、receipt schema の
  2 相化が要る。**現 API では不能ではなく未裁定。**
- **R5 budget の canonical ledger anchor (T-922 (3) の budget 側)** — receipt が指す ledger を
  読むだけでは「唯一の予算台帳」を検証しない。policy に canonical path を置く裁定が要り、
  それは admission policy = T-923 (deny 中) に触れる。加えて M1 の過剰拒否 (並行 reservation)
  を避ける設計 (chain 内 event 検証) が要る。
- **R6 production producer の不在そのもの** — 0 節。**これが T-922 の真の上流 blocker**であり、
  §9.1 item 1 は R6 が閉じるまで充足しない。

## 4. 変異事前登録 (DW-M01)

L3 の「後段先取り」を踏まえ、**実効 gate へ照準した 6 件**を登録する。
各件、同じ入力を拒否する層が前後に無いことを実装子に確認させる。

| ID | 変異 | 単独で殺す期待テスト | 先取り検査 |
|---|---|---|---|
| M1 | `_subprocess_scheduler()` の live hash 再検査を削除 | `test_scheduler_adapter_rejects_wrapper_changed_after_prepare` | `_scheduler_effect` 側に**置かない**ので先取り無し |
| M2 | coordinator anchor の wrapper 比較を caller 申告値どうしの比較へ退化 | `test_staged_wrapper_must_match_shipped_module_bytes` | 申告一致は通るので `_assert_declared_file_identity` に先取りされない |
| M3 | `prepare_group()` の live repo anchor を削除し caller roots だけにする | `test_prepare_group_rejects_forged_git_identity_before_any_mkdir` | `coordinate()` を経由しない直呼びで検査するので先取り無し |
| M4 | anchor roots と caller roots の**和**を**caller 側のみ**へ変更 | 同上 (別 case) | — |
| M5 | `_canonical_job_script()` から `--request` と path を削除 | `test_generated_script_executes_staged_wrapper_cli` (subprocess 実行) | **既存 `test_t810_coordinator.py:465-475` が先取りする** → 変異を「script は生成するが request path を別 slot のものにする」へ照準変更 |
| M6 | `_read_regular_bytes` の読取前後 fingerprint 一致検査を削除 | `test_declared_identity_rejects_file_swapped_during_read` | 単独帰属を実装子に確認させる |

**過剰拒否の正例 (受理集合を縮小する wave の必須登録):**

| ID | 正例 | 期待 |
|---|---|---|
| P1 | caller が anchor roots の**外**に正当な `work_root` を置く | 受理される (S-B′ が正当運用を殺さない) |
| P2 | staged wrapper が同梱 module と byte 同一 | 受理される (S-A′ が正例を殺さない) |

## 5. 分割と投入

guard/budget を scope 外にしたため**実装子は 1 人**。所有 = `t810_coordinator.py` /
`t810_pbs_wrapper.py` / `t810_harness_schema.py` と対応 test 3 file。
`t810_guard.py` / `t810_budget.py` / policy json は**触らない**。

## 6. 撤回する親の主張

- 「(1) は実質閉」→ **撤回。** 配線は閉じているが、production 正例として検証する道は
  producer 不在で塞がれている (0 節)。達成できるのは統合経路の成立まで。
- 「対案 X で任意 wrapper を拒否できる」→ **撤回。** shadowing (B2-A) を path anchor で
  塞いでも、依存閉包・binary・TOCTOU が残る。部分 hardening 以上を主張しない。
- 「(3) を本 wave で実施する」→ **撤回。** guard・budget とも裁定へ返す。
- (P1) の D328 判定は**維持**。ただし R1 を返す理由は D328 ではない。
