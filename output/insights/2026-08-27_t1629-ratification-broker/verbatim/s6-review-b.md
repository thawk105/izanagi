## 所見

### 1. M10 の期待 node は exact な収集 node と一致しない

- **主張:** 事前登録 M10 の期待名は、実装された parametrized node の exact 名ではない。
- **成立条件:** [s4-mutation-prereg.md:22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1629-ratification-broker/s4-mutation-prereg.md:22)、[test_enforcement_source_ratification_receipt.py:494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_enforcement_source_ratification_receipt.py:494)
- **根拠:** 登録名は `test_v2_non_regular_ledger_entries_are_rejected` だが、収集されるのは `...[symlink]` と `...[gitlink]` の 2 node。base 名は選択 prefix には使えても exact collected node ではない。
- **成果物影響 (DW-G05):** mutation report の期待 KILLED node join が MISMATCH になり、M10 の検出証拠を受理できない。
- **判定:** **must-fix、本 wave。** 凍結 prereg を維持するなら、少なくとも一方を非 parametrize の unsuffixed node に分割する。全実装 node 名自体は ASCII。

### 2. 共有 fixture が暗号依存欠落を skip に変え、consumer 群を弱める

- **主張:** `ratified_enforcement_source` は、以前の fail-closed fixture に `pytest.importorskip` を導入している。
- **成立条件:** [conftest.py:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/conftest.py:195)、特に [conftest.py:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/conftest.py:201)
- **根拠:** Git 不在は `pytest.fail` だが、cryptography 不在は skip。親の M10 は 22 file / 112 source 箇所を確認している。さらに checked-in duration ledger と AST の静的突合では、module-level `usefixtures` と parametrize を展開すると約 1,102 node が該当する。全走では新規 receipt test の直接 import が collection error になり得るが、consumer だけの焦点走は大量 skip で rc=0 になり得る。返り値は従来どおり digest で、副作用の v1→v2 切替自体は production 配線に追随している。
- **成果物影響 (DW-G05):** 焦点レポートが批准 gate 回帰を検査せず skip として完了し、検査済み node 集合とレポート内訳が弱くなる。
- **判定:** **must-fix、本 wave。** 直接 import または明示的 `pytest.fail` にする。

### 3. 裁定で必須だった `hooks/README.md` の運用境界が未反映

- **主張:** repo copy は参照実装で、運用 copy は AI 非到達 host に置くという必須説明が module docstring にしかない。
- **成立条件:** [s4-ruling.md:117](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1629-ratification-broker/s4-ruling.md:117)、[ratification_broker.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/tools/ratification_broker.py:2)、[hooks/README.md:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/hooks/README.md:112)
- **根拠:** 裁定は module docstring と `hooks/README.md` の両方を要求するが、commit に README 差分がなく、現行 README に ratification/broker の説明はない。
- **成果物影響 (DW-G05):** repo 内 broker を運用 copy と誤用すると、broker/verifier の改変で任意 closure の receipt が作られ、certified 受理集合が攻撃者選択へ変わる。
- **判定:** **must-fix、本 wave。**

### 4. 秘密鍵 egress テストは stdin しか検査せず、名前ほどの検出力がない

- **主張:** `test_private_key_bytes_are_not_sent_to_children` は argv・環境・remote Git 履歴への漏えいを検出しない。
- **成立条件:** stub は argv と stdin を記録する [test_ratification_broker.py:135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_ratification_broker.py:135) 一方、検査は stdin だけ [test_ratification_broker.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_ratification_broker.py:660)。
- **根拠:** PEM、seed、その base64/hex を ssh argv や remote command に載せる production 変異でも現 assert は緑。remote tree 検査も現在の filesystem bytesだけで、Git object history を検査しない。
- **成果物影響 (DW-G05):** 漏えい鍵で任意 digest の署名 receipt を作れ、批准済み digest 集合と certified 受理集合が拡大する。
- **判定:** **must-fix、本 wave。** 少なくとも ssh の argv/stdinと、秘密材料の代表 encoding を独立に検査する。

### 5. receipt test の 27-path collection sentinel は追加 2 path の脱落を検出しない

- **主張:** module-level `assert len(...) == 27` は production tuple に追加 2 path を再注入してから数えるため、その 2 path が production から落ちても成立する。
- **成立条件:** [test_enforcement_source_ratification_receipt.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_enforcement_source_ratification_receipt.py:35)
- **根拠:** `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` から `ed25519_verify.py` または receipt verifier が消えても、行37–38が足し戻す。独立 golden の [test_t671_source_binding.py:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_t671_source_binding.py:190) は赤になるため、suite 全体の穴ではない。
- **成果物影響 (DW-G05):** 現状は独立 golden が同じ脱落を拒否するため、certified 受理集合・レポート・台帳は変わらない。
- **判定:** **nit、本 wave で直すのが望ましい。** 独立 27-tuple と production tuple を直接比較する。

既知の回収恒真型については、runner 検査、merge 前提、小位数 R の各テストに同型の残存は見つからなかった。

### 6. duration ledger の旧 nodeid 10 件は stale

- **主張:** 10 key は収集されず、新しい `twenty_seven` node は未知 cost になる。
- **成立条件:** [acceptance_duration_ledger.json:14847](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/acceptance_duration_ledger.json:14847)、[acceptance_duration_ledger.json:14902](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/acceptance_duration_ledger.json:14902)
- **根拠:** runtime lookup は exact nodeid を使い、見つからない unit は第96位既知 costへ落とす [conftest.py:1304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/conftest.py:1304)、[conftest.py:1348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/conftest.py:1348)。台帳は選択・skip・受理判定には使わないという D746 の fail-soft 契約。
- **成果物影響 (DW-G05):** 台帳に死んだ参照10件と live node欠落10件が残り、xdistの初期配布順だけが劣化する。収集集合と certified 選択結果は変わらない。
- **判定:** **nit、ただし本 wave で key migration すべき。** 10 key の `twenty_five` を `twenty_seven` に置換し、既存の実測値をそのまま保持する。値の新造は不要で、`nodeid_count=15909` も不変。

### 7. current phase doc に v1 前提が残る

- **主張:** T-1378 は「署名と trust root を設けない」とした旧裁定のままで、今回の実装状態と矛盾する。
- **成立条件:** [docs/phase3.md:744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/docs/phase3.md:744)
- **根拠:** commit は signed v2 receipt と trust root を実装済み。段7で T-1378 の消化・supersede と、構造的限界を記録する必要がある。
- **成果物影響 (DW-G05):** certified 値は変わらないが、phase 台帳が実装済み機構を未採用として参照し続ける。
- **判定:** **nit、本 wave の段7で更新。**

`docs/` の exact 25 残存は次の扱いです。

- [fig2b provenance:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/docs/paper-story/figures/fig2b_backoff_sweep_3workload.provenance.json:69)、同123・177は過去 artifact の記録値なので変更しない。
- [decisions.md:32559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/docs/decisions.md:32559) と [decisions.md:34202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/docs/decisions.md:34202) は既決定時点の歴史記録なので書き換えず、s4-ruling §7 の新決定を末尾追記する。
- `docs/failures.md` と `docs/archive/` の 25-path 記述も発生時点の履歴であり、追随対象ではない。

## 既存 assert の監査

直接変更された既存 assert は次の2件だけで、どちらも path数追随です。

- [test_artifact_admission.py:1011](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_artifact_admission.py:1011): identity scope の `exact 25` → `exact 27`。
- [test_artifact_admission.py:1136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_artifact_admission.py:1136): closure map 件数 `25` → `27`。

[test_t671_source_binding.py:186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_t671_source_binding.py:186) と [同:364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_t671_source_binding.py:364) の既存 assert 群は、関数改名により diff 上は置換だが、比較演算と受理意味は同じです。意味上の変更は以下のみです。

- 独立 golden tuple に2 path追加。
- `_RATIFICATION_IMPLEMENTATION_PATHS` を `[17:20]` から `[17:22]` へ変更し、2 verifierを加える。
- `_RECEIPT_IMPLEMENTATION_PATHS` を `[20:]` から `[22:]` へ変更し、従来の5 pathを保持。
- call-count pin `verify_ratified_contract_loader_binding == 1` は [同:803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_t671_source_binding.py:803) で維持。

したがって、閉包追随以外に緩んだ既存 assert はありません。

## pin 閉包の棚卸し

追随済みの全 literal pin は以下です。

- canonical tuple: [campaign_lock.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/campaign/campaign_lock.py:27)
- 独立 broker tuple: [ratification_broker.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/tools/ratification_broker.py:38)
- T671 golden・slice・test名: [test_t671_source_binding.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_t671_source_binding.py:38)
- artifact-admission golden・件数: [test_artifact_admission.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_artifact_admission.py:46)、[同:1136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_artifact_admission.py:1136)
- production の逐語: [campaign_lock.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/campaign/campaign_lock.py:27)、[contract_loader_binding.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/campaign/contract_loader_binding.py:2)、[artifact_admission.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/campaign/artifact_admission.py:67)
- 残件: duration ledger 10 key、`docs/phase3.md:744`、`hooks/README.md`。

その他の `CONTRACT_LOADER_RELATIVE_PATHS` consumer は production constant を動的参照しており、追加 literal pin は見つかりませんでした。

## 変異 node 照合

M10以外は事前登録名と実装関数名が exact 一致し、すべて ASCII です。

| ID | 実装位置 | 判定 |
|---|---|---|
| M01–M03 | [test_ed25519_verify.py:259](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_ed25519_verify.py:259)、266、288 | exact |
| M04–M09 | [test_enforcement_source_ratification_receipt.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_enforcement_source_ratification_receipt.py:352)、373、391、407、429、448 | exact |
| M10 | [同:494](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_enforcement_source_ratification_receipt.py:494) | **不一致。実 node は `[symlink]` / `[gitlink]` 付き** |
| M11–M13 | [同:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_enforcement_source_ratification_receipt.py:552)、572、593 | exact |
| M14–M17 | [test_ratification_broker.py:416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/tests/test_ratification_broker.py:416)、494、507、584 | exact |

## 受入全走への影響

- 新規3 fileは親実測で101 node、合計5.33秒です [parent-measurements.txt:235](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1629-ratification-broker/materials/parent-measurements.txt:235)。専用テスト自体は開発停止級ではありません。
- receipt gate は1行0.023秒、以降ほぼ1行0.009秒の線形です [parent-measurements.txt:189](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1629-ratification-broker/materials/parent-measurements.txt:189)。二乗化の懸念は解消済みです。
- 外側 shard は file/group連結成分を node数で割り付けるため、3 fileは重み37・39・25の独立成分になります [acceptance_shards.py:288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/tools/acceptance_shards.py:288)。fileを跨いで分割されず、収集集合 gateにも影響しません。
- 3 fileに明示 `xdist_group` はなく、内側 loadgroup では原則1 node 1 unitです。101 nodeは duration ledger 未登録なので第96位 costで初期配置されます。
- 唯一の広い所要リスクは function-scoped共有 fixtureです。各 invocationで27 fileのcopy、鍵生成、Git 2 commitを行い、M19の gate costとは別です。静的には約1,102 current nodeが fixture対象であり、追加CPU/IOは確実ですが、wall-time増分の実測はありません。

この fixture コストは **nit・次 wave候補**です。DW-G05影響は「受理集合は変えず、受入完了時刻と shard負荷だけを増やす」です。現資料から開発停止級とは判定しません。

## 総括

静的レビューの結論は **must-fix 4件**です。

1. M10 の exact node 不一致。
2. 共有 fixture の `importorskip`。
3. `hooks/README.md` の必須運用境界欠落。
4. 秘密鍵 egress テストが stdin しか検査しない点。

既存 assert の意味的緩和はありません。pin の未処理は duration ledger 10 keyと段7文書です。pytestは実走しておらず、所要・pass数は親の M18/M19/M22 の実測だけを引用しました。Web検索は使用していません。