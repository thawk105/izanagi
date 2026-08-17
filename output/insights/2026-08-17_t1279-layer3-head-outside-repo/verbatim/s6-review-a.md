## 総括

- must-fix は 3 件。現在 worktree の物理パスを official 判定に使う設計が受理集合を広げる。
- repo 外 campaign を直したとの主張に反し、CLI 経路は依然として repo 外入力を拒否する。
- M-4 の期待失敗 node 集合は、追加された E2E assertion を含まず不完全である。
- 「探索 campaign は必ず repo 外」は反証された。明示 root と env 未設定時は Git 配下になりうる。
- v2 authority の commit は decoder が lowercase hex40 に限定しており、空文字・非 hex の侵入はない。
- 決定論比較は当該 field を除外しており、同一 campaign の二回 build での一致には依存していない。
- pytest は実走していない。以下は差分、consumer、凍結 artifact を打切りなしで静的走査した結果である。

## must-fix

[重大] orchestrator/campaign/layer3_report.py:184 — `campaign_dir.is_relative_to(_DEFAULT_OUTPUT_ROOT.parent)` は「現在の source worktree の物理パス内か」しか判定せず、official/exploration の権威ある区別ではない。`_resolve_campaign_dir` は custom `output_root` を受理するため、別 linked worktree の `/tmp/wt2/output/campaigns/x`、外部 submodule/superproject、bind mount 上の official campaign は Git 障害時に repo 外と誤判定される。逆に source tree 内へ mount された別 repository は repo 内と誤判定される。symlink と `..` は line 393 の `resolve()` で正規化されるが、bind mount は正規化されない。この分岐は実質的な新しい path-based gate である — 修正しない場合、従来 `Layer3ReportError` だった official v2 入力が lock pin で受理され、`build_accepted_report` 経由では `certifying_input=true` の層3レポートまで生成可能になり、official 受理集合が広がる。

[高] orchestrator/campaign/layer3_report.py:682 — CLI は `output_root` を渡せず、repo 外 campaign は line 397 で helper 到達前に拒否される。明示 `--generated-from-head` を付けても同じであり、「全入口を覆う」「repo 外 campaign でも失敗しない」という brief の成果物条件を満たさない — 修正しない場合、CLI から repo 外 campaign の `layer3_report.json` を生成できず、手動検証経路では層3レポートとその後続参照が欠落する。

[中] /home/SFC/tanab/.claude/jobs/96db6009/tmp/t1279/s4-adjudication.md:70 — M-4 の期待失敗 node は unit test だけだが、変更後の `orchestrator/tests/test_p3_autonomous_workload_trial.py:2473` も lock commit との完全一致を検査するため必ず失敗する。hex64 は completeness を通り比較射影から除外されるが、最後の E2E assertion で落ちる — 修正しない場合、DW-M08 の完全集合比較で mutation ledger が不一致となり、この変異を正しく KILLED と認定できない。

## nit

[中] orchestrator/campaign/layout.py:293 — 明示 `output_root` は検査なしで返され、line 306 では env 未設定時に repo 既定へ戻る。さらに 8c は `p3_autonomous_workload_trial.py:2480` で引数なしの exploration layout を使うため、「探索 campaign は機械的に必ず repo 外」は偽である — 修正しない場合、Git-backed exploration campaign を HEAD 更新の前後で二回 build すると `meta.generated_from_head` が変わる。ただし completeness はこの field を除外するため certified 選択値には波及しない。

[低] orchestrator/campaign/layer3_report.py:164 — `_git_head` は `OSError` と `CalledProcessError` を変換するが、`text=True` の decode による `UnicodeDecodeError` は素通りし、helper も `Layer3ReportError` しか捕捉しない。`AttributeError` は不正な private-helper 直接呼出しや monkeypatch でのみ成立し、通常の public 経路では Path 化と exact dataclass decode により成立しない — 修正しない場合、異常な Git stdout では外部 campaign の fallback が働かず、build cell の層3レポートが生成されない。

[低] orchestrator/tests/test_layer3_report.py:1666 — repo 外 v2 test は計画に反して `_git_head` の失敗を固定していない。`tmp_path` の祖先が Git repository である実行環境では lock fallback ではなく ambient HEAD を取得し、無変異でも偽赤になる。E2E の `tmp_path` 配置も同型である — 修正しない場合、受入結果と mutation ledger が pytest の base directory に依存する。

## 調べたが問題なし

[確認] orchestrator/campaign/campaign_lock.py:167 — v2 authority は exact key 集合を要求し、`contract_loader_commit` は line 197 で lowercase hex40 に検証される。decode 済み authority が `None` でなく空文字・非 hex になる正規経路はない — 成果物影響: fallback 値の形式だけを理由に completeness の hex40/hex64 gate が緩むことはない。

[確認] orchestrator/campaign/autonomous_trial_completeness.py:2091 — persisted 値は hex40/hex64 を要求し、line 2139 で決定論比較から除外する。certifying admission、独立 admission decision、E1 epoch 検査も lines 2352-2398 で維持される — 成果物影響: `generated_from_head` の値だけでは certified 選択、fresh rebuild 比較、proof chain の他 field を変更できない。

[確認] orchestrator/campaign/layer3_report.py:50 — `_HERE` は resolve 済みであり、public build 経路の campaign も line 393 で resolve される。symlink alias、`..`、現在の POSIX filesystem 上の大文字小文字差による追加の偽陰性は確認できない — 成果物影響: これらの path 表記差だけで層3レポートの受理集合や値は変わらない。

[確認] output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/reports/layer3_report.json:1 — exact field/value 検索では tracked layer3 report 7 件が `generated_from_head` を bytes として保持していた。7 件の path と全体 SHA-256を逆検索したが `FROZEN_MANIFEST`、独立 golden、別の逐語台帳による pin はなく、今回の差分もこれらを編集していない — 成果物影響: 既存7レポートの bytes と参照は不変である。