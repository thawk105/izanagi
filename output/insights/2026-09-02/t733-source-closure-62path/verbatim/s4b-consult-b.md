## 総括

案 1 を推す。ただし、通常 decoder を旧 grammar 対応に広げる実装には反対する。  
`purpose` を decode 前に確定し、別型を返す歴史閲覧専用 decoder として実装する場合に限り、親の案 1 に賛成する。  
案 2 は測定後に authority を再構成するため不採用。案 3 は最小修正の次善策だが、中央 admission を失う代償が大きい。  
以下は静的読解結果であり、pytest は実行していない。

## 各案の評価

### 案 1: 歴史閲覧限定の versioned decoder

- 規律 2への影響:
  - 現在は `_validate_authority()` が map を exact-62 と比較するため、旧 map は purpose 判定前に拒否される。`campaign_lock.py:253-272`、`artifact_admission.py:1023-1045`。
  - 安全にできる条件は、既存の `decode_campaign_lock()` を exact-62 専用のまま残し、`decode_historical_campaign_lock_*()` を別設すること。既存 decoder 自体を union grammar にすると、`ident.py`、`wal.py`、A2 認証などの current consumer まで旧 map を受理するため不可。
  - `HISTORICAL_RAW` と certified の型分離は実在する。certified view は内部 token と exact E1 を要求し、certified consumer も exact 型を要求する。`artifact_admission.py:347-381`、`artifact_admission.py:1359-1365`。
  - ただし「歴史値が certified 系へ一切流れない」は言い過ぎである。`critic.digest` は両 view 型を受け入れ、`online_digest` は historical view を探索入力へ渡す。`critic/digest.py:685-701`、`critic/online_digest.py:35-45`、`campaign/guided.py:161-175`。直接の認証証拠化ではないが、間接利用はある。

- 規律 7への影響:
  - 元 lock を変更せず、記録時の ordered path grammar で epoch を再現し、現行適合は `unknown` とするため最も整合する。`artifact_admission.py:404-424`。
  - 旧 map を現行 exact-62 の scope 文言で表示してはならない。現在の `CampaignVerifierEpoch` は current scope を固定しているため、歴史専用診断型か grammar 固有 scope が必要。`artifact_admission.py:161-203`。
  - 記録 commit の blob 検証も、その grammar の ordered path 集合で行う必要がある。現行 binding 型は exact-62 固定なので、そのまま再利用できない。`contract_loader_binding.py:55-94`、`contract_loader_binding.py:386-411`。

- 既裁定との整合:
  - D1245 は方向として強く支持するが、直接命じたのは `current-closure-unavailable` の目的別処理である。旧 wire grammar の受理まで自動的に批准した裁定ではない。`rulings-verbatim.md:392-401`。
  - D1075 の certified exact-62 は維持される。`rulings-verbatim.md:240-254`。
  - D1128 の自己参照限界は変わらない。新しい helper module を追加して既存 closure file から import すると、その module も閉包へ追加すべきになる。したがって互換処理は既存の `campaign_lock.py` と `artifact_admission.py` 内へ置くのが妥当。`rulings-verbatim.md:296-306`。

- 代償:
  - 旧 grammar は path 数でなく exact ordered tuple で識別しなければならない。
  - 8、12、14、24、25、27 の各 grammar について epoch 順序、scope 文言、commit blob 検査が必要。
  - まず実在が確認された exact-24 だけで赤を閉じ、他 grammar は実在 corpusまたは既裁定を根拠に段階追加する方が受理集合を小さく保てる。

- 作業量:
  - `campaign_lock.py`: 100〜160 行。
  - `artifact_admission.py`: 120〜220 行。
  - `contract_loader_binding.py`: 40〜80 行。
  - `layer3_report.py`、`s1_report.py`、`qualification/artifacts.py`: 合計 20〜50 行。
  - 関連テスト: 180〜300 行。
  - 合計概算 450〜750 行、8〜10 file。exact-24 限定なら 280〜450 行程度。

### 案 2: 外部 11 件を新閉包で再発行

- 規律 2への影響:
  - gate 自体は緩まないが、旧測定を current exact-62 authority 付き artifact として扱うなら意味上の過剰認証になる。
  - lock は WAL が存在する前に loader binding を live capture して作られる。`ident.py:575-602`。測定後に残り 38 path の Git blob hash を計算しても、「測定時に disk bytes と blob が一致した」事実は復元できない。

- 規律 7への影響:
  - 元 lock の上書きは明確に反する。当時検査していない 38 path を、当時の authority の一部だったように見せるためである。
  - current commit で再発行すればさらに悪く、測定コード時点そのものが変わる。
  - 元 lock を残し、後日作成の migration sidecar として明示するなら許容余地はあるが、それは案 2ではなく別 schema である。

- 既裁定との整合:
  - D1245 は過去を現行形式へ書き換えるのでなく、歴史閲覧と現行認証を分けることを求めている。案 2は逆方向。
  - D1128 の自己参照限界も解消しない。fresh exact-62 lock になっても外部実行器は生じない。

- 代償:
  - B10 では lock hash が `CANONICAL_SHA256`、completion artifact map、receipt chain、凍結 provenance に連鎖している。`plot_b10_extended_backoff.py:129-155`、`plot_b10_extended_backoff.py:403-449`。
  - A2 では lock hash が raw evidence に入り、raw manifest、completion、acquisition の digest 鎖へ伝播する。`paper_story_a2_certification.py:2618-2626`。
  - 凍結 provenance JSON を変えないという本 wave の条件と両立しない。

- 作業量:
  - 最低でも外部 lock 11 件、B10 completion 3 件、A2 の raw manifest・completion・acquisition 群を更新する。
  - repo 側も B10 の hash 定数、独立テスト定数、provenance を更新する必要がある。
  - 安全な再発行 tool まで作るなら 300〜500 行以上。外部変更は概算 20〜40 file。作業量以前に意味論上不採用。

### 案 3: fig2c を file-bytes 束縛へ移す

- 規律 2への影響:
  - global certified gate は変わらないため、全体の認証受理集合は広がらない。
  - B10 は既に 22 入力すべてを exact SHA-256 で検査し、lock identity、completion artifact map、WALと dat の数値一致も独立検査している。`plot_b10_extended_backoff.py:217-241`、`plot_b10_extended_backoff.py:345-449`、`plot_b10_extended_backoff.py:543-573`。
  - したがって campaign 同一性を全部失うわけではない。失うのは中央 codec、activation tuple、recorded commit blob、deny overlay、current admission policy、attempt topology、build receipt の検査である。`artifact_admission.py:1072-1146`、`artifact_admission.py:1196-1256`。
  - 後日 overlay で同じ bytes が deny されても、固定 hash だけの図生成器は自動追随しない。

- 規律 7への影響:
  - 元 bytes を保存する点は良い。fig2c の主張も descriptive かつ paper-gain 不適格と明記されている。`plot_b10_extended_backoff.py:60-65`。
  - epoch を検査しないなら、再生成 provenance は `E1` を名乗らず、`historical-bytes-pinned`、current conformance `unknown` 相当へ変える必要がある。

- 既裁定との整合:
  - D1245 に反しないが、中央の歴史閲覧機構を直さず fig2c だけ迂回する局所対応である。
  - D1128 の限界は、repo 内 hash 定数と checker の自己参照へ形を変えるだけで消えない。

- 代償:
  - 中央 admission receipt と epoch provenance を失う。
  - fig2c の固定 3 campaign には強い byte 束縛が残るが、一般的な historical campaign reader にはならない。

- 作業量:
  - `plot_b10_extended_backoff.py`: 60〜130 行。
  - `test_plot_b10_extended_backoff.py`: 30〜70 行。
  - provenance markerや独立テスト調整: 30〜60 行。
  - 合計 120〜260 行、2〜3 file。

## 第 4 案

exact-hash 限定の historical compatibility registry がある。

11 件の元 `campaign.lock` と WAL の SHA-256、対応する ordered grammar を固定し、一致した artifact だけを `HISTORICAL_RAW` へ通す。任意の旧 grammar artifact を受理しないため、案 1より受理集合が狭い。

ただし、正の allowlist を新設し、B10 に既にある hash 台帳を重複させる。将来の歴史 artifact も都度登録が必要になる。概算 350〜600 行、5〜8 fileで、案 1より一般性が低いため推奨しない。

## 同型で壊れる他の consumer

全 `*.py` について `require_admitted_campaign`、`decode_campaign_lock`、`campaign.lock`、外部 root 定数を照合した。

- 現在の受入全走で実 external root を decode する経路は 1 系統だけである。  
  `test_plot_b10_extended_backoff.py:146-149` → `plot_b10_extended_backoff.py:747-756` → `plot_b10_extended_backoff.py:675-744` → `plot_backoff.py:267-357`。対象 campaign は 3 件。
- A2 の外部 8 lock を現在のテストが直接開く経路は見つからなかった。`test_paper_story_a2_certification.py:1743-1755` の絶対 path は qstat fixture 内文字列の置換にだけ使われる。
- ただし、historical と称しながら通常 decoder を直接呼ぶ潜在 consumer が残る。
  - `qualification/artifacts.py:900-915`
  - `layer3_report.py:98-106`、`layer3_report.py:541-571`
  - `s1_report.py:302-312`
- `plot_s1_9pair.py:554-592`、`critic/online_digest.py:35-45`、`replay.py:129-151` は中央 historical API を使うため、案 1の中央修正へ追随する。
- `paper_story_a2_certification.py:2563-2590` と `backoff_requested_us.py:556-623` も旧 map では失敗するが、前者は現行 A2 認証、後者は current certified reference を要求する経路である。案 1で旧 grammar 対応へ変えてはならない。

したがって、追加の「現在の受入全走を赤にする live-root consumer」は 0 件。ただし、案 1を中央 API だけ直すと、上記 3 個の直接 historical decoder が意味不一致のまま残る。

## 推奨と、その条件

案 1を次の条件で採る。

- 通常の `decode_campaign_lock()`、encode、resume、certified admission は exact-62 のまま変更しない。
- `purpose` を decode より前に exact enum で確定する。
- 歴史 decoder は別入口、別返却型にし、通常 `DecodedCampaignLock` と交換可能にしない。
- grammar は path 数でなく exact ordered tuple で識別する。未知の集合、subset、superset は拒否する。
- 歴史 epoch は記録 grammar の順序と scope で計算し、current conformance は必ず `unknown` とする。
- 互換実装を新 module に分離しない。分離するなら、その module を closure へ追加する影響を再裁定する。
- exact-24 historical 成功、同じ bytes の certified 拒否、未知 grammar の両目的拒否、型境界拒否をテストする。
- `qualification/artifacts.py`、`layer3_report.py`、`s1_report.py` の直接 decoder を同時に整理する。
- 凍結 PNG、PDF、provenance JSONと外部 11 lock は変更しない。

## 親の裁定・前提の誤り

- `s4-ruling.md:70-74` の「repo consumer は11件を decode しない」「受入全走は赤にならず、図再生成も壊れない」は誤り。`plot_b10_extended_backoff.py` が依存先 `plot_backoff.load_campaign()` を通じて中央 historical admission を呼んでいた。
- D1245 を案 1の無条件な事前承認と扱うのも誤り。支持するのは目的分離の原則であり、旧 grammar の具体的な受理集合は今回あらためて決める必要がある。
- 「HistoricalCampaignView なら certified 主張への流入経路は完全に無い」も強すぎる。直接の view 昇格は防がれているが、critic の共通 consumer と guided の間接利用は存在する。従って型分離に加え、consumer ごとの目的監査が必要である。