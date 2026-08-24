### [RA-1] 全変異は殺せるが、MUT-1〜3 と MUT-7 は純増検出力が重複する

**確信度**: high  
**must-fix / nit / backlog**: nit

**根拠**:

| 変異 | 赤くなる node と assertion | 判定 |
|---|---|---|
| MUT-1 | `test_material_report_certification_scope_is_exact_on_all_return_paths`: `orchestrator/tests/test_codex_reasoning_ab.py:7518` の exact equality。既存 node `test_verify_replays_complete_fake_codex_experiment` の `:7583-7597` も同じ不一致で赤。 | kill。新規 node の当該変異に対する純増検出力はゼロ。 |
| MUT-2 | MUT-1 と同じ 2 assertion。`"packet"` 欠落で dict equality が破れる。 | kill。純増検出力は重複。 |
| MUT-3 | 同じ 2 assertion。`material_packet_requirement` の文字列不一致。 | kill。純増検出力は重複。 |
| MUT-4 | `test_replay_forwards_only_successful_snapshot_evidence_to_adjudication`: `:7624-7633` は POS のみを期待し、`:7669` の `captured == expected_verified` が POS+NEG の全 final IDs で破れる。 | kill。既存公開 manifest node は replay mismatch 自体で変異前後とも赤なので殺せない。 |
| MUT-5 | `test_material_packet_source_requires_replayed_snapshot_evidence`: gate を削れば `:11473` の reason count が 0。条件だけを消して無条件 append にすれば `:11464` が破れる。 | kill。既存公開 node には純増検出力なし。 |
| MUT-6 | `test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run`: cache hit の二本目で比較を省けば拒否理由が消え、最初に `:7717` の `rejected_rc == RC_AGGREGATE` が破れる。仮に別理由で赤でも `:7719` が pre/post reason 欠落を捕捉する。 | kill。この node 固有。 |
| MUT-7 | 既存 `test_verify_replays_complete_fake_codex_experiment` の `:7569` が、全 packet の membership reason により rc 0 でなくなって破れる。新規 evidence node の `:7669` と shared-oracle node の baseline `:7701` も赤。 | kill。追加 node の純増検出力はゼロ。 |

殺せない変異はありません。MUT-1〜3 は既存 node に追加された assertion との重複であり、MUT-7 は変更前から存在する正例 assertion だけで十分です。

**成果物影響**: 材料レポートの値や受理集合には影響せず、変異台帳上の純増検出力の帰属だけが重複する。  
**修正案**: mutation コメントへ MUT-1〜3 の既存 end-to-end との重複、および MUT-7 が既存正例だけで殺されることを注記する。

### [RA-2] MUT-6 node は baseline 正例だが、拒否時は二理由になる

**確信度**: high  
**must-fix / nit / backlog**: nit

**根拠**:

- 事実: `_schedule` は同一 case の二 arm に同じ benchmark snapshot SHA を設定する (`orchestrator/tests/test_codex_reasoning_ab.py:693-713`)。`_full_manifest` も同じ snapshot と case を `supervise_pair` に渡す (`:1446-1455`)。
- 事実: `verify_snapshot` の oracle は snapshot と case から構成され、時刻や run ID を含まない (`tools/codex_reasoning_ab.py:2975-3126`)。したがって同一 pair の二 oracle は同じ bytes になる。
- 事実: 二本目の descriptor を一本目へ差し替えても (`orchestrator/tests/test_codex_reasoning_ab.py:7689-7698`)、実装は row descriptor の path と launch descriptor の path を比較しない。launch 側は SHA と schedule の比較だけ (`tools/codex_reasoning_ab.py:10013-10024`) で、submodule SHA も同じ oracle 内容に対する比較 (`:10025-10032`)。
- 推論: descriptor 共有だけを施した baseline に launch、submodule、receipt canonical replay の別理由は生じず、`:7700-7702` の `accepted["valid"] is True` は静的に成立する。
- 事実: tamper 後は pre/post reason が `tools/codex_reasoning_ab.py:10047-10052` で積まれる。同時に二本目は verified set から外れ (`:10053-10054`)、packet membership reason も `:8812-8818` で積まれる。したがって拒否は二理由である。
- ただし `orchestrator/tests/test_codex_reasoning_ab.py:7719` が pre/post reason 自体を count 1 で直接検査するため、この node は pre/post の発火を証明している。共有加工直後から別理由で赤いという問題ではない。

**成果物影響**: 実レポート挙動は正しいが、MUT-6 の証跡を「単一理由の拒否」と記録すると実際の failure reasons と食い違う。  
**修正案**: この node 内だけ `_load_adjudication` を wrapper 化し、全 final run IDs を渡して membership reason を抑止した上で、pre/post reason だけで拒否されることを exact 比較する。

### [RA-3] `snapshot_checks_passed` は広義の snapshot reason 全体とは一致しない

**確信度**: medium  
**must-fix / nit / backlog**: backlog

**根拠**:

- 事実: flag が false になるのは、scheduled snapshot SHA、submodule SHA、pre/post mismatch の三箇所だけ (`tools/codex_reasoning_ab.py:10019-10032`, `:10047-10052`)。
- 事実: snapshot oracle replay mismatch は reason を積むが flag を false にしない (`:10040-10043`)。ただし `snapshot_replay_verified` が false のままなので、`:10053` の conjunction により集合へは入らない。現行の導出結果に取りこぼしはない。
- 事実: supervisor ledger の `snapshot_unchanged is not True` は別の snapshot reason を積む (`:9729-9730`) が、その run ID は後段の flag に伝達されない。ledger の flag だけを false にし、実際の pre/post artifacts を一致させた入力では、この reason がありながら run は verified set に入る。
- 推論: 「replay 時の evidence 成功集合」という裁定上の狭い意味なら現行動作は整合する。一方、「snapshot 関連 reason が一件もない集合」という意味では取りこぼしがある。
- cache hit が省略するのは `verify_snapshot` 本体だけ (`:10039-10046`)。run 固有の launch SHA、submodule、pre/post、receipt、score はそれぞれ評価される (`:10019-10032`, `:10047-10072`)。
- descriptor の直接 subscript は安全である。手前の `_artifact_path` が dict を要求し (`:8436-8444`)、64 字の SHA を要求する (`:8451-8453`)。呼出しは `:9979-9981`、subscript はその後の `:10033-10037` で、失敗時は outer catch (`:10136-10137`) に入る。

**成果物影響**: ledger 由来の snapshot reason がある invalid report で、packet-specific membership reason が付かず、当該 run が evidence 集合に残る。  
**修正案**: 現行裁定に合わせるなら flag を `snapshot_replay_bindings_passed` 等へ改名し、ledger reason を対象外と明記する。全 snapshot reason-free 集合を意図するなら、ledger 検証から失敗 run IDs を返して集合から除外する。

## 追加確認

- 既存 reason の削除・改名はありません。pre/post reason は同じ文字列のまま移動し、新規 membership reason が追加されただけです (`s5-diff.patch:342-472`)。
- `_replay_manifest` の返却 tuple は `tools/codex_reasoning_ab.py:10225` の四要素のままです。`SCHEMA_VERSION` も `:48-54` で 2 のままです。
- `make_packets` は差分対象外で、packet body は引き続き output bytes をそのまま書く (`:10377-10387`)。serializer と schema 定数にも変更がないため、この差分による出力 bytes の変化はありません。
- diff で削除された既存 test 行は `_load_adjudication` の四つの旧呼出しだけで、同じ assertion を維持したまま必須引数が追加されています。期待値の緩和、skip、xfail の追加はありません。
- `_aggregate_verified` の返値には宣言がありません (`:9563-9586`)。`verify_manifest` の早期 return と共通 return の双方に宣言が付き (`:10252-10280`)、`aggregate_manifest` も委譲します (`:10283-10293`)。
- `_certification_scope` は呼出しごとに新しい dict と list を組み立てるため fresh です (`:10228-10243`)。

## 総括

- MUT-1〜MUT-7 はすべて静的に kill 可能で、殺せない変異はありません。
- MUT-1〜3 と MUT-7 は別 node でも殺されるため、指定 node の純増検出力はゼロです。
- shared-oracle 加工後の baseline は valid であり、別検査による先行拒否はありません。
- MUT-6 の拒否は pre/post と membership の二理由ですが、pre/post reason の直接 assertion は有効です。
- 既存 tuple、schema、reason 文字列、packet bytes、公開 API だけへの fresh 宣言は維持されています。
- 以上は静的検査結果であり、pytest は実走していません。