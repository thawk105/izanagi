| 所見 | 判定 | 現物による理由 |
|---|---|---|
| R1 MF-1 — D の恒真化 | **partial** | `_CRITIC_D_SELECTORS` だけが除去を駆動し、未知 selector は fail-closed、reason/evidence の無条件除去も消えた（[test_p3_autonomous_workload_trial.py:1065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:1065)）。ただし relation fixture は evidence を固定値で直書きし、実 producer の候補依存 `sha256_12` を通さない。 |
| R1 MF-2 — ABORT WAL の偽 certified/dry-pass | **regressed** | ABORT fixture の一部は `rejected` へ直ったが、別 fixture が依然 `certified`・`variant=None`・COMMITなし・有限 metrics・`critic_digest_generated=True` を返す（[test_p3_autonomous_workload_trial.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:171)）。さらに既存 certified/dry-pass 経路を rejected fixture へ差し替えて被覆を後退させた。 |
| R1 MF-3 — raw WAL projector | **closed** | factory は exact `AdmittedCampaign` のみを受け、digest は同一 view identity を要求する（[p3_s4_loop.py:364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:364)、[同:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:438)）。 |
| R1 MF-4 — CLI 二重ロード＋diff 欠落 | **partial** | nominal type は中立 module 化で閉じた。CLI は今も `load_diff_rejections(view)` を renderer へ渡さない（[digest.py:752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:752)）。 |
| R1 MF-5 — role payload を同じ v2 で変更 | **closed** | role schema は v3 へ上がり、critic payload/harness の exact key-set も固定された（[p3_autonomous_workload_trial.py:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:143)）。report 側の問題は R2 MF-2 に残る。 |
| R1 SF-1 — autonomous/RAW を漏らす caller 検査 | **closed** | autonomous を含む現存全 caller を列挙し、RAW と projector/tag/reflux 省略を拒否する（[test_p3_s4_loop.py:940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_s4_loop.py:940)）。 |
| R1 SF-2 — import-time source read | **closed** | production は生成済み literal のみを読み、source/golden 再導出は test 側へ移った（[reflux_ir.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_ir.py:20)）。 |
| R1 SF-3 — synthetic provenance の workload 流用 | **closed** | 閉じた `origin_kind` を heading に必須表示し、未知値も拒否する（[digest.py:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:594)）。 |
| R2 MF-1 — CLI nominal type | **closed** | 中立 `identity_projection.py` と直接 subprocess 回帰がある（[test_critic.py:805](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_critic.py:805)）。 |
| R2 MF-2 — v2 report／reader fail-open | **partial** | role は v3 だが report は v2 のまま。`declassifications` は report/journal に増えたのに completeness の必須 field・型・policy・role 制約へ入っていない（[autonomous_trial_completeness.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/autonomous_trial_completeness.py:183)）。旧 v2 legacy branch もない。 |
| R2 MF-3 — pseudonym を `variant=` 表示 | **closed** | verify/liveness/diff/abort の全経路が `candidate_label=` になった（[digest.py:596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:596)）。 |
| R2 MF-4 — M11/M12/M15 帰属 | **partial** | M11・M12 は原子化された。全19 anchor も一意。ただし M13 の説明は sentinel 裁定後に stale、M15 は checkout detector pin であり artifact 受理集合には接続しない。 |
| R2 SF-5 — 未知 ID による受理集合縮小 | **closed** | 非空未知値は候補非依存の固定 `candidate-unregistered`／固定 suffix へ落ちる。生値 fallback はなく、custom drive は complete のまま（[p3_s4_loop.py:298](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_s4_loop.py:298)、[p3_autonomous_workload_trial.py:1764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1764)）。 |
| R2 SF-6 — repo 全体 consumer 検査 | **partial** | 現存 caller は全件入ったが、検査対象は依然 hard-coded 6 path。新しい production file の caller は自動発見されない。 |
| R2 SF-7 — docs 追随 | **partial** | docs 差分はゼロ。projector、`candidate_label`、schema v3/report v2、sentinel、残余境界が runbook／decision に未反映。 |
| R2 nit-8 — IR detector 名 | **closed** | `CHECKOUT_IR_EMITTER_GOLDEN_REGRESSION_ID` へ改名され、artifact identity ではない旨も明記された（[reflux_ir.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/reflux_ir.py:20)）。 |

### 変異 19 件の静的判定

全 anchor は指定 production file 内で **1/1**。以下の KILL は静的到達判定であり、実走結果ではない。

| 変異 | anchor | 指定 node の静的判定 |
|---|---|---|
| M1 | `"candidate_label": candidate_label,` | **成立**。raw へ戻すと relation test の `raw_variant != candidate_label` が直接落ちる（[test:1178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:1178)）。 |
| M2 | `identity_projection.project_variant(rj.variant)` | **成立**（[test:670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_critic.py:670)）。 |
| M3 | `rj.variant, rj.src_token,` | **成立**（[test:679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_critic.py:679)）。 |
| M4 | `identity_projection.project_variant(lv.variant)` | **成立**（[test:688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_critic.py:688)）。 |
| M5 | `lv.variant, lv.src_token,` | **成立**（[test:697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_critic.py:697)）。 |
| M6 | `identity_projection.project_build_attempt_id(` | **成立**（[test:706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_critic.py:706)）。 |
| M7 | `identity_projection.project_build_admission_receipt_sha256(` | **成立**（[test:718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_critic.py:718)）。 |
| M8 | `identity_projection.project_variant(dq.variant)` | **成立**（[test:732](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_critic.py:732)）。 |
| M9 | `dq.variant, dq.src_token,` | **成立**（[test:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_critic.py:742)）。 |
| M10 | `else f"candidate_label={identity_projection.project_variant(s.variant)}"` | **成立**（[test:752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_critic.py:752)）。 |
| M11a | `*, identity_projection: IdentityProjection,` | **成立**。既定 RAW 化すると省略時の `pytest.raises` が落ちる（[test:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_critic.py:827)）。 |
| M11b | `identity_projection: IdentityProjection) -> str:` | **成立**（[test:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_s4_loop.py:877)）。 |
| M12a | `tag=CRITIC_TAG,` | **成立（構文 pin）**（[test:1024](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_s4_loop.py:1024)）。 |
| M12b | trigger の `reflux=(cfg...=="on"),` | **成立（構文 pin）**（[test:1030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_s4_loop.py:1030)）。 |
| M12c | `tag=trigger.CRITIC_TAG,` | **成立（構文 pin）**（[test:1037](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_s4_loop.py:1037)）。 |
| M12d | autonomous の `reflux=(cfg...=="on"),` | **成立（構文 pin）**（[test:1048](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_s4_loop.py:1048)）。 |
| M13 | `return mapping[raw]` | node は **KILL** する（[test:836](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_s4_loop.py:836)）。ただし現 baseline は未知 ID を拒否しないため、「未知だけ拒否→全拒否」という事前登録説明との帰属は不成立。 |
| M14 | `"forbidden_json_pointers": ["/diff_digest"],` | **成立**。ただし予定どおり diagnostic sensitivity pin のみ（[test:958](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:958)）。 |
| M15 | `_CHECKOUT_IR_GOLDEN_32_ROWS_SHA256 = (` | 指定 node は **KILL** する（[test:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_reflux_ir.py:315)）。golden term への帰属は成立するが、artifact 受理集合への帰属は不成立。 |

M1について、`test_critic_relation_oracle_detects_candidate_derived_evidence_leak` は二 payload の相違を evidence だけに限定しており、evidence 非除外の負例としては帰属している。ただし `DiffQuarantineRejection.variant` は空のため、同テスト自身は「projection を外す」負例ではない。projection 除去は M1 の main relation test が別途直接検出する。

### 名乗り

最終差分のコード・追加コメント・識別子・test docstring に、origin-scope ID、non-interference／indistinguishability、P2 充足、cap-lift、build 閉鎖、proof-chain 保全、U-1〜U-3 完了の新規名乗りはない。使用しているのは上限内の campaign-local label、critic relation regression、自己申告 annotation、checkout regression detector である。

### must-fix

1. **R1 MF-1: oracle は強化されたが、実 evidence producer を避けている。** Relation helper は `DiffQuarantineResult(... evidence="fixture evidence")` を直書きする（[test:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:119)）。実 producer は候補行の byte length と `sha256_12` を evidence に載せ（[diff_quarantine.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/diff_quarantine.py:319)）、renderer はそのまま描画する（[digest.py:686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/critic/digest.py:686)）。32点の閉じた候補集合では短縮 hash も逆引き可能な候補チャネルである。  
   **成果物影響:** 候補依存 evidence により critic payload／`input_payload_sha256`／critic 応答／次候補が変わり、certified 選択と report・journal・receipt 参照が候補 wire に依存する。

2. **R1 MF-2: outcome↔WAL terminal 不整合を fixture 移動で隠している。** `_fake_drive_with_finite_metrics` は COMMITなしで `certified` と有限 throughput を発行し、variant/digest だけを `None` にした。production は required field と stop reason しか検査せず（[p3_autonomous_workload_trial.py:1715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/campaign/p3_autonomous_workload_trial.py:1715)）、WAL terminal と照合しない。加えて既存 build test は `certified→rejected`（[test:1661](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:1661)）、public-entry fixture は `dry-pass→rejected`（[test:1930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:1930)）へ書き換えられ、正例被覆が消えた。  
   **成果物影響:** WAL に存在しない certified と有限 fitness が critic・材料レポート・試行台帳へ入り、certified 選択と receipt の参照先が WAL と矛盾する。

3. **R1 MF-4: CLI は diff-quarantine を今も捨てる。** 追加 subprocess test は exit 0 と見出ししか検査せず、diff-only campaign／「全 variant 緑」反転を固定していない。  
   **成果物影響:** hard reject が critic digest から消え、critic の次手と後続 certified 選択が変わり、材料レポートが rejection を欠落させる。

4. **R2 MF-2: report v2 と formal reader が fail-open のまま。** `declassifications` の欠落・任意型・偽 policy・非 auditor 値を completeness が受理する一方、旧 role v2 は producer 現行値との単純比較で拒否される。  
   **成果物影響:** 同じ report v2 の下で意味の異なる report が formal receipt を取得し、既存 v2 trial の受理集合も縮み、試行台帳の report/journal hash が比較不能になる。

5. **R2 MF-4: M13/M15 を現説明のまま mutation 証拠に数えられない。** M13 は sentinel 裁定後の operator へ再事前登録が必要。M15 は明示的に artifact 搭載禁止・production consumer 0 であり、checkout detector の diagnostic mutation へ降格すべきである。  
   **成果物影響:** 材料レポート／mutation 台帳が、存在しない artifact acceptance guard を kill 済み根拠として参照する。

### should-fix

1. **R2 SF-6:** current caller の棚卸し自体は合っているが、`production_paths` が固定リストである。ディレクトリ探索または import graph 由来の収集にしない限り、「repo 全体」は将来の新規 caller を検出しない。

2. **R2 SF-7:** docs は未追随。[axis-onboarding.md:295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/axis-onboarding.md:295) は projector 必須を欠き、[phase3-s8c-autonomous-trial-runbook.md:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/phase3-s8c-autonomous-trial-runbook.md:27) は v3／sentinel／declassification を記さず、[decisions.md:8138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/docs/decisions.md:8138) は旧 `harness_result.variant` 契約のままである。

### nit

- `critic_digest:rejection-count` は数値 field を pop するだけで、`rejections` list の要素数が残るため実際には count を declassify していない（[test:1126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p2-noninterference/orchestrator/tests/test_p3_autonomous_workload_trial.py:1126)）。これは false-green ではなく過剰な赤なので nit。

## 総括

- **NO-GO。**
- 最大理由は、D comparator の恒真化だけを直し、実 candidate-dependent evidence producer を relation fixture から外したこと。
- outcome と admitted WAL terminal の照合は依然なく、偽 `certified` fixture が別形で残る。
- certified／dry-pass の既存経路を rejected fixture へ書き換えたため、検査被覆も後退した。
- critic CLI は diff-quarantine rejection を落とす。
- report v2 reader は `declassifications` を検証せず、旧 role v2 の互換 branch もない。
- 固定 sentinel は候補非依存で、生値 fallback もなく、この裁定変更自体に新しい漏洩は見つからない。
- 19 anchor は全件一意だが、M13 の説明と M15 の受理集合帰属は成立しない。
- 名乗り上限の超過は見つからない。
- pytest は実行しておらず、親の 615 passed / 0 failed を本レビューから緑とは主張しない。