静的判定は **NO-GO** です。pytest・plain runner・変異本走は実行していません。

## 所見

### RB-1 / major / [reflux_origin_ledger.py:1932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1932)

**成果物影響:** feasibility を通った v2 authority が、宣言した floor を満たせる event 列を一つも持たない状態になり、W5 の構築的 feasibility という説明が偽になる。

失敗シナリオ: `imax=2, qmax=2249, batch_cardinality_min=2248, required_queries=2249` は、現在の二つの上界検査 `2249 <= 2*2248` を通る。しかし実際には、

- 1 batch では codec 上限 2248 を超える。
- 2 batch では最小 cardinality の合計が 4496 となり Qmax を超える。

したがって floor 2249 は到達不能である。さらに ledger byte 計算は `batch_count = 2249 // 2248 = 1` とし、存在不能な「2249-member の 1 batch」を affine 計算してしまう。[V21:2366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2366) の正例は `batch_min=2` だけなのでこの穴を覆わない。

最小の是正案: `b` batches について `b <= imax`、`b*batch_min <= qmax`、`b*MAX >= required_queries` を同時に満たす `b` の存在を検査する。上記の負例と、現行の `2249 = 1124+1125` 正例を対にして固定する。

### RB-2 / major / [test_reflux_origin_ledger.py:2150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2150)

**成果物影響:** W3 の三値 outcome matrix を広げる退行が V18 を通り得るため、テストが受理契約を完全には固定していない。

V18 が拒否する matrix 負例は、未知 outcome、accepted の evidence 欠落、tombstoned の evidence 付与、rejected の constraint 欠落だけである。次の不正セルが欠けている。

- accepted + constraint digest
- rejected + evidence 欠落
- tombstoned + constraint digest

例えば [実装の constraint 閉包:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:660) から accepted/tombstoned の constraint 拒否だけを外しても、現在の V18 は検出しない。tombstone に constraint を許すと、未実行 suffix から class 情報を開示できる。

なお既存の `Raises` は例外の実在と `RefluxOriginLedgerError` 型を検査しており、単なるメッセージ比較ではない。[test:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:47)

最小の是正案: 三つの合法セルと全不正セルを表形式で列挙し、encode/decode と reducer の双方へ同じ契約 oracle を当てる。少なくとも上記三負例を追加する。

### RB-3 / major / [s4-adjudication.md:76](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/out/s4-adjudication.md:76) / [test_reflux_origin_ledger.py:1987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:1987)

**成果物影響:** mutation ledger や test report が row proxy を物理 query accounting の証拠として誤読され、裁定済みの名乗り制限を失う。

実装 docstring は「evidence 付き sealed member row 数であり、物理 query の証明ではない」と正直である。一方、裁定が要求した「テスト名への明記」は履行されていない。

- `test_v17_...origin_query_accounting`
- `test_v14_independent_i_q_k_floor...`
- `test_v19_...origin_total_query_partition`

これらは synthetic event と任意 digest だけで進むテストなのに、名前からは物理 query receipt が存在するように読める。また [V02:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:486) の `six_event_transition_matrix` も、`BatchTombstoned` 削除後は対象 event が五つであり陳腐化している。

最小の是正案: nodeid に `sealed_evidence_row_proxy_not_physical_query` を明記し、任意 digest・物理 receipt 不在でも ledger seal まで進むことを「境界の実証」として独立 test にする。恒真な query 一対一検査は追加しない。V02 も実際の event 数へ改名する。

## W1〜W5 / Δ1〜Δ11 突合

| 項目 | 静的判定 |
|---|---|
| W1 | 裁定どおり ledger 内の第一級 batch FSM。production 結線は名乗っていない |
| W2 / Δ1・Δ2 | 適合。`replicate_counts` は seal 後も保持され、replay でも全 committed prefix から再構築される。V17 は batch 跨ぎ reset を拒否する |
| W3 | 実装は outcome と evidence digest claim の単一 commitment を照合する。ただしテスト閉包は RB-2 |
| W4 / Δ4 | 適合。全 batch terminal は committed→prepared→sealed、tombstone は固定 row suffix。byte 長は受容残余と明記 |
| W5 | authority injection と exact counter は ledger が担当し、referent 解決は consumer 義務と明記。ただし feasibility は RB-1 |
| Δ3 | `sealed_queries`、`tombstoned_queries`、`tombstone_count` は preseal projection から除外される |
| Δ5 | production 実装に `member_sequence_commitment` は存在しない |
| Δ6 | 数値と独立 oracle は妥当 |
| Δ7 | 32 lowercase hex・非ゼロ。31/33/34、非 hex、全ゼロの負例あり |
| Δ8 | per-batch と origin-total の単純上界は分離したが、厳密な分割可能性が不足（RB-1） |
| Δ9 | manifest/authority/event/head/runtime と registry path は v2。削除・追加とも staged |
| Δ10 | production docstring は適合、テスト名と境界の名乗りは不適合（RB-3） |
| Δ11 | digest claim・非 dereference・formal consumer 境界はコード上で明記されている |

P-1 は同一 wire を二 batch、replicate ordinal 0〜3 で `BatchSealed` まで進めている。[test:2006](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2006)  
P-2 は accepted + tombstoned suffix を実際に `BatchSealed` し、全三 event の row 数一致を確認している。[test:2217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2217)

## Consumer・削除面

静的検索では、対象実装・対象テスト・v2 registry 以外の `orchestrator/` に直接 caller、旧 constructor、旧 field、旧 authority path は 0 件だった。`tools/` と `hooks/` も 0 件。

- `conftest.py` に固有参照なし。
- plain-runner meta-testに対して対象テストは `_run()` と `__main__` を維持し、allowlist にも残っていない。
- real-repo serialization の canonical node 集合に本ファイル固有の consumer はない。
- docs の旧 path は [archive worklog:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/archive/worklog-phase3-0804-186.md:71) の歴史記録 1 件だけ。
- 旧 API 名が残る `mutation-spec.json`、`mutation-spec-runtime-v1.json`、`mutation-ledger-run1.json`、`mutation-ledger-run2.json` は P3 の凍結済み履歴で、live code から参照されていない。

v1 authority は空 registry、D159 は production caller ゼロを記録しているため、sanctioned な旧 event 履歴はない。[decisions.md:7900](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/decisions.md:7900) 新 runtime を `.../v2` に分離したため、v1 bytes を v2 として黙って replay することもない。外部で独自作成された v1 runtime の互換 reader は失われるが、追跡済み・production の保証ではない。

`member_sequence_commitment` の削除による順序保証の消失もない。ordered member list は event hash、prepared identity、seal 時の ordered zip で束縛されている。

## 数値の独立再計算

worst-case rejected member object は 465 bytes。二件目以降は区切りカンマ込みで 466 bytes増える。event wrapper は空 list 時 679 bytesなので、`n >= 1` では:

`frame(n) = 679 + 465n + (n-1) = 678 + 466n`

したがって、

- `n=2248`: `678 + 466×2248 = 1,048,246`
- `n=2249`: `1,048,246 + 466 = 1,048,712`
- ceiling: `2^20 = 1,048,576`

よって literal `2248` と両 byte 数は正しい。accepted/tombstoned row は digest が `null` になる分だけ短く、committed/prepared frame の per-member 増分も rejected seal より小さい。

## 総括

中核の危険は三点です。

1. 高い `batch_min` で到達不能な floor を authority admission が受理する。
2. V18 の三値 matrix が全不正セルを固定していない。
3. テスト名が row proxy を query accounting と呼び、Δ10 の名乗り制限を満たさない。

親はこれらの是正後、Δ12〜Δ14 の docs/handoff、staged rename、計算ノード上の対象 23 node・meta-test・M-1〜M-18 を確認すべきです。現時点ではテスト実測結果はありません。

**判定: NO-GO**