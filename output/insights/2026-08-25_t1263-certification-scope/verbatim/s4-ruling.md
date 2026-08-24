# 段 4 裁定 — [T-1263]

段 2 プラン (`s2-plan-out.md`) と段 3 の 2 レンズ (`s3-lensA-out.md` / `s3-lensB-out.md`) を
親が real / refuted・採用 / 不採用・scope 内 / 外に裁定する。以下がプラン v2 である。

## 0. 前提の更新

- wave 開始時の main = `16086f12`。段 4 直前に main が `fe355590` へ進んでいたため、
  実装子を起こす前に `--ff-only` で取り込んだ。取り込み範囲は本 wave の編集面
  (`tools/codex_reasoning_ab.py`、`orchestrator/tests/test_codex_reasoning_ab.py`) に
  1 行も触れていない。`python3 tools/check_ai_provenance.py` は全史で rc=0。
- 裁定 inbox (`docs/handoff/`) と `docs/worklog.md` を段 4 直前に再走査した。
  T-1263 に関する新しい裁定・更新は無い。

## 1. 親 brief の撤回事項

### R-1 (P1) は refuted。撤回する。

段 2 と段 3 レンズ A (A-2, A-6) が独立に反証した。prelaunch 失敗 attempt が final になっても、
`make_packets` が final の `output` descriptor を必須にするため
(`tools/codex_reasoning_ab.py:10330-10335`)、正規経路では packet を作れない。packet 一式を
手で組んでも `output_sha256` が無いため `_load_adjudication` の SHA 結線
(`:8862-8905`) が別の理由を積む。**未検証 snapshot 由来 packet が `valid: true` へ到達する
公開経路は現行に存在しない。**

### R-2 brief の「membership 検査で受理集合が狭まる」も撤回する。

レンズ A の A-1 が real。membership 検査が偽になる入力は、すべて既存 snapshot 理由を
同時に積む。したがって **membership 検査単独では、今日緑の manifest を赤にできない。**
本 wave の worklog・decisions・宣言 field のいずれにも「membership が受理集合を狭めた」と
書いてはならない。

### R-3 brief 実測表の 3 行を訂正する (A-6)。

- `verify_snapshot` を呼ぶのは `_replay_manifest` だけではない。supervisor も実行前後に呼ぶ
  (`tools/codex_reasoning_ab.py:6854`, `:7014`)。正しくは「**report を作る側で**再検証するのは
  `_replay_manifest` だけ」。
- prelaunch 失敗 attempt が「一度も snapshot 検証を通らない」は過一般化。supervisor 側の
  `verify_snapshot` 成功後に version probe や Popen で失敗する場合がある。正しくは
  「**replay 側の検証を通らない**」。
- `make_packets` は「output bytes を写すだけ」ではない。schedule 正規化・cardinality・
  slot 集合も検査する (`:10265-10302`)。

## 2. 採用する所見と実装内容

### R-4 [A-1 / 採用・real] membership 検査は冗長だが恒真ではない。実装する。

ユーザー裁定は「材料レポートに載る packet だけは未認証 snapshot 由来でないことを 1 箇所で
検査する」であり、検査の実装を要求している。冗長であることは実装しない理由にならない。
ただし**性格を正しく記録する**: これは受理集合を狭める gate ではなく、
**report が snapshot 再検証に依存していることを構造的に固定する検査**である。
上流の snapshot 再走・evidence 伝達が将来外れたとき、この検査が赤くなる。

### R-5 [B-1 / 採用・real] 宣言は private helper でなく公開 API が出す。

`_aggregate_verified` に宣言を付けると、helper を直呼びして
`verdicts` と空 `reasons` を渡すだけで「宣言付き `valid: true`」を作れる
(`tools/codex_reasoning_ab.py:9172-9180`, `:9557-9561`)。これは本 wave が防ごうとしている
虚偽表示そのものである。**宣言 field は `verify_manifest` が自分の全 return path で付ける。**
`_aggregate_verified` は宣言を付けない。`aggregate_manifest` は `verify_manifest` へ委譲
しているので自動的に付く。

### R-6 [A-4 / A-5 / B-9 / B-4 / 採用・real] 宣言 field の形と識別子を確定する。

段 2 案の `"aggregate.valid"` は実在する JSON path ではなく、`"packet"` (artifact kind) と
`"packet_state"` (manifest descriptor 名) が同じ配列に混在していた (B-4)。
`"source_run_snapshot_verified"` は実装より強い主張だった (A-5 / B-9) —
実装が保証するのは「凍結 pre/post oracle と replay 時現物の evidence 再走が成功した」ことで
あって、run 実行時点の歴史的 snapshot の再構成ではない。確定形:

```json
{
  "certification_scope": {
    "certification_subject": "material-report",
    "certified_entrypoints": ["verify", "aggregate"],
    "certified_report_fields": ["valid"],
    "uncertified_artifact_kinds": [
      "packet",
      "packet_state",
      "verdict_log",
      "revealed_map"
    ],
    "material_packet_requirement": "mapped_final_run_snapshot_evidence_replayed",
    "closed_world": true
  }
}
```

- `certification_subject` は `docs/glossary.md` の variant 単位の certified と混同させないため
  (B-4)。
- `certified_entrypoints` は R-5 の限定を機械可読にする。
- `material_packet_requirement` は evidence 再走に限定した識別子へ弱めた (A-5 / B-9)。

### R-7 [A-4 / P4 / 採用・real・scope 内] run ごとの pre/post 再検査と cache key 強化。

現行 `snapshot_cache` は `oracle_path.as_posix()` だけを key にし、**pre/post 一致比較まで
cache miss 分岐の内側にある** (`tools/codex_reasoning_ab.py:10023-10029`)。同じ oracle path を
共有する 2 本目以降の run は、自分の `snapshot_after` を一度も比較されない。
**これは本物の穴であり、今日緑の manifest を赤にできる唯一の変更である** (A-4)。

「検証済み run 集合」を健全に導出するには、run ごとの pre/post 比較が必須なので scope 内で
採用する。cache key は `(oracle_path.resolve().as_posix(), snapshot_oracle descriptor の
sha256, case)` にし、**`verify_snapshot` が正常 return し canonical replay bytes が一致した
identity だけ** cache に入れる (現行は mismatch reason を積んだ後も cache に入る)。

**この変更が受理集合を狭める唯一の箇所である。** membership 検査ではない。
worklog・decisions はこの帰属を取り違えてはならない (A-4)。

### R-8 [B-8 / 採用・確認事項] 受理集合は狭まるだけ。

親も静的に確認した。`valid` は一貫して `not reasons`。新規は reason 追加のみ。
cache 細分化は hit を減らす方向、pre/post の全 run 化は検査回数を増やす方向。
今まで赤かった manifest が緑になる経路は無い。実装後に親が変異の正例 (MUT-7) で実測する。

### R-9 [B-6 / B-7 / 採用・確認事項] 凍結 bytes と既存契約は壊さない。

`SCHEMA_VERSION` は 2 のまま。packet-state と custodian mapping は触らない。
既存 `failure_reasons` 文字列は 1 つも消さない・改名しない。
必須引数化で壊れる `_load_adjudication` 直呼出しは
`orchestrator/tests/test_codex_reasoning_ab.py:11246-11248`, `:11282-11284`,
`:11311-11313`, `:11416-11418` の 4 箇所。実装子が全部更新する。

## 3. scope 外と裁定した real 所見 (起票してユーザーへ返す)

### R-10 [B-2 / real・scope 外] 中間 CLI と単独 score は守られない。

`make-packets` / `append-verdicts` / `freeze-verdicts` / `reveal-mapping` / `score-run` は
いずれも packet 由来値を外へ出すが、ユーザー裁定が「全中間層への再検証要求は取らない」と
明示的に却下している。**実装せず、宣言 field の `uncertified_artifact_kinds` で
機械可読に告知するだけとする。** 裁定パッケージへ。

### R-11 [B-3 / real・scope 外] invalid report にも axis ledger が残る。

`reasons` があれば旧 6 field は `None` になるが (`:9507-9518`)、
`primary_judgment_axis_ledger` などの axis ledger は無条件で残る (`:9563-9578`)。
宣言は「certified なのは `valid` だけ」と言うので**虚偽ではない**が、
「未検証由来の値を report に載せない」まで求めるなら不足する。
受理集合と report shape を変える別判断なので scope 外。起票。

### R-12 [B-5 / real・scope 外] 既存の凍結材料 report には宣言が無い。

`output/insights/2026-08-09_t181-certified-rerun/{aggregate,verify}.json.gz` は
`certification_scope` を持たないまま「認証済み集計」として参照されている
(`docs/phase3.md:1167-1176` 他)。凍結 bytes は変更禁止なので scope 外。
sidecar で明記するか「新規生成 report のみ対象」とするかはユーザー裁定。起票。

### R-13 [A-3 / 採用・記録方法の裁定] 変異台帳は 2 種類を分けて書く。

局所配線の証拠 (宣言 exact 一致、evidence 伝達 spy、membership append) と、
manifest 一本で受理集合が動く証拠 (pre/post 全 run 化) を**同じ欄に混ぜない**。
前者を「材料レポートの受理集合の純増検出力」と書いてはならない。

## 4. gate の署名と通る正例 (DW-S04)

### gate 1 — material packet の evidence 要求 (R-4)

- **拒否**: `verify_manifest(manifest_path, sessions_root=R)` において、revealed mapping の
  `packet_id -> run_id` のうち `run_id` が snapshot evidence 再走に成功した run 集合に
  含まれないものが 1 件でもあれば、`failure_reasons` へ
  `"<packet_id>: material packet source run lacks replayed snapshot evidence: <run_id>"`
  を積み、`valid` を `false`、rc を `RC_AGGREGATE` にする。
- **通る正例**: 全 final attempt が replay 側 snapshot 検証を通過した完全な実験 manifest
  (既存 `test_verify_replays_complete_fake_codex_experiment` の fixture)。
  従来どおり `valid: true` / `experiment_complete: true` になり、`certification_scope` が付く。

### gate 2 — run ごとの pre/post evidence 一致 (R-7)

- **拒否**: 同一 oracle identity を共有する run のうち、自分の `snapshot_after` が
  `snapshot_oracle` と bytes 一致しない run があれば、既存文字列
  `"<run_id>: pre/post snapshot oracle mismatch"` を積み `valid` を `false` にする。
  **2 本目以降の run でも省略しない。**
- **通る正例**: 同一 oracle identity を共有する 2 run がいずれも
  `snapshot_after == snapshot_oracle` の manifest。`valid: true` のまま。

## 5. 変異事前登録 (DW-M01)

**期待 node は裁定文からの転記ではなく、実装後に親が 1 件ずつ注入して実測してから登録する**
(F28 の再発防止)。ここで登録するのは変異の位置・向き・単一理由性の確認義務である。

| ID | 変異 | 種別 | 単一理由性の確認義務 |
|---|---|---|---|
| MUT-1 | `certified_report_fields` を `["valid", "packet"]` にする | 宣言 | 宣言 exact 比較 node 以外がこの入力を拒否しないこと |
| MUT-2 | `uncertified_artifact_kinds` から `"packet"` を落とす | 宣言 | 同上 |
| MUT-3 | `material_packet_requirement` を `"packet_self_certified"` にする | 宣言 | 同上 |
| MUT-4 | `_replay_manifest` が実測集合でなく final attempt の全 run ID を渡す | 配線 | 既存 snapshot 理由は変異前後とも残るため、report の赤では区別できない。集合を直接観測する node だけが殺すことを確認する (A-3 C5) |
| MUT-5 | `_load_adjudication` の membership 条件または reason append を削除する | 配線 | 他層が同じ入力を拒否しないこと。冗長性ゆえ**公開 manifest では殺せない**ので、必須引数の契約を直接試す node で殺す |
| MUT-6 | pre/post 一致比較を cache miss 分岐の内側へ戻す (path-only skip へ退行) | 受理集合 | 同一 oracle identity を共有する 2 run の manifest でだけ差が出ることを確認する。**本 wave 唯一の manifest 級 kill** |
| MUT-7 | 検証済み run 集合を常に空にする (過剰拒否) | 正例 (承認外の過剰拒否検出) | 既存 end-to-end 正例 `test_verify_replays_complete_fake_codex_experiment` が赤くなること。DW-M01 の「受理集合を縮小する wave では正例も登録する」に対応 |

MUT-6 の anchor が実装後に一意でなければ `DW-M04` に従い停止する。

## 6. 実装単位

編集面 2 file、Codex `role=author` 1 本。依存が一本道 (evidence 導出 → 集合伝達 → 検査 →
宣言 → テスト) なので分割しない。docs は親が書く。
