結論は「payload 面の部分実装として条件付き GO」です。現行 production の値生成に wire・実効 diff・その SHA の直接コピーはありません。ただし SHA 由来 ID や WAL の自由文字列が偶然一致する場合はあり、その実行は payload を変えず gate で拒否します。以下は静的追跡結果であり、pytest は実行していません。

## (A) 現行 critic payload の実測判定

### `harness_result.variant`

値は [p3_autonomous_workload_trial.py:1651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1651) で組まれ、[同:1653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1653) が `outcome["variant"]` をそのままコピーする。

production default driver での生成元は次の三形態である。

- no-build は `None`。[p3_s4_loop_trigger_gating.py:553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:553)
- diff-quarantine reject は `diffq-` + SHA-256 先頭 12 hex。[p3_s4_loop.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:237)
- build 到達時は genome と source token の SHA-256 先頭 12 hex。[pipeline.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/pipeline.py:87)、選択点は [p3_s4_loop_trigger_gating.py:582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:582)。

判定は以下。

- 5-bit wire: **条件付きで含む**。意図的コピーではないが、hex hash 中に当該 5 文字が偶然現れ得る。32 個の canonical wire について現行 `diffq_variant_id` を静的列挙した範囲では「自分自身の wire」を含むものは 0 件だった。
- 実効 diff 全文: **含まない**。最大 18 文字程度の ID なので現行 diff 全文は収まらない。
- 実効 diff の 64-hex digest: **含まない**。長さ上不可能。

### `critic_digest`

[p3_autonomous_workload_trial.py:1647](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1647) が digest file を読み、[同:1658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1658) で全文をコピーする。production の生成点は [p3_s4_loop_trigger_gating.py:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:748) から呼ばれる `make_critic_digest()` で、[p3_s4_loop.py:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:272) が `render_text()` と `render_rejections()` を連結する。

- `render_text()` は genome・metrics を描画するが wire/diff/digest を直接読まない。[critic/digest.py:490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:490)
- `render_rejections()` は variant、src token、integrity notes、liveness extra、diff evidence を描画する。[critic/digest.py:556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:556)
- diff evidence の通常形は本文でなく 12-hex 短縮 hash。[diff_quarantine.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/diff_quarantine.py:319)。ただし malformed anchor や領域外行では raw 行を evidence に入れる枝がある。[同:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/diff_quarantine.py:383)、[同:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/diff_quarantine.py:448)

したがって三 vector とも、**直接は含まないが、WAL 由来文字列や hash が一致した場合は条件付きで含む**。特に wire は variant/hash の偶然一致、diff/digest は notes・extra・evidence 等へ同一文字列が既に入った場合に成立する。

現存 production artifact [s8a_trigger_loop_digest.txt:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/s8a_trigger_loop_digest.txt:1) の全 37 行には、32 種の wire、確認対象 diff、対応 SHA の一致はなかった。これは現存 artifact の実測であり、将来値の保証ではない。

従って現行確認値では baseline は赤にならず、payload の field/value 変更は不要。将来の正規値が偶然 hit した場合、payload を変えず成立させる唯一の方法は、その invocation を provider 手前で拒否することである。その値も受理しなければならないなら、除外追加は検査の恒真化、escape/hash 化は payload 値変更になるため、**実装を止めて裁定へ返す**。

## 実装プラン

新規 `orchestrator/campaign/reflux_noninterference.py` は現時点で存在せず、行番号はまだない。I/O・filesystem・driver import を持たない pure leaf とする。

公開 API は概ね次の形にする。

```python
CandidateMaterial(
    candidate_wire: str,
    effective_diff: str,
    effective_diff_sha256: str,
)

checked_role_payload(
    role,
    payload,
    *,
    candidate_materials: tuple[CandidateMaterial, ...],
) -> dict
```

`candidate_materials` に default は置かない。leaf は exact built-in JSON tree を plain dict/list に snapshot し、同じ snapshot を `_invoke` の hash 計算と provider に渡す。これで検査後に別 traversal の値へすり替わる Mapping/TOCTOU を避ける。入力そのものは変更しない。

top-level key は [現在の common producer:1006](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1006) を共通九 field とし、role ごとに次へ完全一致させる。

- planner: `current_perf`, `leading_indicators`, `whiteboard`。[同:1469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1469)
- coder: `leakproof_context`, `gating_spec`, `planner_direction`, `baseline`, `whiteboard`。[同:1495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1495)
- auditor: `working_diff`, `diff_digest`, `designated_source_context`, `correctness_digest`。[同:1557](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1557)
- critic: `harness_result`, `critic_digest`。[同:1649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1649)

nested map も閉じる。対象は descriptor の形 [s8b_descriptor.py:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/s8b_descriptor.py:121)、descriptor binding [同:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/s8b_descriptor.py:194)、metrics [p3_autonomous_workload_trial.py:692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:692)、whiteboard の五 field [p3_s4_loop.py:310](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:310)、planner direction、policies、critic harness result。未知 role、extra/missing key、非 JSON 型、非有限 float、cycle は同じ固定拒否に畳む。

全 string key/value を再帰走査し、各 `CandidateMaterial` の wire、非空 diff、diff SHA、および pin 済み IR schema SHA の substring を拒否する。auditor についてだけ、親 brief の P1 [brief.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-05_t244-p2-noninterference/brief.md:38) に従い次の二 path を例外とする。

- `$.working_diff` は out-of-band の `effective_diff` と byte 一致した場合だけ除外。
- `$.diff_digest` はその diff を leaf が再計算した SHA、および supplied SHA の双方と一致した場合だけ除外。

他 field に同じ diff/digest を複製すれば拒否する。空 diff は substring vector にせず、その SHA は検査する。

結線は `_invoke()` [p3_autonomous_workload_trial.py:904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:904) の最初、現行 payload hash [同:909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:909) より前とする。provider 呼出し [同:922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:922) 後では遅い。

`_run_workload()` の状態初期化点 [同:1433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1433) に material history を置き、preview [同:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1533) 直後に `coder.wire`、diff、再計算 SHA から current material を作る。planner/coder には過去 material、auditor/critic には current を加えた tuple を `_invoke` の非 payload 引数として渡す。`MAX_APPROVED_GENERATIONS = 1` は変更しない。

## (B) 恒真化を避ける正負境界

設計 draft が要求する観測面閉包は [README.md:416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-01_t244-reflux-design/README.md:416) の P2 に対応する。allowlist と値走査を独立に持つため、少なくとも次の変更は赤になる。

1. `_common_payload()` [p3_autonomous_workload_trial.py:1006](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1006) に `effective_mask` を追加する。key closure で赤。
2. critic の `variant` [同:1653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1653) を `coder.wire` に差し替える。値走査で赤。
3. `critic_digest` [同:1658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1658) を current working diff または SHA に差し替える。値走査で赤。
4. auditor の `correctness_digest` [同:1562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1562) へ diff をコピーする。auditor の許可二 path 外なので赤。
5. `GATING_SPEC` または `DESIGNATED_SOURCE_CONTEXT` を一 byte 変更する。[同:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:236)、[同:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:242)。pin 比較で赤。
6. planner 呼出し role [同:1476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1476) を未知名へ変える。provider 到達前に赤。

一方、捕まえられないものも明示する。

- base64、圧縮、Unicode 符号化、分割、言い換え、暗号化などの semantic copy。
- variant/hash、数値、metrics、文章長、順序を用いた相関・符号化。wire が hash の入力であっても、同じ字面でなければ検出しない。
- accept/reject、停止理由、呼出し回数、時刻、file size、provider error など payload 外の side channel。
- 許可 field に、禁止 vector と一致しない別コードで情報を載せる経路。
- role prompt、session、環境変数、artifact、report、provenance、直接 provider 呼出し。
- auditor は P1 により current diff と digest を意図的に観測する。従って「全 untrusted role から diff が消えた」とは主張できない。

これは [projection_guard.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/projection_guard.py:2) と同じく lexical tripwire であり、数学的な情報流非干渉ではない。

## (C) 必要な結線層と scope 外残余

8c driver 内では production の `provider.invoke` は [p3_autonomous_workload_trial.py:922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:922) の一箇所だけだった。planner/coder/auditor/critic の四 call site は [同:1475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1475)、[同:1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1513)、[同:1566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1566)、[同:1660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1660)。従って今回効かせるための必須層は、material 作成、四 call site から `_invoke` への out-of-band 引渡し、`_invoke` entry、検査済み snapshot の provider 利用である。

確認した残余は次のとおり。

- `_journal_auditor_skip()` [同:976](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:976) は role を呼ばない。`working_diff` を除いた pre-audit 情報を journal に書くだけで、payload gate の bypass ではない。一方、digest・理由等が journal/report に残る別観測面なので裁定候補。
- `_preview()` [同:653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:653) は role を呼ばないが、diff/digest の trusted producer であり material 結線が必要。
- 旧 trigger driver の `--preview-wire` は diff/digest を stdout へ直接出す。[p3_s4_loop_trigger_gating.py:769](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:769)、[同:817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:817)。実 LLM は main session が別途 spawn する設計 [同:783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:783) なので `_invoke` を通らない。
- sort driver にも同型の preview/stdout 経路がある。[p3_s4_loop_sort.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_sort.py:352)、[同:397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_sort.py:397)。
- provider 自身の public `invoke()` は payload を artifact に保存してから subprocess stdin へ渡す。[claude_projected_provider.py:253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/claude_projected_provider.py:253)。直接呼べば今回の gate を迂回できる。provider layer へ gate を置くには role と trusted candidate material を渡す新契約が必要。
- role が見る effective prompt は role file と mediated contract の連結である。[claude_projected_provider.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/claude_projected_provider.py:156)。特に coder contract 自体が例示 wire `"10100"` を持つ。[p3_autonomous_workload_trial.py:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:201)。これは payload gate の対象外。
- D51 provenance は auditor digest を保存する。[p3_s4_loop_trigger_gating.py:736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:736)。driver outcome は report に入る [p3_autonomous_workload_trial.py:1643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1643)。

provider layer、旧/manual driver、preview stdout、prompt bundle、journal/report/provenance は今回実装したふりをせず、別々の裁定パッケージ候補とする。この成果物が名乗れるのは brief [brief.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/output/insights/2026-08-05_t244-p2-noninterference/brief.md:28) のとおり「P2 の 8c payload 射影面の部分実装」までである。

## (D) auditor digest の命名

wire 上の `"diff_digest"` は payload 不変条件により維持する。同様に `AuditorVerdict.diff_digest` と report projection [p3_autonomous_workload_trial.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:753) も変更しない。

内部では次へ分離する。

- auditor 入力: `auditor_input_effective_diff_sha256`
- auditor 出力 echo: `auditor_verdict_echoed_diff_sha256`
- leaf の trusted material: `candidate_effective_diff_sha256`

`preview_result["diff_digest"]` を最初の名前へ束縛して payload key に入れ、parser 後の `auditor.diff_digest` を二番目へ束縛して照合する。既存 provenance key `"auditor_diff_digest"` [p3_s4_loop_trigger_gating.py:738](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop_trigger_gating.py:738) は外部 field 変更になるため残し、「verdict echo」と注記する。将来の field rename は別裁定とする。

## (E) 凍結定数の pin

leaf は driver の `GATING_SPEC` / `DESIGNATED_SOURCE_CONTEXT` を import して期待値を作らない。承認済み本文を leaf 側に独立な UTF-8 byte literal として置き、payload 値を `value.encode("utf-8") == PINNED_BYTES` で比較する。

静的計算値は次のとおり。

- `GATING_SPEC` [p3_autonomous_workload_trial.py:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:236): 351 bytes、SHA-256 `bd80b3cc64f24c995485eaa4cd26fd5c6a7257945e52e0bc159219aea0c75cd0`
- `DESIGNATED_SOURCE_CONTEXT` [同:242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:242): 868 bytes、SHA-256 `c55df71e844581d7881fd300f2b8d825b31ff2b6d901d7e96d2b69c53a7dac78`

専用テストも driver/leaf から期待値を取得せず、承認本文 byte と上記 digest を test literal として持つ。pin 合格後に限り、coder の `$.gating_spec` と auditor の `$.designated_source_context` を値走査から除外する。一 byte drift は除外前に拒否する。

IR について、現行 production に実在する schema identity は [reflux_ir.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_ir.py:19) の `SCHEMA_ID = "izanagi-trigger-gate-ir/v1"` だけで、独立した canonical schema bytes/SHA はない。その literal bytes の SHA-256 は `2a5fc8f2dd1e979870a7421274c24f9bea3457e446cc7ec4c1971ac6cbb6540e`。実装では誤称を避け `IR_SCHEMA_ID_SHA256` と命名して禁止 vector にする。「IR schema SHA」が emitter SHA、raw/effective IR SHA、別 schema artifact の SHA を意味するなら、その preimage 定義は裁定が必要であり、この gate で閉じたとは名乗らない。

## (F) disclosure-free な拒否

leaf は単一型 `RefluxNoninterferenceError`、固定 message `"invalid reflux role payload"` のみを公開する。入力、role、field path、vector 種別、長さを exception 本体や属性へ入れない。

[reflux_ir.py:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_ir.py:86) と同じく、内部検査中の例外は一度 handler を抜けてから `_reject()` し、`raise ... from None` とする。全拒否で次を同一に固定する。

- exact type、`str`、`repr`、`args`
- `vars(exc) == {}`
- `__cause__ is None`
- `__context__ is None`
- `campaign.*` / `orchestrator.campaign.*` の両 import 経路で同じ fingerprint

開発者向けには private pure classifier `_diagnose(...) -> internal enum/path | None` を置けるが、`__all__` に出さず production driver から呼ばない。開発者は debugger/REPL で in-memory payload を再投入して原因を確認する。journal/report へ reason code や vector を書かず、既存 supervisor error の type/message 記録 [p3_autonomous_workload_trial.py:1231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1231) にも固定文言しか到達させない。

## (G) 段 5 の所有分割

素集合にできる。

- 所有 A:
  - `orchestrator/campaign/reflux_noninterference.py`
  - `orchestrator/tests/test_reflux_noninterference.py`
- 所有 B:
  - [orchestrator/campaign/p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:904)
  - [orchestrator/tests/test_p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:774)

A は独立 literal fixture だけを使い、driver を import しない。B は四 role 結線、current material 作成、auditor key assert の追加、provider-before-reject integration を担当する。package `__init__.py` や共通 fixture を編集しなければ重複所有はない。merge 順は A → B。

既存 payload assert [test_p3_autonomous_workload_trial.py:774](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:774) には auditor capture と次の exact set を追加する。

```text
common_keys |
{working_diff, diff_digest, designated_source_context, correctness_digest}
```

## (H) 事前登録 mutant

新規テスト二ファイルにはまだ実在行番号がないため、assert は安定した test ID/name で pin する。対象行は現行実在行を示す。

| ID | operator | 対象 | 最初に赤くなる assert |
|---|---|---|---|
| M1 | SDL: entry gate 削除 | `_invoke` の現行 hash 手前 [p3_autonomous_workload_trial.py:909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:909) | B `test_rejects_before_provider`: `assert provider.calls == []` |
| M2 | MOV: gate を sink 後へ移動 | provider call [同:922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:922) | B `test_rejects_before_provider`: `assert provider.calls == []` |
| M3 | CRP: `"planner"` → 未知 role | [同:1476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1476) | A `test_unknown_role_is_uniformly_rejected`: `pytest.raises(RefluxNoninterferenceError)` |
| M4 | MFI: common に `effective_mask` 追加 | [同:1006](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1006) | B `test_current_payload_keysets_reach_all_roles`: `assert report["status"] == "complete"` |
| M5 | STR: `GATING_SPEC + " "` | coder assignment [同:1502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1502) | A `test_frozen_text_bytes_are_independently_pinned`: fixed rejection expectation |
| M6 | STR: designated context 一 byte変更 | auditor assignment [同:1561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1561) | A `test_frozen_text_bytes_are_independently_pinned`: fixed rejection expectation |
| M7 | VCP: auditor correctness digest へ working diff 複製 | [同:1562](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1562) | B `test_auditor_exemption_is_path_exact`: `assert auditor_provider.calls == []` |
| M8 | VCP: critic variant へ `coder.wire` | [同:1653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1653) | B `test_critic_wire_leak_is_rejected`: `assert critic_provider.calls == []` |
| M9 | VCP: critic digest へ working diff | [同:1658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1658) | B `test_critic_diff_leak_is_rejected`: `assert critic_provider.calls == []` |
| M10 | VCP: critic digest へ current diff SHA | [同:1658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1658) | B `test_critic_diff_sha_leak_is_rejected`: `assert critic_provider.calls == []` |
| M11 | HCR: preview digest を diff と不一致な固定 SHA へ | digest producer [同:670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:670) | A `test_candidate_material_recomputes_digest`: fixed rejection expectation |
| M12 | VCP: IR schema-ID SHA を critic digest へ挿入 | critic assignment [同:1658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1658) | B `test_critic_ir_schema_sha_leak_is_rejected`: `assert critic_provider.calls == []` |

テストは実行していない。上表は親が実装・静的確認後に実測するための事前登録であり、ここでは pytest 緑を完了条件にしていない。

## 総括

(A) 現行 producer は variant/critic digest へ wire・実効 diff・その SHA を直接コピーしていない。
SHA/WAL 文字列の偶然一致では条件付きで含み得るが、確認した現存 artifact と canonical diffq 32 件は非該当だった。
従って payload の field/value を変えず、hit した invocation を provider 手前で拒否する部分 gate は実装可能。
判定は **GO（8c payload 射影面のみ）**。baseline 実測が赤、または別の IR SHA 定義が必須なら実装せず裁定へ返す。