## 対応表

`closed` は、元が refuted の所見では「修正後も反証が成立し、退行なし」を表す。

| ID | 判定 | fix 後の根拠（file:line） |
|---|---|---|
| RA-01 | closed | `docs/agent-architecture.md:129` は出自条件を撤去。`:130` の campaign WAL は例示であり、`:124` の公開文献由来の測定済み性能を排除しない。 |
| RA-02 | closed | `docs/agent-architecture.md:135`〜`:138` は説明を含む**成果物全体**を選定対象から外し、説明部分の削除投入と指示検出回避の加工を明示的に禁止する。 |
| RA-03 | closed | `docs/agent-architecture.md:128` は送り手を主語に維持。`:137`〜`:138` の「gate は変えず」も存続し、機械的分類の追加要求はない。 |
| RA-04 | closed | `docs/agent-architecture.md:139`〜`:140` は遡及禁止の対象を過去の走行・記録・fixture、理由を「この規律との差だけ」に限定。将来入力への免責はない。 |
| RA-05 | closed | `docs/agent-architecture.md:128` と `docs/phase3-s4b-runbook.md:41`〜`:43` は manifest 作成時の選定義務。`docs/roadmap.md:25`・`:29` の参照可能範囲と実投入の区別を壊さない。 |
| RB-01 | closed | `docs/agent-architecture.md:130`〜`:131` が進行状態と抽象的成否だけの checkpoint を除外。対象 `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/loop_state.json:2`〜`:32` はその条件に該当し、選定不可に決まる。 |
| RB-02 | closed | `docs/phase3-s4b-runbook.md:42`〜`:43` は role 節と箇条書きの項を区別。節名の短縮表記は `docs/agent-architecture.md:105` の逐語部分文字列として1行、項名は `:128` に全文一致で1行だけ当たる。 |
| RB-03 | closed | `docs/agent-architecture.md:129`・`:133`〜`:136` は内容基準を維持。別 campaign の `output/campaigns/p3-s4-red-s4-red-consumer-9a1897c4/runs/wal.jsonl:3`・`:6`〜`:7` の timeout・検証失敗記録も選定可能で、同 campaign の lock・digest の説明文は除外される。 |
| RB-04 | closed | `docs/phase3-s4b-runbook.md:41`〜`:43` は K2 適用条件と参照だけ。`docs/agent-architecture.md:130` も歴史的例示を維持し、規律の複製・可変状態・追加機構を持ち込んでいない。 |
| RB-05 | closed | `docs/agent-architecture.md:128` の裁定参照と `docs/phase3-s4b-runbook.md:42`〜`:43` の参照先は実在。fix 後の `python3 -B tools/check_docs.py` と `git diff --check` はともに終了コード0。 |

## 新規所見

以下は、指定された疑義を再検査した結果であり、新しい real の欠陥は確認しなかった。

| ID | 判定 | 根拠・成果物への影響 | 最小修正（維持する逐語） |
|---|---|---|---|
| F-01 定義の過度な拡張 | refuted | `docs/agent-architecture.md:129` の定義単独では測定結果を含む設計文書も重なりうるが、`:131`〜`:137` が説明を含む成果物と設計・運用 docs 自体を明示的に除外する。本文全体から設計説明の投入許可は導けない。 | 不要。「これらの説明を含む成果物は、測定値が同居していても source に選ばない。」 |
| F-02 checkpoint 除外の一般条件化 | refuted | `docs/agent-architecture.md:130`〜`:131` は checkpoint 全般の禁止でも、全測定記録への必須フィールド追加でもない。「進行状態と抽象的な成否だけ」という内容上の限定がある。対象ファイルの `success` と全件 null の `delta_pct` はこの除外に該当する。 | 不要。「観測値と判定を伴わず、探索の進行状態と抽象的な成否だけを保存した checkpoint は測定記録に当たらない。」 |
| F-03 別成果物への加工指南 | refuted | `docs/agent-architecture.md:136` の「別の測定記録」は選定先の変更を指す。`:138` は加工した入力の作成自体を禁止しており、削った内容を別ファイルへ保存して投入する操作も許さない。manifest の加工経路は新設されない。 | 不要。「指示検出を避けるために自由文を削除・抜粋・言い換えした入力も作らない」 |
| F-04 参照の不一致 | refuted | RB-02 のとおり、見出しは逐語の短縮表記、項名は全文一致で、両方とも部分文字列検索が一意。存在しない節・項への誘導は残っていない。 | 不要。「『知識源の選定 (送り手側の義務、D1936 項 2)』項に従って選ぶ。」 |
| F-05 隣接規律・roadmap との矛盾 | refuted | `docs/agent-architecture.md:118`〜`:127` の受け手境界・構造遮断、`:152`〜`:155` の主張境界を変更していない。`docs/roadmap.md:29` が区別する参照許可範囲と実投入のうち、今回の義務は後者を制約する。 | 不要。「manifest を作る信頼中核は `sources` を」 |

## 総括

全10件は closed。fix が持ち込んだ新しい real の欠陥、残る blocker は確認しなかった。  
焦点再レビューとして land 可。文書検査と差分の空白検査は成功した。  
既存の実行境界の断定（段4裁定 S-02）は、裁定どおり別タスクの射程に残る。  
ファイル変更・commit は行っていない。