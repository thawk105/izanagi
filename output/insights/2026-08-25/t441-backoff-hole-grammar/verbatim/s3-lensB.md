# 所見

現状の段 2 プランは採用不可です。role 裁定待ちを正しく認識していますが、consumer 閉包、policy identity、値の帰属に未解決の穴があります。

## 1. `quarantine()` 1 点では consumer 閉包にならない

- **区分**: must-fix
- **成果物影響**: 文法外の backoff hole bytes が別 materializer から build・verify・COMMIT へ進み、certified 選択、材料レポート、試行台帳に正規候補として残り得る。
- **根拠**:
  - `quarantine()` は書込み前の局所関所にすぎない: `orchestrator/campaign/p3_s4_loop.py:199-282`
  - `patchharness.applied()` は patch を適用して body を呼ぶだけで文法を検査しない: `orchestrator/campaign/patchharness.py:247-263`
  - `s1_direct_comparison` の `backoff_fixed_best` は patch-only で `quarantine()` を呼ばない: `orchestrator/campaign/s1_direct_comparison.py:651-659,711-718`
  - 旧 coder kickoff は variant patch を直接適用して `run_campaign()` へ渡す: `orchestrator/campaign/p3_kickoff.py:54-63,110-122`
  - `backoff_sweep` は source の生成過程を検査せず、現在の evidence を machine-generated として attest できる: `orchestrator/campaign/backoff_sweep.py:242-248,267-276`
  - build admission の materialized-source 検査は trigger 専用: `orchestrator/campaign/build_admission.py:170-219,615-628,743-755`
  - D127 決定 (3): 「gate は driver ではなく materializer」「driver 内だけでは `pipeline.evaluate()`・sweep・screening・手動 patch が素通し」: `docs/decisions.md:6247-6250`
- **scope 判定**: 本 wave の scope 内。brief の編集面列挙が狭すぎる。build/materializer 境界まで含めないなら、本 wave は設計凍結だけで終了すべき。

静的に数え直した production caller は次の 8 module・15 call site です。段 2 の「14 call site」も 1 件不足しています。

| module | call site | marker |
|---|---:|---|
| `p3_s4_loop.py` | 991, 999 | backoff |
| `p3_s4_loop_sort.py` | 156, 456, 564 | sort |
| `p3_s4_loop_trigger_gating.py` | 421, 890, 1007 | trigger |
| `p3_autonomous_workload_trial.py` | 1595 | trigger |
| `s1_verify_extime_calibration.py` | 342 | trigger |
| `s1_direct_comparison.py` | 666 | trigger または sort |
| `s6_sort_sweep.py` | 333, 354 | sort |
| `s8a_trigger_sweep.py` | 434, 456 | trigger |

backoff marker を直接渡す caller が `run_one_iteration` の 2 点だけ、という狭い主張は正しいです。しかし、それは `quarantine()` caller の閉包であって、同じ source/hole を build する consumer の閉包ではありません。

`render_hole()` の production caller は `quarantine()` 内の 1 点だけです (`p3_s4_loop.py:245`)。直接 test caller は `test_p3_s4_loop.py:164` と `test_campaign.py:6006` です。したがって `render_hole()` の閉包を数えても、patch-only/manual materialization は現れません。

## 2. grammar version が identity・WAL・cache に束縛されない

- **区分**: must-fix
- **成果物影響**: 旧文法で合格した variant が新文法下でも同じ campaign/WAL/cache identity を持ち、再検査なしの terminal skip、旧 COMMIT の材料レポート再利用、cache hit が起き得る。
- **根拠**:
  - `SourceEvidence` に grammar policy/version field がない: `orchestrator/campaign/source_digest.py:113-135`
  - source identity は source bytes と genome だけで作られる: `source_digest.py:2096-2135`
  - variant ID は genome と `src_token` だけ: `orchestrator/campaign/pipeline.py:117-123`
  - build policy preimage は pin・authority・registry だけ: `orchestrator/campaign/build_admission.py:458-465`
  - cache key は source token と同じ admission receiptを再利用する: `orchestrator/campaign/buildcache.py:599-617`
  - backoff campaign config に grammar schema/version がない: `orchestrator/campaign/p3_s4_loop.py:817-833`
  - WAL replay は terminal variant を seed し、同じ variant ID を `evaluate()` 前に skip する: `orchestrator/campaign/loop.py:304-327,378-382`
  - 対照的に trigger は schema を campaign identityへ入れる: `orchestrator/campaign/p3_s4_loop_trigger_gating.py:475-478`。WAL も schema、attempt、source、commitment を照合する: `orchestrator/campaign/wal.py:950-1059`
  - [T-409] must-fix B-2 も同型を明記: `output/insights/2026-08-04_t409-evolve-hole-allowlist/README.md:90-94`
- **scope 判定**: 本 wave の scope 内。versioned grammar を新設するなら、accepted 側の identity 束縛までが同じ変更単位。

最低限、backoff proposal campaign の `search_config`、campaign lock、accepted attempt の WAL binding、materialized source evidenceを同じ grammar schemaへ束縛する必要があります。後から global `BuildAdmissionPolicy` 全体へ無条件に version を加えると trigger/sort を含む全 campaign ID と cache namespaceが動くため、backoff proposal に限定した束縛にすべきです。

## 3. decimal 受理と `int(coder.value)` が帰属を壊す

- **区分**: must-fix
- **成果物影響**: 例えば実行 bytes が `20.5` でも WAL/genome は `BACKOFF_FIXED=20` となり、certified 値、backoff 選定値、材料レポートのラベルが実際の binary と食い違う。
- **根拠**:
  - プランの BNF は小数を受理する: `s2-plan.md:78-98`
  - genome は `BACKOFF_FIXED=int(coder.value)` として切り捨てる: `orchestrator/campaign/p3_s4_loop.py:967-971`
  - 現行整合検査は元の float と literal の数値一致だけを調べ、整数化との一致を見ない: `p3_s4_loop.py:856-887`
  - プラン自身が `CoderProposal.value`、genome、実値の一対一帰属を必要としている: `s2-plan.md:18-23`
- **scope 判定**: 本 wave の scope 内。

v1 を現行 genome の意味に合わせるなら、受理値は正準な整数 `1..1000` に限定すべきです。小数を残すなら genome、WAL、freeze の値型を小数対応へ変える別設計が必要です。

## 4. 「正準 decimal」と言いながら正準化がない

- **区分**: must-fix
- **成果物影響**: `20`、`20.0`、`20.00` など同じ実効値が別 `src_token`・variant・cache entry・iteration として数えられ、選択集合と試行台帳が重複する。
- **根拠**:
  - BNF は任意の外周空白と複数の decimal spelling を受理する: `s2-plan.md:78-98`
  - 公開 API は decision だけを返し、正準 bytes を返さない: `s2-plan.md:37-50`
  - backoff は受領 bytesをそのまま `render_hole()` へ渡す: `orchestrator/campaign/p3_s4_loop.py:176-186,245`
  - trigger だけは materialization 前に emitter bytesへ正準化される: `p3_s4_loop.py:227-230`
  - D174 は同義 spelling をそのまま materialize すると複数 source digest・variant ID が生じるため、書込み直前に正準化すると決定している: `docs/decisions.md:8587-8609`
- **scope 判定**: 本 wave の scope 内。

整数の完全一致 spelling だけを受理するか、validator が正準 implementation を返し、それだけを materializeする必要があります。

## 5. P1 は偽で、role 裁定は実装前の実 gate

- **区分**: 裁定パッケージ候補
- **成果物影響**: 裁定なしで literal-only を実装すると、role が現在生成可能としている式を拒否し、backoff 軸の受理集合と「LLM synthesis」の意味を無承認で縮める。
- **根拠**:
  - role が禁止するのはコメント delimiter と行末 backslash: `.claude/agents/coder-v4-autonomous.md:20-25`
  - 出力は `double now_backoff = <式>;` であり、`<式>` の構文制限はない: `.claude/agents/coder-v4-autonomous.md:52-63`
  - 骨格契約は既存 silo API を呼ぶ straight-line code を明示的に許す: `patches/silo-backoff-fixed.patch:60-70`
  - 従って `double now_backoff = 1 + 1;` や `Backoff_.load(...)` は現 role 契約内だが、プラン v1 は拒否する。
  - D127 決定 (1) は producer を変えず consumer だけ狭める非互換形を退ける: `docs/decisions.md:6235-6239`
  - role 定義変更はユーザー明示承認が必要: D48 必須条件 6、`docs/decisions.md:1770-1775`
  - D511 は既存禁止文を 1 byte も書き換えず、執行範囲を別節で後置すると定める: `docs/decisions.md:21294-21305`
- **scope 判定**: 本 wave の scope 内だが、ユーザー裁定までは設計凍結のみ。

P2 の「単一宣言文」は role template と整合します。狭まる差分は主に `<式>` を call-free、さらに literal-onlyへ変える部分です。ここは段 2 の判断が正しく、親 brief の P1 が誤りです。

## 6. freeze の「7 file」は Python subset に限った数え方

- **区分**: nit
- **成果物影響**: 現プランの編集面だけなら受理集合への影響はないが、freeze 閉包の母集合を誤記すると、後続の identity修正で参照・再凍結対象を見落とす。
- **根拠**:
  - `known_axes_freeze.json` が SHA-256 を持つ live source は、7 Python fileに加え external source 2 fileの計9 file:
    - `s1_known_axes_freeze.py`: `known_axes_freeze.json:5-8`
    - `axis_trigger_gating.py`, `s8a_trigger_sweep.py`: `:46-53`
    - `genome.py`: `:107-109`
    - `backoff_sweep.py`: `:152-154`
    - `s6_sort_sweep.py`, `p3_s4_loop_sort.py`: `:200-207`
    - `external/ccbench/cmake/Options.cmake`: `:220-228`
    - `external/ccbench/cc/silo/CMakeLists.txt`: `:232-239`
  - 親 brief の7件列挙: `s1-brief.md:45-49`
- **scope 判定**: 本 wave の scope 内。

`p3_s4_loop.py`、新 grammar module、`diff_quarantine.py`、`build_admission.py` はこの9件に含まれません。したがって「主編集面が pin 外」という結論自体は維持されます。trigger/sort の受理集合も exact marker 条件を守る限り変わりません。ただし materializer gate追加後の非影響テストは `quarantine()` 単体だけでなく build-admission 経路でも必要です。

## 7. 親の実測 1・4・6 は結論の射程を限定すべき

- **区分**: backlog
- **成果物影響**: certified 値そのものは変わらないが、「既存 producer と互換」「全経路を閉じた」という材料レポートの主張が証拠より強くなる。
- **根拠**:
  - 実測1は pin `028f34d`、単一 patch、`quarantine(write=False)` だけ: `s1-brief-addendum.md:3-8`
  - 32形は手選択集合で、build、cache hit、WAL replay、material report readerを測っていない: `s1-brief-addendum.md:8-40`
  - 実測4は `quarantine()` callerだけを母集合にしている: `s1-brief.md:51-55`
  - 実測6は current checkout の `output/` text scan: `s1-brief.md:61-66`
  - reject WALは implementation原文を保存せず hashにだけ使う: `orchestrator/campaign/p3_s4_loop.py:287-316`
- **scope 判定**: 実コーパス保存方式の追加は本 wave の scope 外。

評価は次のとおりです。

- 実測1の「現 `quarantine()` は25/32を受理」は有効です。ただし end-to-end certification の測定ではありません。
- 実測4の「backoff marker callerは2点」は有効ですが、consumer閉包という呼称が過大です。
- 実測6の「current `output/` に自律 backoff implementationの凍結コーパスを発見できない」は反証できません。しかし、job dir、過去 checkout、実行時 source、原文を保存しないWALは母集合外です。「過去に生成・certifyされた形がない」または「producer互換性を確認した」とは読めません。
- current treeの静的再走査では `output/` は12,514通常ファイルで、symlinkはありませんでした。従って現 checkoutに限る走査としては広い一方、時間軸と外部job dirは覆いません。

## 8. scope 外で別途必要な policy migration

- **区分**: 裁定パッケージ候補
- **成果物影響**: pre-v1 COMMITを新文法の証拠として混ぜると材料レポートの参照が誤り、逆に無条件失効すると既存certified proof chainを切る。
- **根拠**:
  - D196は新世代を有効化する前に historical resolver と versioned dispatchを production consumerへ配線し、発火経路がなければ設計メモに留めると決定: `docs/decisions.md:9490-9517`
  - D167は凍結 literalのconsumer-local membershipを要求: `docs/decisions.md:8314-8345`
  - D173はmaterializerの受理集合をproducer schemaから独立させる: `docs/decisions.md:8564-8585`
- **scope 判定**: 本 wave の scope 外。

裁定候補は次の2点です。

1. pre-v1 artifactはhistorical certificationとして保持するが、v1 campaignのcurrent accepted setには混ぜない。
2. 将来自律backoff implementationをfreezeから再materializeするconsumerが実在した時点で、consumer-local grammar/version gateを追加する。現時点では対象artifactがないため、DW-G04に従い先行実装しない。

## 総括

- **must-fix は4件**です。最も危険なのは、`quarantine()` caller閉包をbuild consumer閉包と取り違えている点です。D127が既に退けた「driverだけにgateを置く」形を再導入しています。
- **現状のプランは、role承認を条件にしても採用不可**です。consumer/materializer閉包、grammar policy identity、整数帰属、正準化の4点を先にプランへ反映し、再レビューする必要があります。
- **親 briefで誤っている点**は、P1、`quarantine()` callerが4 moduleという数、`quarantine()` 1点でbackoff経路が全部閉じるという結論、freeze対象を無限定に7 fileとした表現です。実測6は「current `output/` に凍結コーパスを発見できない」という限定付きなら維持できます。

pytestやbuildは実行していません。所見は静的検査のみです。