## 総括

独立に読んでも、3案では案1が最善であり、親の推奨方向に賛成する。  
ただし、既存 decoder の受理集合を直接広げる実装には反対する。D1163 後の certified gate は現行 closure の可用性しか見ないため、旧 grammar が certified へ通る危険がある。  
専用の歴史 decoder、旧 grammar の明示識別、`HistoricalCampaignView` 限定という三重境界が必須である。  
案2は過去 authority の事後改変、案3は fig2c の中央 admission を失うため採らない。テストは実行していない。

## 各案の評価

### 案1: 歴史閲覧限定の versioned decoder

- 規律2への影響: 条件付きで維持できる。現行 decoder は exact-62 を要求しているが、certified gate 自体は記録 closure と現行 closure の一致を検査せず、現行 closure を capture できれば通す。[campaign_lock.py:253](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/campaign_lock.py:253)、[artifact_admission.py:1002](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/artifact_admission.py:1002)。したがって `_validate_authority()` や通常の `decode_campaign_lock()` を known-set 許容へ変えるだけでは、旧 map が `CertifiedCampaignView` まで到達しうる。これは不可。
- 安全な境界: `purpose` は admission 前に型検査できるため、`HISTORICAL_RAW` の場合だけ専用 decoder を選べる。[artifact_admission.py:1295](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/artifact_admission.py:1295)。通常 decoder、`classify_campaign()`、A2 の直接 decoder は exact-62 のまま残すべきである。
- certified への流入: `HistoricalCampaignView` から `CertifiedCampaignView` への直接昇格は、発行 token、E1 要求、exact 型検査で閉じている。[artifact_admission.py:329](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/artifact_admission.py:329)、[artifact_admission.py:1359](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/artifact_admission.py:1359)。
- ただし「歴史値が certified と名の付く処理へ一切流れない」は偽である。歴史 view の `records` は共通 `ImmutableWalRecord` であり、`require_persisted_certified_commit()` は view 型を要求しない。[artifact_admission.py:686](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/artifact_admission.py:686)。歴史 view の records を渡す正例も固定され、`s1_report` も実際に使用する。[test_artifact_admission.py:1513](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/tests/test_artifact_admission.py:1513)、[s1_report.py:354](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/s1_report.py:354)。これは「当時記録された certified 証拠」の確認と限定して表示し、現行認証と呼ばない条件が要る。
- 規律7への影響: 最も整合する。元 lock、元 WAL、元 commit map を変更せず、当時の grammar で解釈し、`current_verifier_conformance="unknown"` とできる。[artifact_admission.py:404](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/artifact_admission.py:404)。
- 既裁定との整合: D1245 が直接裁定したのは `current-closure-unavailable` であり、旧 wire grammar そのものではない。[rulings-verbatim.md:392](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t733-source-closure/input/rulings-verbatim.md:392)。したがって自動的な許可ではないが、「歴史閲覧と現行認証を分離する」という理由は案1を強く支持する。D1075 は certified 経路の拡張命令なので、歴史専用 decoder は矛盾しない。[rulings-verbatim.md:240](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t733-source-closure/input/rulings-verbatim.md:240)。
- D1128: 改善も解消もしない。旧 artifact は新 decoder の bytes を記録していないため、「当時の decoder が認証された」とは言えない。現行コードによる歴史解釈にすぎない。判定器が閉包内という自己参照限界も残る。[rulings-verbatim.md:283](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t733-source-closure/input/rulings-verbatim.md:283)。
- 作業量: production 約200〜350行、test 約180〜300行。主に `campaign_lock.py`、`contract_loader_binding.py`、`artifact_admission.py`、歴史 decoder を直接使う `s1_report.py`、`test_campaign_lock_codec.py`、`test_artifact_admission.py`、B10回帰テストの計6〜7ファイル。

### 案2: 外部11件を新閉包で再発行

- 規律2への影響: 表面的には exact-62 を維持するが、現在の code/activation authority を過去の WAL に載せれば、実行されていない組合せを certified として受理させる。正しさゲートの強化ではなく証拠の事後合成になる。
- 規律7への影響: 不適合。「当時 exact-62 closure で測った」という事実は存在しない。記録 commit から追加38 path の digest を事後導出できても、「その map を持つ lock が測定時に存在した」ことや「当時それを gate とした」ことにはならない。
- 既裁定との整合: D1139 は byte級批准を廃止したが、commit IDや測定時点情報を参考として正確に残すことは維持している。虚偽の再発行を許した裁定ではない。[rulings-verbatim.md:320](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t733-source-closure/input/rulings-verbatim.md:320)。
- 代償: 11 lockだけでは閉じない。B10では lock hash が completion と生成器定数に束縛される。[plot_b10_extended_backoff.py:403](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/tools/plotting/plot_b10_extended_backoff.py:403)。A2では lock hash が raw cell、WAL receipt、raw manifestへ連鎖する。[paper_story_a2_certification.py:2762](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/paper_story_a2_certification.py:2762)、[paper_story_a2_certification.py:3181](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/paper_story_a2_certification.py:3181)。外部走査でも8 lockの各 hashが2〜4別ファイルに現れた。
- 作業量: 最低でも11 lock、A2 raw 16件、B10 completion 3件、manifest/receipt/provenance、repo側 hash定数へ波及し、30ファイル超。正当に行うなら再発行ではなく再測定であり、コード行数では見積もれない。

### 案3: fig2cを file bytes 束縛へ移す

- 規律2への影響: fig2c生成経路について明確な弱化。現在は `backoff.load_campaign()` が `HISTORICAL_RAW` admission を通し、検証済みの不変 WAL records と epoch を返す。[plot_b10_extended_backoff.py:675](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/tools/plotting/plot_b10_extended_backoff.py:675)、[plot_backoff.py:267](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/tools/plotting/plot_backoff.py:267)。
- 失うもの: v2 exact schema、authority mapと記録 commit blobの照合、activation tuple、overlay deny、現行 admission policy、attempt topology、trigger binding、lock/WALの読取前後同一性。[artifact_admission.py:1141](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/artifact_admission.py:1141)、[artifact_admission.py:1196](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/artifact_admission.py:1196)、[artifact_admission.py:1254](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/artifact_admission.py:1254)。
- 残るもの: 22入力の固定 SHA-256、scheduler receipt chain、campaign identity suffix、WAL/dat数値照合は独立に残る。[plot_b10_extended_backoff.py:235](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/tools/plotting/plot_b10_extended_backoff.py:235)、[plot_b10_extended_backoff.py:345](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/tools/plotting/plot_b10_extended_backoff.py:345)、[plot_b10_extended_backoff.py:594](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/tools/plotting/plot_b10_extended_backoff.py:594)。したがって完全な無束縛ではないが、中央 admission と同値ではない。
- 規律7への影響: 元 bytes を温存する点はよい。ただし E1や「admitted」とは記録せず、固定 corpus の raw historical projection へ格下げする必要がある。
- 既裁定との整合: D1245の歴史閲覧には沿うが、「理由を全面撤去しない」に反しやすい。D1128の自己参照を解消するのではなく、対象判定器を経路から外して主張を弱めるだけである。
- 作業量: plotting側約100〜180行、test約80〜150行、fig2c provenance JSON再生成。generator/dependency hashも変わるため、凍結 provenance bytes据置とは両立しない。

## 第4案

案1の縮小版として、まず実害が証明された exact-24 だけを、専用 `HISTORICAL_RAW` decoderで受ける案がある。8/12/14/25/27は実物fixtureとconsumerを添えて別途追加する。

これは独立した意味論というより案1aだが、今回の唯一の赤を閉じつつ歴史受理集合の拡大を最小化できる。約250〜400行で見込める。将来grammarを追加するたび閉包内実装を変更する費用は残る。

## 同型で壊れる他の consumer

固定された外部11件については、静的に2系統ある。

- B10 3件: `plot_b10_extended_backoff.load_measurements()` → `_load_workload()` → `plot_backoff.load_campaign()` → `require_admitted_campaign(HISTORICAL_RAW)`。これが観測済みの赤である。[plot_b10_extended_backoff.py:747](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/tools/plotting/plot_b10_extended_backoff.py:747)。
- A2 8件: `collect_results()` の再導出時に `_raw_cell_from_wal()` → `_campaign_observation()` → 通常 `decode_campaign_lock_bytes()` を通る。[paper_story_a2_certification.py:2141](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/paper_story_a2_certification.py:2141)、[paper_story_a2_certification.py:2583](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/paper_story_a2_certification.py:2583)。これは歴史閲覧ではなく現在のA2 certification再導出なので、案1では意図的に直さないのが正しい。

任意の実 root を受け取れる他の歴史 consumer は、共有 replay routerを除いて7入口あった。

- `tools/plotting/plot_backoff.py`
- `tools/plotting/plot_s1_9pair.py`
- `orchestrator/critic/online_digest.py`
- `orchestrator/critic/digest.py`
- `orchestrator/campaign/p2_2_report.py`
- `orchestrator/campaign/layer3_report.py`
- `orchestrator/campaign/s1_report.py`

このうち `s1_report.py` だけは `require_admitted_campaign()` ではなくprivate decodeを直接使うため、案1実装時に別途配線変更が必要。[s1_report.py:302](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/s1_report.py:302)。上記以外に、11件の固定rootへ結び付いた repo 内 decoder consumer は見つからなかった。

## 推奨と、その条件

- 案1を採る。今回だけを最小修正するなら案1aの exact-24限定でもよい。
- 通常の `decode_campaign_lock()` と `_validate_authority()` は exact-62のまま変更しない。
- boolean引数による緩和ではなく、名前と型が異なる専用 historical decoderを設ける。
- `purpose` を decoder選択前に exact enumで検査する。`classify_campaign()` と全 certified経路は通常 decoderだけを使う。
- certified経路には、D1163の可用性検査より前に「recorded grammarがcurrent exact-62」という独立assertを置く。
- 各旧grammarは key数ではなくexact path集合と順序で識別し、未知集合、欠落、余分なkeyは拒否する。
- 記録commit blobとのdigest照合は旧grammarのpath集合全体で維持する。
- 歴史scopeは当時のexact-Nを表示し、現行exact-62 scopeを流用しない。`current_verifier_conformance` は必ず `unknown`。
- 旧grammarから `CertifiedCampaignView` が発行されないこと、通常decoderとA2再認証が旧exact-24を拒否し続けることを負例で固定する。
- `require_persisted_certified_commit()` の結果は「記録当時のcertified証拠」と明記し、現行認証へ読み替えない。
- 外部11件と凍結fig2c成果物のbytesは変更しない。

## 親の裁定・前提の誤り

- 段4 §5-1 の「11件をdecode経由で読まない」「図の再生成も壊れない」は誤り。実 call chain は上記B10経路に存在し、受入実測が反証した。[s4-ruling.md:70](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t733-source-closure/input/s4-ruling.md:70)。
- 「本waveが新たに作る回帰ではない」も不正確。旧grammar拒否という一般方針は以前からあるが、exact-24 artifactsはT733直前には読め、exact-62置換後に初めて読めなくなった。具体的な互換性回帰は本waveによる。
- 「HISTORICAL_RAWからcertified主張への経路はない」と一般化できない。formalなCertified view発行は閉じているが、歴史recordsを persisted certified helperへ渡す経路は明示的に存在する。
- 親の案1という最終推奨自体には反対しない。ただし通常decoderを広げる実装なら、案1ではなくcertified受理の弱化になる。