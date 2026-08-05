| 所見 | 判定 | 静的根拠 |
|---|---|---|
| RA-1 | **closed** | partition 存在区間を検査している。[ledger.py:1976](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1976)、正負例 [test:2653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2653) |
| RA-2 | **closed** | origin ごとの head transaction 寄与と共有 genesis を authority 全体で合算。[ledger.py:1537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1537)、2-origin 境界 [test:2671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2671) |
| RA-3 | **closed** | batch ごとに cardinality の最大追加 3 桁を予約し、origin-total を拒否。[ledger.py:1923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1923)、[ledger.py:2054](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:2054)、境界 [test:2693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2693) |
| RA-4 | **closed** | 2248/2249 を commit 経路で通している。[ledger.py:1087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1087)、[test:2718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2718) |
| RA-5 | **closed** | 旧型・union 要素不在と raw `"batch-tombstoned"` 拒否を固定。[ledger.py:958](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:958)、[test:658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:658) |
| RA-6 | **partial** | 再照準用 assertion は増えたが、M-9′・M-22 は依然 false-kill、M-16′・M-23〜25 は exact anchor 不在で単一理由性未確立。[ledger.py:1186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1186)、[test:2452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2452) |
| RA-7 | **closed** | nodeid が row proxy / not physical query を明記。[test:2174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2174) |
| RB-1 | **closed** | RA-1 と同じ構築的 partition 検査・正負例で閉鎖。[ledger.py:1979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1979)、[test:2655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2655) |
| RB-2 | **closed** | 合法 3・不正 9 の 12 セルを encode/decode/reducer に適用。[ledger.py:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:646)、[test:2381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2381) |
| RB-3 | **closed** | V02/V14/V17/V19 を実際の event 数・row-proxy 境界へ改名。[test:658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:658)、[test:1610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:1610)、[test:2509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2509) |

元所見の集計は、fix 子の申告どおり **closed 9 / partial 1 / regressed 0**。ただし RA-6 の partial は「本走待ち」だけではなく、以下の静的な単一理由性不成立を含む。

以下の「失敗」は仮想変異時の静的到達予測であり、pytest・変異の実測結果ではない。

## 新規所見

### RF-1 / major — M-9′ は三層目の `zip(strict=True)` に遮られる

file:line: [ledger.py:1186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1186)、[ledger.py:1207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1207)、[ledger.py:1301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1301)、[test:2452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2452)

成果物影響: 変異台帳が partial-opening 防壁を KILLED と記録し、proof chain が存在しない耐性を参照する。

失敗シナリオ: 明示 cardinality 検査と query partition 検査を同時に除去しても、2 prepared 対 1 opening の `zip(..., strict=True)` が `ValueError` を送出する。V18 は `RefluxOriginLedgerError` を要求するため node は失敗するが、mutant は opening を受理していない。

最小の是正案: M-9′を三層同時変異（明示長検査、strict zip、partition 検査）へ再登録するか、現行二層変異を KILLED ではなく diagnostic pin に降格する。

### RF-2 / major — M-22 は実 replay では後段に mask される

file:line: [ledger.py:958](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:958)、[ledger.py:2170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:2170)、[test:666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:666)

成果物影響: legacy tombstone の再導入耐性が、実際には event chain を通過しない中間 parser 変異で水増しされる。

失敗シナリオ: 最終 `_fail("unknown event type")` だけを除くと direct helper は `None` を返すため V02 は失敗する。一方、非 genesis replay は直後の `_event_payload(None)` で `"unsupported origin event"` となり、同じ legacy frame は依然拒否される。

最小の是正案: 型・union・parser・reducer を含む旧経路全体を再導入して replay まで受理する変異へ照準する。そうしないなら M-22 は diagnostic sensitivity pin とする。

### RF-3 / major — M-16′ の node は shape pin で、accepted replay を証明しない

file:line: [test:2537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2537)、[ledger.py:669](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:669)、[ledger.py:805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:805)

成果物影響: pre-seal ordinal 漏洩への耐性を、単なる dataclass/key 形状不一致による kill と誤記録できる。

失敗シナリオ: V20 は field/key の存在だけで失敗する。codec/parser/replay を同時更新していない mutant でも同じ node が失敗するため、「実 ordinal を載せ、replay まで受理」の成立をこの nodeid だけでは示せない。

最小の是正案: code-only の end-to-end mutant と、mutant 上で replay が ordinal 以外の理由では拒否されない positive route を anchor 時に固定する。作れなければ diagnostic pin に降格する。

### RF-4 / major — M-23〜M-25 は exact replacement 未確定では単一セル変異にならない

file:line: [ledger.py:635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:635)、[ledger.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:660)、[ledger.py:1243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1243)、[test:2383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2383)

成果物影響: outcome-matrix の kill を別セルの拡大や後段 commitment mismatch に誤帰属し、mutation ledger の理由が一意でなくなる。

失敗シナリオ:

- M-23/M-25 で constraint 拒否行だけを削ると、値は `None` に正規化され、reducer は matching fixture の digest と不一致になって後段で拒否する。
- M-24 で共通 evidence 必須行を削ると、rejected だけでなく accepted-no-evidence も同時に通り、登録セルより先の assertion が失敗する。
- M-25 の単純削除は accepted と tombstoned の両セルへ作用する。

最小の是正案: 対象 outcome だけを許し、与えられた digest を保持し、他の合法・不正セルを変えない exact replacement を事前登録する。各 targeted cell を独立 test に分けると失敗理由も固定できる。

## 新規検査の発火性

| Fix | 検査行を壊した場合の静的 oracle | 判定 |
|---|---|---|
| F1 | 到達不能 fixture の `Raises("floor cannot be partitioned")`。[test:2662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2662) | 恒真ではない |
| F2 | 2-origin overflow の `Raises("shared runtime head")`。[test:2688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2688) | 恒真ではない |
| F3 | production affine 値の直接一致と overflow authority 拒否。[test:2697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2697)、[test:2713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2713) | 恒真ではない |
| F4 | 2248 の receipt/snapshot assertion と 2249 の `Raises`。[test:2734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2734) | 恒真ではない |
| F5 | 型・union 不在 assertion と raw unknown-event `Raises`。[test:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:660) | 恒真ではない。ただし M-22 の kill 帰属は RF-2 |
| F8 | 各不正セルについて encode/decode/reducer の `Raises`、合法セルは `state.phase == "IDLE"`。[test:2411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2411) | 恒真ではない |

F1〜F5/F8 自体に恒真候補はない。

## `DW-M01` assertion 照合

| 変異 | assertion 単位の静的判定 |
|---|---|
| M-9′ | **不成立**。V18 は失敗するが残存 `zip(strict=True)` が理由。 |
| M-10′ | **成立**。unknown outcome の最初の codec `Raises` が失敗し、fixture は matching result commitment を持つ。 |
| M-14′ | **成立**。sealed=0 / tombstoned=4、全 counter 一致なので floor 以外の拒否なし。 |
| M-16′ | **未確立**。field/payload absence は観測するが replay-capable mutant の証拠ではない。 |
| M-18a | **成立**。V22 の正例 `_manifest(...)` が単一-batch Qmax 退行による過剰拒否を観測する。 |
| M-18b | **成立**。2249 fixture は cardinality guard 以外を満たし、committed frame 自体は record ceiling 内。 |
| M-18c | **成立**。73,749 fixture は origin-total だけが超過し、head・partition・Kmax は合法。 |
| M-19 | **成立**。V22 負例は partition 存在検査だけが拒否理由。 |
| M-20 | **成立**。両 manifest は個別 head 上限内で、authority aggregate だけが拒否理由。 |
| M-21 | **成立**。旧 affine は cardinality 10 で 11,191 となり、期待 11,194 の直接 assertion が観測する。 |
| M-22 | **不成立**。direct parser は観測するが、実 replay は後段で拒否。 |
| M-23 | **未確立**。対象 constraint を保持する outcome-specific anchor なら成立可能。単純削除は後段 mismatch。 |
| M-24 | **未確立**。rejected だけを緩める条件書換えなら成立可能。共通行削除は accepted も同時に変える。 |
| M-25 | **未確立**。tombstoned だけを許し digest を保持する anchor が必要。 |

## 数値の独立再計算

production/test helper を import せず、wire の key・値長から再構成した。

- F1: `C=2248`, `F=2249` なので必要 batch 数は `ceil(2249/2248)=2`。
  - `batch_min=1124`: `min(imax=2, floor(2249/1124)=2)=2`、存在する。
  - `batch_min=2248`: 最大 batch 数は `1`、存在しない。

- F2: head prepared は 1,064 bytes、committed は 745 bytes、pair は 1,809 bytes、2-origin genesis は 760 bytes。
  - `760 + 2×(3×6182+1)×1809 = 67,103,806`
  - 一方だけ 6183 batch: `67,103,806 + 3×1809 = 67,109,233`
  - ceiling `64<<20 = 67,108,864`

- F3: rejected 三 frame の exact 式は  
  `E(n) = 2101 + 909n + (digits(n)-1)`。
  - `E(10)=11,192`
  - `E(100)=93,003`
  - `E(1000)=911,104`

  保守上界は各 batch に追加 3 bytes を予約する。33 batch、origin genesis + class frame = 1,624 bytes より:
  - `909×73,748 + 2,104×33 + 1,624 = 67,107,988`
  - 1 member 増は `+909`、したがって `67,108,897`
  - 旧 affine は 33×3=99 bytes 少なく、overflow 側は `67,108,798`

すべて申告 literal と一致する。

## 回帰と期待値改変

fix-only 差分を段5退避済み [s5-snapshot.patch:2260](/work/1/SFC/tanab/dev-wave-jobs/t244-p4-batch-freeze/s5-snapshot.patch:2260) と比較した結果:

- 既存期待 literal の変更、skip/xfail 化はない。
- V18 の旧4負例 loop は削除されたが、現在の12セル matrixと unknown blockへ包含され、decode 検査も追加されている。緩和ではない。
- V02/V14/V17/V19 は関数名だけの変更。
- staged 全差分では v1→v2 golden literal の変更が見えるが、これは段5 snapshotに既に存在し、今回の fix による書換えではない。

fix-only の production 変更は feasibility/accounting 部分に限定されている。次の既存保証に静的後退はない。

- seal 前の結果非公開: [ledger.py:1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1027)、[ledger.py:2687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:2687)
- salt の origin-wide 再利用拒否: [ledger.py:1201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1201)
- exact rejected class: [ledger.py:1327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1327)
- wire 正準性: [ledger.py:1047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1047)
- 単一 in-flight: [ledger.py:1078](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1078)
- tombstone no-refund: [ledger.py:1118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1118)、[ledger.py:1295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1295)
- pre-seal projection から counter / replicate ordinal を除外: [ledger.py:1030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_origin_ledger.py:1030)、[test:2539](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_reflux_origin_ledger.py:2539)

## 総括

**NO-GO**。

F1〜F5/F8 の production fix、境界 literal、元所見 9件の閉鎖、既存保証の非後退は静的に確認できた。一方、RA-6 の根は閉じていない。特に M-9′とM-22は現在の登録どおりでは false kill、M-16′とM-23〜M-25は exact anchor が決まるまで `DW-M01` の単一理由性を主張できない。

親は変異本走前に、M-9′の三層化、M-22の実 replay 変異への再照準、M-16′/M-23〜25の outcome-specific end-to-end anchor を確定すべきである。その後、計算ノードで対象 node・meta-test・変異 matrixを実測する必要がある。今回は pytest・変異とも実走していない。