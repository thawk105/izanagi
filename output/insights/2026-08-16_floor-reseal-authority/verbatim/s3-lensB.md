## 所見

### 1. Q3 lockstep が issuer で機械拒否されない

- 重大度: blocker
- 根拠: `rulings-inbox/...:45-50`、`docs/calibration-freeze-authority-bundle-design.md:178-216,840-844`、`s2-plan.md:159-174`
- 再現の筋道: 現在は active が g1、protocol は旧 pin、HEAD は新 pin (`s1-brief.md:19-23`)。零引数 `reseal-protocol` は `(g1, 新 pin)` を未使用 pair として受理する。P6 は「呼ばない」という運用であり、issuer の拒否条件ではない。
- 影響: 環境世代を進めず floor だけ進めた protocol が発行され、Q3 の片側交代を受理集合へ追加する。後続 consumer が参照すれば、certified 選択・report・ledger が上位 lockstep 外の物差しを参照する。

### 2. 新 namespace が既存 launch の未知 file 拒否に当たる

- 重大度: blocker
- 根拠: `s2-plan.md:7-19`、`orchestrator/campaign/s8b_floor_campaign.py:3216-3237,3363-3380`、`tools/pegasus/floor_campaign.sh:947-965`
- 再現の筋道: `reseal-protocol` が `output/s8b-freeze/floor-protocols/*.json` を作ると、`_assert_freeze_allowlist()` は固定4 file・selector-runs・既知 chain record 以外を未知 file として拒否する。
- 影響: 既存 floor campaign の launch 受理集合が PASS から拒否へ変わる。新 protocol を作るだけで既存の測定・certified 経路が止まり、plan の「既存受理は不変」は成立しない。

### 3. producer だけ追加され、実 production consumer は新 protocol を読まない

- 重大度: major
- 根拠: `s1-brief.md:27-31,51-54`、`s2-plan.md:7-19,124`、一次資料 `docs/calibration-freeze-authority-bundle-design.md:581-600`
- 再現の筋道: shell、`s8b_floor_campaign.py`、`certified_writer_admission.py:206-214`、`s8b_holdout_admission.py:53,383-403`、`s8b_prediction_runner.py:79,1542-1549` などは固定 path を読む。さらに `s8b_verdict.py:953-968` と `s8b_oracle_driver.py:1186-1205` は freeze/ratified pointer 経由で読むが、`floor-protocols/` へ解決しない。
- 影響: 新 pair は floor campaign、certified 選択、report、試行台帳へ到達せず、発行機構が実質 inert になる。consumer を一部だけ切り替えれば式3で拒否されるため、scope 外理由は「後続へ送る」根拠にはなるが、今回の機構を有効と呼ぶ根拠にはならない。

### 4. pair index の閉包が production の参照集合を覆っていない

- 重大度: major
- 根拠: `s2-plan.md:23-36`、`orchestrator/campaign/s8b_ratified_freeze.py:876-896,2914-2921`、`orchestrator/campaign/s8b_verdict.py:959-968`
- 再現の筋道: index は legacy path と `floor-protocols/` 直下だけを走査する。一方 ratified の `floor_protocol.path` は任意の canonical relative path を受理し、verdict はその pointer を直接読む。
- 影響: `output/protocol.json` など別 path に同じ pair の valid protocol を置いて pointer から参照させても index は一件と報告する。案3の「組ごとに一件」が崩れ、参照 path と index の証拠集合が不一致になる。

### 5. manifest・hold・既存 literal pin は新 artifact を検出せず緑のまま

- 重大度: major
- 根拠: `orchestrator/tests/test_frozen_artifacts.py:162-184,234-247`、`orchestrator/campaign/freeze_verification_hold.py:14-48`、`orchestrator/tests/test_s8b_floor_campaign.py:1153-1179,6174-6186`
- 再現の筋道: `FROZEN_MANIFEST` は既知23 pathだけを検査し、`HELD=True` の間は held対象を照合しない。新しい `floor-protocols/` を追加しても keyset、literal pin、held check ID は変わらない。`check_docs.py` も構造 lint が中心で意味的 consumer 閉包を検査しない。
- 影響: 新 artifact の bytes・path・trust root が凍結台帳に現れず、既存テストは緑のままになる。一次資料 §9 が要求する versioned path の manifest/keyset 追随が欠落する。

### 6. 専用 issuer が generic writer と hooks の保護面を迂回する

- 重大度: major
- 根拠: `s2-plan.md:15-19,120,124`、`orchestrator/campaign/s8b_floor_campaign.py:550-553,726-744`、`hooks/guard_write.py:268-275`
- 再現の筋道: generic `write_protocol_document()` と `guard_write` は `output/s8b-freeze/` への直接書込みを拒否するが、plan は専用 issuer から private writer を直接呼ぶ。CLIに confirm、TTY、T-080 receipt はない。hooks は script 内部の `os.link` を観測しない。
- 影響: hold状態と既存拒否テストを保ったまま、新しい freeze-located artifactだけを発行できる。AI発行を許す裁定自体ではなく、その発行がQ3 receipt・manifest・sanctioned writerのどれにも束縛されていない点が問題である。

### 7. `reseal-protocol` に実運用の呼出し地点がない

- 重大度: major
- 根拠: `s2-plan.md:79-96`、`tools/pegasus/floor_campaign.sh:947-965`
- 再現の筋道: plan が実際に dogfood するのは read-only の `check-protocol-index` だけで、環境 activation、floor submission、campaign launch のどこからも `reseal-protocol` を呼ばない。
- 影響: HEAD pinやactive contractが前進しても protocol は自動生成されず、新 pairの certified 選択・report・ledgerは引き続き0件。手動CLIだけの条件付き機能として残る。

### 8. `check-protocol-index` 公開CLIは現状では余剰

- 重大度: minor
- 根拠: `s2-plan.md:72-96,114-122,159-170`
- 再現の筋道: issuerの事前scan・post-write scan・real-repo testが既にあり、別CLIは実運用から呼ばれない。
- 影響: 値や受理集合を直接変えないが、発火条件・責任者・失敗時の扱いがない新しい操作面だけが増える。index表示を残すなら、launchまたはactivation chainの正式な呼出し地点を定める必要がある。

### 9. index 検査コストが artifact 数に比例する

- 重大度: minor
- 根拠: `s2-plan.md:23-36,72-96`
- 再現の筋道: 発行と checker のたびに namespace 内の全 protocolを strict parse、validate、canonical再計算する。protocol数の上限、キャッシュ、固定indexはない。
- 影響: 環境契約・ccbench pinの履歴が増えるほど発行時間と検査時間が O(N) で増える。git履歴全体走査ではないが、artifact数比例コストは残る。

## 攻撃したが破れなかった点

- `_PROTOCOL_KEYS` は実際に18 keyで、2 mutable / 16 inheritedという分割自体は裁定文の「2つ以外は変更不可」と整合する。
- 既存 legacy bytes、`FROZEN_MANIFEST`、keyset pin、`freeze_verification_hold` の21 check ID、human `freeze-protocol` のTTY・confirm・T-080は、plan上は変更されない。
- create-only、決定的 path、既存 pathの上書き拒否は、凍結履歴不変条件と整合する。
- 式3が床値だけの切替を拒否するという親の実測・要約自体は正しい。ただし、それはconsumer閉包をscope外にする理由ではない。

## 親裁定が要る択一

- issuerでQ3を機械化し、上位lockstep receiptと両成分変更を必須にするか、`reseal-protocol` を次のchain完成まで fail-closedで dormant にするか。
- 今waveで全consumer・allowlist・pointer・計算ノード境界まで移行するか、今回は実効性を主張しない設計メモだけにするか。
- versioned protocolを`FROZEN_MANIFEST`/keysetへ追加するか、別の動的manifestを新設するか。
- pair indexを全production pointerの閉包へ広げるか、productionが参照できるprotocol pathを新namespaceだけに制限するか。
- `check-protocol-index` を削除するか、正式なactivation/launch手順へ組み込むか。

## 総括

新機構は現状のままではQ3片側交代を発行できる。  
発行先の新namespaceは既存launchの未知file拒否にも衝突する。  
consumerは固定pathのままで、新artifactはcertified経路へ届かない。  
pair indexもproductionの全pointerを覆わず、常設gateになっていない。  
manifest・hold・hooksは新経路を検査せず、既存テストは緑のままになり得る。  
land前に、Q3、consumer閉包、凍結台帳の三択を親が確定すべきである。