## 恒真化の検査

結論: 照合述語は恒真ではない。

- `expected` は proposal からではなく、封印済み publication の registry 行にある `initial_proposal_sha256` から取得される。[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:394)
- `observed` は proposal の parse 結果を `canonical_json_bytes` に渡して別途再導出される。[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:455)
- 両者の不一致は無条件に拒否される。同値時だけ通る。[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:456)
- publication load の例外は握り潰さず `B4ProtocolError` として再送出する。[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:444)
- bootstrap では binding が無い場合も共通関数を必ず呼ぶため、`if binding is not None` 型の素通しはない。base は 2183、sort は 493、trigger は 973。
- closed schema は proposal の形だけを制限し、registry hash を含意しない。registry 側は hash の形式だけを検査する。[p3_b4_analysis_ledgers.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_b4_analysis_ledgers.py:339)

不一致入力列は次のように構成できる。根拠は読解。

1. schema-valid な `variant=20` の document の canonical hash を持つ publication を封印する。[p3_b4_proposal_binding_support.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/p3_b4_proposal_binding_support.py:61)
2. 同じ publication root と同じ attempt ID を固定する。
3. proposal file だけを schema-valid な `variant=21` に差し替える。[test_p3_b4_proposal_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_b4_proposal_binding.py:93)
4. 3 loader とも `canonical hash differs` で拒否する。base/sort では整数・implementation、trigger では wire が変わるため、canonical hash は実際に異なる。

再現対象 node:

`orchestrator/tests/test_p3_b4_proposal_binding.py::test_same_publication_and_attempt_reject_schema_valid_proposal_mutation[base]`

同じ node の `[sort]`、`[trigger]` も同型である。

A1 (nit): canonical 化失敗時の例外適配が壊れており、新規 baseline test が赤になる。

- `attempt_registry_core.canonical_json_bytes` は `TypeError` / `ValueError` を `AttemptRegistryCoreError` に変換する。[attempt_registry_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/attempt_registry_core.py:197)
- 呼出側は変換前の例外型しか捕捉しない。[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:385)
- そのため [test_p3_b4_proposal_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_b4_proposal_binding.py:61) が期待する `B4ProtocolError` にならない。
- 再現、実走:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -c \
'from orchestrator.campaign import p3_s4_loop as L
try:
 L.canonical_b4_proposal_sha256({"value": float("nan")})
except Exception as e:
 print(type(e).__module__ + "." + type(e).__name__)'
```

実出力は `orchestrator.campaign.attempt_registry_core.AttemptRegistryCoreError`。入力は引き続き拒否されるため、成果物の受理集合には影響しない。

## 段 4 裁定との適合 (逐条)

### §3.1 適用範囲

適合している。

- 3 loader とも `b4_reflux_ablation=True` かつ terminal receipt hash 不在のときだけ registry 照合を行う。
  - base: [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:2180)
  - sort: [p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop_sort.py:490)
  - trigger: [p3_s4_loop_trigger_gating.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop_trigger_gating.py:970)
- 正規 continuation は binding 引数を渡さず、terminal receipt だけを driver argv に載せる。[p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_b4_launcher.py:207)
- continuation に binding 引数が混入した場合は launcher、driver main、loader の各境界で拒否する。
- binding 引数なしの既存 continuation は canonical hash 比較へ入らない。既存の receipt 検証経路は保持される。
- 非 B-4 の既存入力も比較へ入らない。
- source projection の変化で旧 campaign lock が drift 拒否され得る点は段 4 §2 で既に採用された既知の波及であり、continuation proposal を registry と比較する滲み出しではない。

### §3.2 照合位置と proposal file 読取り回数

適合している。

- base: receipt gate 2139–2159、closed schema 2160–2179、registry binding 2180–2189。
- sort: receipt gate 463–486、closed schema 487–489、binding 490–499。
- trigger: receipt gate 942–965、closed schema 966–969、binding 970–979。

proposal file の各 loader 当たりの動的読取り数:

| loader | `open` | `read_bytes` | `json.load` | `json.loads` |
|---|---:|---:|---:|---:|
| base | 1 | 0 | 0 | 1 |
| sort | 1 | 0 | 0 | 1 |
| trigger | 1 | 0 | 0 | 1 |

base には `json.loads` の代替分岐が二つ記述されているが、一回の呼出しで実行されるのは片方だけである。[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:2125)

launcher は proposal file を開かない。publication loader が receipt・registry・manifest を読む処理は proposal の再読取りではない。

### §3.3 canonical hash

A1 の例外適配を除き適合している。

- raw bytes ではなく、`json.loads` 後の dict を `attempt_registry_core.canonical_json_bytes` に渡す。[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:379)
- terminal receipt key は canonical document から除外される。
- `1` と `1.0` は serializer 上で区別される。
- key 順、空白、Unicode escape の表記差は canonical 化で消える。

### §3.4 行選択

適合している。

- `attempt_id` exact match を列挙し、件数が 1 でなければ拒否する。[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:405)
- 選択後に registry 行の `driver` と実 driver を比較する。[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:417)
- `expected` はその行の `initial_proposal_sha256` である。

### §3.5 fail-closed

6 項目すべて拒否される。

1. binding 欠落、片方だけ、空文字: 共通関数 438–441、および各 driver main の引数 gate。
2. 相対 root、不在、publication load 失敗: issuer の absolute path gate と、共通関数 444–449。
3. attempt 不在・複数: 405–416。封印済み loader 自体も重複 ID を先に拒否する。
4. 登録 hash が 64 lowercase hex でない: 422–426。publication loader も上流で拒否する。
5. driver 不一致: 417–421。
6. canonical hash 不一致: 455–459。

continuation と非 B-4 への binding 引数も、launcher [p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_b4_launcher.py:685) と3 driver mainで拒否される。

## 実行前性

指定された5種類の campaign 実行作用には、不一致拒否前に到達しない。根拠は読解。

- base: proposal load・照合は 2619–2629、worktree 進入と `drive_iteration` は 2633–2646。[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:2619)
- sort: 照合は 781–787、worktree 進入と drive は 791–801。[p3_s4_loop_sort.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop_sort.py:781)
- trigger: 照合は 1332–1338、worktree 進入と drive は 1342–1354。[p3_s4_loop_trigger_gating.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop_trigger_gating.py:1332)
- `patchharness.checkout` は context manager 本体への進入時に初めて一時 directory と git worktree を作る。[patchharness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/patchharness.py:345)
- campaign lock と WAL recovery は drive 内の `ensure_resumable_attempts` より後:
  - base 2330
  - sort 595
  - trigger 1114
- `run_campaign` も各 drive のさらに下流にあるため、loader 不一致から到達不能。
- build と WAL append も同様に drive/run path の下流である。

新規 test は `drive_iteration`、campaign lock、WAL、build、`run_campaign` を spy 化している。[test_p3_b4_proposal_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_b4_proposal_binding.py:324) ただし pytest は未実走なので、これは読解上の補強に留める。

launcher が照合前に sidecar と campaign directory を作る経路は実在する。[p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_b4_launcher.py:552) これは段 4 が明示的に非保証へ落とした作用であり、campaign lock・WAL・build・`run_campaign`・実 worktree 操作ではない。

## 変異の帰属と期待 node

| ID | 判定 | 期待 node |
|---|---|---|
| M01 | 単一理由で kill | `orchestrator/tests/test_p3_b4_proposal_binding.py::test_same_publication_and_attempt_reject_schema_valid_proposal_mutation[base]` |
| M02 | 単一理由で kill | M01 と同じ node |
| M03 | 単一理由で kill。driver main の guard 除去で preflight spy に到達 | `orchestrator/tests/test_p3_b4_proposal_binding.py::test_driver_main_requires_binding_and_rejects_it_outside_bootstrap[base]`、同 `[sort]`、`[trigger]` |
| M04 | A2。変異位置の再登録が必要 | `orchestrator/tests/test_p3_b4_proposal_binding.py::test_launcher_cli_requires_bootstrap_binding_and_rejects_continuation_binding` |
| M05 | A3。現在の入力では期待した受理集合変化を検出しない | `orchestrator/tests/test_p3_b4_proposal_binding.py::test_unknown_duplicate_invalid_hash_and_driver_mismatch_reject` |
| M06 | 単一理由で kill | `orchestrator/tests/test_p3_b4_proposal_binding.py::test_matching_bootstrap_accepts_reordered_spaced_unicode_spelling[base]`、同 `[sort]`、`[trigger]` |
| M07 | 単一理由で kill。drive spy が先行到達を検出 | `orchestrator/tests/test_p3_b4_proposal_binding.py::test_mismatch_is_single_read_and_precedes_all_campaign_effects[base]`、同 `[sort]`、`[trigger]` |
| M08 | 単一理由で kill | `orchestrator/tests/test_p3_b4_proposal_binding.py::test_unknown_duplicate_invalid_hash_and_driver_mismatch_reject` |
| M09 | 単一理由で kill | `orchestrator/tests/test_p3_b4_proposal_binding.py::test_bootstrap_binding_missing_halves_empty_values_and_load_failure_reject` |
| M10 | 単一理由で kill | `orchestrator/tests/test_p3_b4_proposal_binding.py::test_same_publication_and_attempt_reject_schema_valid_proposal_mutation[sort]` |
| M11 | 単一理由で kill | `orchestrator/tests/test_p3_b4_proposal_binding.py::test_same_publication_and_attempt_reject_schema_valid_proposal_mutation[trigger]` |
| M12 | A4。base の広い既存 node は候補だが、3 driver の直接正例が不足 | `orchestrator/tests/test_p3_b4_closed_critic.py::test_public_b4_receipt_gate_accepts_live_certified_bound_receipt` |
| M13 | 正例として適合 | `orchestrator/tests/test_p3_b4_proposal_binding.py::test_matching_bootstrap_accepts_reordered_spaced_unicode_spelling[base]`、同 `[sort]`、`[trigger]` |

A2 (nit): M04 の事前登録位置 `argparse required=True` は実装に存在しない。

- launcher の2引数は optional として宣言され、bootstrap 分岐の手動条件で必須化されている。[p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_b4_launcher.py:664)
- これは continuation では引数を拒否する必要があるため、実装挙動自体は裁定に適合する。
- 再現、読解: `required=True` を検索すると新規2引数には存在しない。M04 を 670–676 の条件削除へ再登録し、上表の launcher CLI node へ再照準すべきである。

A3 (nit): M05 の現 fixture は driver 検査除去による誤受理を作れていない。

- 現 test は base document の hash を登録した publication を sort loader に渡す。[test_p3_b4_proposal_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_b4_proposal_binding.py:201)
- 再現、読解: driver 検査 418–421 を除去しても、base document hash と sort document hash が異なるため、456 の canonical mismatch が次に拒否する。node は message regex の違いで赤になるだけで、M05 の期待理由「別 driver 行で通る」を証明しない。
- 同じ実 nodeへ、`driver="base"` だが `initial_proposal_sha256=H(sort proposal)` の封印済み行を渡す入力に再照準すべきである。現実装なら driver 不一致だけで拒否し、M05 mutant なら hash が一致して受理される。

A4 (nit): M12 の3 driver 単位の直接正例が不足している。

- 新規 parameterized node は「continuation に binding 引数を渡すと拒否」だけを検査し、binding 引数なしの continuation が比較されないことを確認しない。[test_p3_b4_proposal_binding.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_b4_proposal_binding.py:285)
- base には既存の広い正例があるが、sort/trigger への片肺 mutant を帰属できない。
- 再現、読解: continuation document と receipt hash を与え、binding 引数を省略して各 loader を呼ぶ経路が新規 test にない。
- `orchestrator/tests/test_p3_b4_proposal_binding.py::test_continuation_and_non_b4_reject_bootstrap_binding_arguments[base]`、同 `[sort]`、`[trigger]` を、拒否例の前に「binding 無し continuation は受理」を確認する node へ再照準するのが最短である。

projection closure、schema、receipt gate、argparse が M01/M02/M06/M07/M08/M09/M10/M11/M13 より先に赤を出す入力は見つからない。各対象入力はそれらの上流 gate を通る形になっている。

## 非保証の記載

欠落なし。段 4 §7 の7項は [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:171) の `B4_PROPOSAL_BINDING_NON_GUARANTEES` に逐語で収録されている。

1. continuation proposal は内容束縛されない。
2. publication の権威は強制されない。
3. manifest membership は検査しない。
4. 成功は耐久証拠に残らない。
5. raw bytes ではなく parse 結果を束縛する。
6. pgrep、Git pin、sidecar、campaign directory が先行し得る。
7. `1` と `1.0` を別提案として扱う。

commit の変更対象9 file に `p3_b4_prerun_issuer.py`、raw producer、material report、receipt schema は含まれない。既存の `B4_PRERUN_NON_GUARANTEES` も変更されておらず、凍結 schema 違反はない。

## must-fix 一覧

なし。

A1〜A4 はいずれも nit である。A1 は拒否例外型と baseline test の問題であり受理は fail-closed のまま、A2〜A4 は変異の位置・帰属・node 照準の問題で、現 production の成果物値・受理集合・参照を変えない。

## 総括

production の proposal binding は恒真ではなく、固定した publication root・attempt ID に対する schema-valid な不一致 proposal を3 driverすべてで拒否できる。bootstrap 限定、receipt/schema 後、canonical parse hash、exact 1 行と driver 照合、実行作用前の拒否も段 4 裁定に適合している。continuation proposal を registry と比較する滲み出しは見つからなかった。

must-fix は0件。nit は4件で、うち1件は実走で確認した baseline test の例外型不一致、3件は M04/M05/M12 の変異帰属である。pytest は実走していない。ファイル編集・commit は行っていない。