## 総括

**NO-GO：旧未commit記録の無修正回収には訂正が必要です。実装の静的監査では、新たなmust-fixは見つかりませんでした。**

監査HEADは `4dfc6ba8398df622ec27461003aa43b24a12b0ad`。`b2037abfa..HEAD` を確認しました。旧finalの成功は `e2b3cc483` の証拠として扱い、統合HEADの実走成功とは扱っていません。

## 所見表

| ID | 判定 | 所見・根拠 |
|---|---|---|
| REC-1 | **must-fix／記録** | 旧failures fragmentの恒久対応の判定根拠が、修正前のNO-GOレビューRR-1を指す。**実害：回収後の台帳から、親root読取り解消の根拠を辿ると未解消判定へ到達する。** [fragment:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/docs/spool/failures/2026-09-18-dev-wave-t2724-t080-defer-active-v2-2.md:15)。具体的反例：参照先`s6-rereview.md`は`8b8bb96f2`を対象とし、RB-6/F8をpartial、親root再読を残存と報告している。fix-4/5とその後の検査を解消根拠として区別して記録する必要がある。 |
| RR-1／RB-6／F8 | **closed（静的）** | selector roleをshared-base構築時に取り込み、receipt接続分岐はcalibration・selector材料の存在を先に要求する。通常fixtureの親root fallbackへ進まない。[emitter:1030](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2724-t2776-recovery/orchestrator/tests/test_s8b_ratified_freeze.py:1030)。欠落7ケースの負例もある。base構築自体の実root依存まで消えた、とは主張できない。 |
| T-2776切離し | **closed（静的）** | replayの削除集合はofficial namespaceと候補exact file。残存treeのmode/OID、候補の無関係な兄弟file、copy後bytesを検査。official／candidate／bothの実scan拒否と無害bytesの正例を保持している。 |
| consumer取り残し | **closed（調査範囲）** | memoは8関数／8nodeへ追随。旧consumer選択時のprewarm不発火、opt-out、constructor追加field、生成scriptを確認。残存memo経路はtokenなしの分岐であり、新keywordによる現行の呼出し破損は見つからない。 |
| RA-4／F4／RR-3 | **closed（旧tipの証拠）** | final A/Bのspec hash、記録node、格納stdoutのFAILED集合を照合。12変異すべて完全一致。現HEADでも各置換anchorは一意。 |
| RR-2 | **partial** | 通常受入の所要・base/copy費用は今回未実測。旧焦点走から統合後の所要を断定できない。 |
| RR-4 | **partial／記録訂正** | failures fragment:13はC3の`2 errors`を省略。一次summaryは **1088 passed / 2 errors / 2 failed / 7 skipped、INTERNALERRORあり**。接続8＋draft1という内訳は訂正済み。 |

## 変異証拠の実効性

両baselineは旧tipで **247 passed**。期待node数と観測数は次の全件で一致しました。

| 変異 | 一致node数 |
|---|---:|
| m1 / m2a / m2b / m3 | 2 / 1 / 1 / 11 |
| m4a / m4b / m5 / m6 | 2 / 2 / 6 / 1 |
| m7 / m8a / m9 / m10 | 2 / 7 / 1 / 1 |

m0はコメントだけの等価対照でSURVIVED、失敗nodeゼロです。

単一理由性について、m2aは不正R trailerで`allowed=True`、m2bはinvalidで`completed`、m5はreceipt変更後の`completed`到達を検出しています。m5の6nodeには呼出し回数だけの赤も含まれますが、`[changed]`が受理挙動の変化を独立に示しています。m8b・m11は最終specに含まれず、冗長gateや撤回済み再走査をkill証拠に数えていません。

## 未実走／残余

- **統合HEADのテスト・受入・変異は未実走。** 親の正規runnerでの検査が残ります。
- 同名fileの内容交換はcampaign-startの列挙digestでは検出しません。旧F1・decisionsに明記済みの残余であり、今回初めて判明した裁定前提違反ではありません。
- 旧insightの`README.md`は未作成でした。中断時点の未完了物として回収すべきです。
- 新たな未見の裁定前提違反は確認できませんでした。chain/X2/Gのland、実A/X発行、コード編集は行っていません。