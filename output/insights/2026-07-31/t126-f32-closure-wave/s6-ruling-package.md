authority: none
default_effect: no-state-change

# T-126 F3-2 closure — ユーザー裁定パッケージ

本 wave は段 6 まで完了し、**統合 commit の直前で fail-closed 停止**した。停止理由は
`docs/ai-provenance.md` の「実装面の Codex author 契約」であり、迂回しない。

## 1. 停止理由 (最優先の裁定事項) — **2026-08-01 解決済み**

> **後日の追記**: 本節の択一はユーザーが (b) を裁定した。ただしその後の調査で、main は既に
> D105 [T-205] として `AI-Agent-Waiver: reason=<ident>; ratified=<YYYY-MM-DD>` を land 済みであり、
> 同じユーザー裁定 (2026-07-31) を別セッションが先に正規化していたことが判明した。
> 自前の例外実装 (D98) は重複かつ非互換 (既存 main commit を誤拒否・番号衝突・docs 予算超過・
> forward correction の防壁を弱める) のため**破棄**し、main の waiver 機構を使って commit した。
> 以下の §1 本文は停止時点の記録として残す。

### 事実

- ユーザー裁定により、本 wave は Codex を使わず Claude の子で plan / 敵対相談 / 実装 /
  レビューを回した (「codex はレートリミットが近いので claude で代替してください」)。
- `docs/ai-provenance.md`「実装面の Codex author 契約」は次を規定する。
  > 小さい、軽量版、test-only、probe-only、production 挙動 0 は免除理由にならない。
  > **Codex が実行不能なら Claude が代行せず停止し、例外の必要性をユーザー裁定へ返す。**
- `tools/check_ai_provenance.py` は `IMPLEMENTATION_PREFIXES`
  (`orchestrator/`, `tools/`, `hooks/`, `.github/`, `.codex/`, `external/`) を変更する
  AI 関与 commit に `product=codex; role=author` の trailer 行が無ければ機械的に拒否する
  (`validate_implementation_author`)。**checker に免除・allowlist・環境変数の escape は無い**
  (grep 実測)。
- 本 wave の実装面 (`orchestrator/qualification/collector.py`、
  `orchestrator/tests/test_t126_pegasus_tools.py`) を書いたのは Claude の子である。
  正直な trailer は `product=claude; …; role=author` になり、checker は赤になる。
  `DW-STOP` は検査赤での続行を禁じる。codex と偽る trailer は、この規約が防ごうとしている当のもの
  なので採らない。

### 裁定を求める択一

| 択 | 内容 | 帰結 |
|---|---|---|
| (a) | **Codex quota 回復を待ち、Codex `role=author` の実装子に再著述させてから commit する** | 契約を一切曲げない。本 wave の Claude 実装は「証拠入力」に格下げし、Codex 実装子が同じ裁定 (s4 / s6) から書き直す。追加コストは実装 1 巡 + 受入再走 |
| (b) | **本 wave 限りの例外を承認する** | 正直な `product=claude; role=author` で commit するため、`docs/ai-provenance.md` と `tools/check_ai_provenance.py` に「Codex 実行不能時の記録付き例外」を新設する必要がある。契約と checker の変更は `docs/decisions.md` 級の裁定であり、AI が既成事実にできない |
| (c) | **commit せずに wave を有界終端する** | 実装差分は worktree に未 commit のまま残す。前 wave と同じ状態に戻る (再開は可能だが、変異 matrix 本走・local main 取り込みは未達のまま) |

親の推奨は **(a)**。理由: この契約は「Claude が代行した事実を不可視にしない」ために存在し、
今回まさにその状況が起きている。(b) は契約自体の改訂を伴うため、レートリミットという一時的事情で
恒久ルールを緩める前に、(a) の追加コスト (実装 1 巡) と比較する価値がある。

## 2. 本 wave の完了状況 (裁定に依存しない部分はすべて完了)

- **実装**: `collector.py` (+36/−3、4 hunk) と `test_t126_pegasus_tools.py` (+227/−40)。
  所有外 0 file (product 305 file の SHA-256 manifest 突き合わせで確認)。
- **敵対検証**: 段 3 レンズ 2 本、段 6 レンズ 2 本、焦点再レビュー 1 本。
  最終判定は **GO / BLOCKER 0 / closed 17 / partial 1 / regressed 0**。
- **計算ノード受入**:
  - related 1 回目 `874729.nqsv` (bnode006) `435 passed, 9 skipped` / 全 rc=0
  - related 2 回目 `874766.nqsv` (bnode033) `441 passed, 9 skipped` / 全 rc=0
  - **全走 `874775.nqsv` (bnode042) `3710 passed, 19 skipped`**、
    check_codex_agents / check_docs / check_ai_provenance / git diff --check /
    source 前後一致 すべて rc=0、overall rc=0
- **未達**: 変異 matrix 本走、統合 commit、latest main 取り込み、local main 取り込み (段 9)。
  いずれも上記 1 の裁定待ちである。

## 3. 変異 matrix の erratum (`DW-M02`)

commit を待たずに証拠を得るため、worktree を一切変更しない隔離 scratch (`/scr`) で
診断走行を行った (`874776.nqsv`、bnode045)。結果は
`mutations=35 killed=35 survived=0 stops=0` だが、**baseline の失敗が 123 node あり無効**である。
scratch copy が `.git` と submodule を持たないため T-126 テスト群が baseline で落ちており、
事前登録した期待赤 node が baseline 失敗集合に含まれてしまっている。
各 mutation の `new_failed_nodes` は meta-test 1 件のみで、単一理由性の裏取りにならない。

初回結果は消さず erratum とする。**変異 matrix の本走は `DW-O19` どおり統合 commit 後に、
tracked file に対する `git checkout --` 復元で行う**。worktree の前後 SHA-256 は一致
(`worktree-before.sha256` == `worktree-after.sha256`) で、診断走行が worktree を汚していないことは
確認済みである。

## 4. 段 4 で scope 外と裁定した real 所見 (実装せず返す)

1. **S1' — series 完走 × targetless staging**: publisher が link 前に落ちた成功 series が
   `unreferenced in-job evidence` で恒久的に閉じない。閉じるには targetless bytes を
   `rejected-evidence/attempt-job-result.{bytes,json}` 等へ保全してから retire する必要があり、
   新しい artifact 種・schema・verifier 受理・変異を伴う。本 wave では T9 + M9i で
   「現行挙動を保ち、retire を targetless へ広げない」ことだけを固定した。
2. **B4 — collector 自身の receipt staging crash 残余**: `create_or_verify_json` の
   `os.link` 成功後 `unlink` 前に落ちると `.attempt-failure-receipt.json.create-*` が残り、
   `_manifest` が `create_or_verify_json` の abandoned-stage 回収より前に拒否するため恒久 deadlock。
   本修正で悪化しないが閉じもしない。
3. **B6 — `target_rejected=1` が `JOB_RESULT` を job-staging へ差し戻さない**:
   `attempt-pointer.json` 不一致時に `target-rejection.json` が attempt namespace へ落ち、
   series ありなら恒久拒否される。`tools/pegasus/t126_qualification.sh` の 1 行修正で閉じる。
4. **A4 派生 — retire の事実が receipt / ledger に残らない**: link/unlink window で落ちた attempt の
   final receipt が clean publish のそれと bytes 上区別できない。監査可能性を残すなら
   receipt schema と `expected_ledger_payload` の変更が要る。
5. **shell 側 crash window に実行裏取りが無い**: 既存テストは
   `IZANAGI_T126_TEST_EXIT_AFTER_BINDING` を常に設定するため `t126_qualification.sh:435-718` を
   一度も実行しない。本 wave は collector 側の挙動だけを実測で固定した。

## 5. backlog (nit、`DW-G05` の成果物影響を 1 行で書けないもの)

- M9h / M9e の anchor が長く、`collector.py` の当該行の 1 文字変更で meta-test が赤になる結合。
- `_EARLY_RETIRABLE_LIFECYCLES` の参照 site が 2 箇所であることの構造保証が
  コメントだけで機械化されていない。
- `T126_MUTATION_REGISTRY` の `node` が単数 field のため、複数期待赤 node の突き合わせが
  裁定文書の手作業に依存する。

---

## 6. main 統合時に判明した追加の裁定事項 (2026-08-01)

### 6-1. 共有 Pegasus policy を単一タスクの凍結証拠が縛る構造

T-139 の commit 済み evidence `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` が
`binding.policy.sha256` で共有 policy の bytes を凍結している。T-126 が同 file へ 9 key を
足したところ drift で赤になった。T-126 側は予約 policy を自前 file へ分離して退いたが、
**「共有 config へ key を足す任意のタスクが T-139 の証拠を壊す」構造は残っている**。
次に同じ file を触るタスクが同じ事故を踏む。恒久対応は T-139 の binding 設計の見直しか、
共有 config を「タスク別 file の集合」へ再編するかの裁定が要る。

### 6-2. T-126 job script の envelope 検査が恒真 (fail-open)

`tools/pegasus/t126_qualification.sh` の予約 envelope 検査は、`for k in keys: print(p[k])` が
`if ... raise` より**前**にあるため、宣言済みの拒否が発火しない。プロセス置換は終了ステータスを
伝えず `set -Eeuo pipefail` も効かないため、行数検査 (`-eq 3`) も通ってしまう。
submitter 側の凍結条件は個別 cap を凍結せず和が 2100 であることしか要求しないので、
`prologue/attestation/finalize = 1500/0/600` を commit すれば submitter を通過し、
job script 側の個別値検査も恒真のため `PROLOGUE_CAP_S=1500` が採用されて cap が緩む。
**本 wave の変更以前から同じ構造** (HEAD / main 双方で逐語同一) であり、受理集合を動かすため
本 wave では扱わなかった。1 行の移動で閉じるが、拒否の実発火は受理集合の変更にあたるので
D96 の手続 (決定記録 + 境界テストの同時更新) が要る。

### 6-3. Pegasus dispatch 経路で子プロセスの `python3` がノード既定へ落ちる

sanctioned entrypoint (`tools/run_tests.py` → `dispatch_compute`) 経由で全走すると、
T-126 の submitter を起動するテスト
(`test_m8b_post_qsub_prebinding_crash_never_uses_raw_stdout_authority`) が
`qsub-invocation.json` 不在で赤になる。同じ tree・同じ計算ノードでも、
Python 3.10 shim を PATH へ置く自前 harness では緑 (472 passed / 9 skipped)。
子プロセスの `python3` が計算ノード既定 3.9 へ戻る、前 wave の handoff が記録した既知問題と同型。
**T-126 の退行ではない**が、この経路では T-126 の submitter 系テストが偽赤になるため、
dispatch 側 (T-188 / T-205 の領域) で shim を配線するか、テスト側で解釈系を明示する裁定が要る。

### 6-4. 変異登録の nit 3 件

- `t126_qualification_member_term_grace_s` は consumer ゼロの orphan (移送前から同じ)。
  実走を支配するのは `t126_control_v1.json` を読む driver 側で、両者の一致を課す検査が無い
- `DEFAULT_RESERVATION_POLICY_PATH` は参照 0 件の dead constant
- prologue evidence の必須 key を 1 個増やしたが `schema_version` は据え置き
  (既存成果物 0 件を実測済みなので互換上の実害はない)
