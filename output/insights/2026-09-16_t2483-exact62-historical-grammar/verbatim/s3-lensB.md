## 所見 B-1: 固定 known-answer が抜け、宣言順の同時変更で緑になりうる

**主張:** 独立した期待 tuple だけでは不十分。exact-62 の固定 E1 と宣言順 path hash を、期待列から再計算しない文字列として置くことがプランに明記されていない。

**根拠 (file:line):** `s2-plan.md:148,184,189` は独立期待列・期待 epoch に言及するが、固定文字列の指定がない。`docs/decisions.md:50655–50671` の D1652 は、production と期待 literal の同時並べ替えを検出するため、固定 E1 と path hash の両方を要求している。踏襲対象の `orchestrator/tests/test_artifact_admission.py:511–523` は期待列から epoch を再導出する helper である。

**real と思う理由 / refuted されうる条件:** 両側の literal を同時に並べ替えると、wire の sorted 順は変わらず、再計算した期待 epoch も追随する。独立した固定文字列を assert する実装計画が示されれば反証される。

**成果物影響 1 行:** 同一の記録 map に対する歴史 E1 が変わり、材料レポートの epoch 参照が変化してもテストが緑になりうる。

## 所見 B-2: 間接 consumer の棚卸しが欠け、Layer3 は admission 成功後も読めない

**主張:** プランの直接参照一覧は一致するが、間接 consumer の影響判定が不足している。特に `layer3_report.build_report` は exact-62 を後段で再拒否する。

**根拠 (file:line):** 直接参照の実行コードは次の全件だった。

- `campaign_lock.py:211,366,382,568,753`：authority 検査・構築、text decoder、bytes wrapper。
- `artifact_admission.py:976,987,999,1029`：歴史 decoder wrapper、目的別 dispatch、blob 検証、epoch 構築。
- `b10_backoff_shape_sweep.py:3131–3145`。
- `b10_backoff_static_tail_formal.py:351–358`。
- 直接テスト参照は `test_campaign_lock_codec.py:149–217` と `test_b10_backoff_shape_sweep.py:2537–2540`。

helper 経由で追うと、`artifact_admission.py:1307 → 1479 → 1522` の中央 admission から、プラン未記載の以下へ流れる。

| consumer | exact-62 に対する結果 |
|---|---|
| `layer3_report.py:733,755` | 歴史 admission 後、`:112–120` の通常 decoder で再拒否 |
| `tools/plotting/plot_backoff.py:275` | admission 拒否から、WAL・dat の後段検査へ進む |
| `tools/plotting/plot_s1_9pair.py:562,589` | 後段の canonical campaign／E0 条件が残る |
| `critic/online_digest.py:42–45` | 歴史 view を `build_digest` へ渡せるようになる |
| `replay.py:149,173` | `discover_campaign_dir → discover_p2_2_dir` へ伝播 |
| `p2_2_report.py:132`、`critic/digest.py:1236` | 上記 discovery 経由で歴史 view を受け取る |

共通 epoch helper の外部呼び手も確認した。`s1_report.py:305`、`s8b_oracle_report.py:557`、`backoff_requested_us.py:507` は通常 decoder を先に通すので、今回も exact-62 を拒否する。

B10 shape は `:3136` の exact-24 条件で拒否を維持する。static-tail は用途条件まで進むが、指定実 3 本の `run_kind` はすべて未設定だったため、`:354` の `t2418-explore` 条件を満たさない。

**real と思う理由 / refuted されうる条件:** Layer3 の二度目の decode は実コード上の確定経路。ただし、今回の完了範囲を中央歴史 API に限定するなら、Layer3 修正は必須とはいえない。材料レポートまで読めるという説明は撤回または限定する必要がある。

**成果物影響 1 行:** 中央 API が緑でも Layer3 材料レポートは生成不能のまま。他の歴史 consumer は後段検査へ進み、certified 選択は通常入口の拒否を維持する。

## 所見 B-3: 実 3 本の確認が decoder 成功だけなら、目的未達を見逃す

**主張:** 「実 3 本で読取り確認」の到達点が未定義。decoder／lock-only epoch の成功だけでは、`HistoricalCampaignView` を取得できる証明にならない。

**根拠 (file:line):** `s1-brief.md:47`、`s2-plan.md:202` は親側確認を残すが、実行する API と期待結果を指定していない。`artifact_admission.py:1312,1368,1379,1397,1400` には activation、WAL topology、commit contract、provenance、build receipt の後段検査がある。

独立した静的照合では、指定実 3 本すべてについて以下を確認した。

- canonical JSON であり、wire key 列が履歴 62 tuple の sorted 順と一致。
- 各 62 path の記録 digest が記録 commit blob と一致。
- 宣言順から算出した E1 は A-2 の 2 本で同一、A-6 は別値。

一方、WAL・activation・receipt を含む admission 全体は実行していない。

**real と思う理由 / refuted されうる条件:** 合成 fixture は実 decoder を迂回していない。`test_artifact_admission.py:526–544` は wire を作り、`:1759` が中央 admission を呼ぶ。ただし合成 corpus の成功は実 corpus の後段検査成功を保証しない。親側確認を「各実 campaign に対する `require_admitted_campaign(..., purpose=HISTORICAL_RAW)` 成功、歴史型・scope・unknown・入力 bytes 不変の確認」と明記すれば解消する。

**成果物影響 1 行:** 合成テストと decode 確認だけが緑でも、実 3 本の WAL を歴史材料として取得できない状態が残りうる。

## 所見 B-4: 「変更面 2 file」はテストを含めると成立しない

**主張:** 親 brief の file 数は過少。ただし実装子を分ける理由にはならない。

**根拠 (file:line):** `s1-brief.md:49` は編集面を 2 file とするが、`s2-plan.md:128–146` は `orchestrator/tests/test_campaign_lock_codec.py` と `orchestrator/tests/test_artifact_admission.py` の編集も要求している。最低でも production 2＋test 2 の 4 file。Layer3 まで直すなら `orchestrator/campaign/layer3_report.py` と対応テストも追加となる。

**real と思う理由 / refuted されうる条件:** 「production module が 2 本」という意味なら解消する。変更は密接に関連しており、実装子 1 本で足りる。registry、新 module、一般化 framework の過剰追加は見つからなかった。

**成果物影響 1 行:** file 数の訂正自体は成果物値・受理集合を変えないため、これは段取り上の nit。

## 所見 B-5: P1・scope の根拠欠落という疑いは反証された

**主張:** 宣言順の取り違え、scope の根拠なし、既存否定テストの必須差し替えという欠陥は確認できなかった。

**根拠 (file:line):**

- `git show 2a9ba783f^:orchestrator/campaign/campaign_lock.py:49–112` を独立取得し、`measured-facts.md:32–93` と全 62 要素・順序が一致した。
- 対象 file の履歴は `a94ba713b → da44dc7b1 → 2a9ba783f`。62 時代の両 commit の tuple は一致し、途中の増減・並べ替えはなかった。
- sorted 列の末尾 LF 付き SHA-256 も親の `ea217fef…bb6ff59` と一致。
- 新 scope は当時の `a94ba713b:orchestrator/campaign/artifact_admission.py` の定数と一致。`docs/decisions.md:50607,50633`、`output/insights/2026-09-02/t733-source-closure-62path/README.md:12–35` が 24＋36＋2、発見集合 131、未収載 69 を裏付ける。
- `test_campaign_lock_codec.py:278–287` に「63 から 1 件削除」は実在するが、通常 decoder の拒否テスト。歴史側で未知とするテストではない。brief `:38` は「あれば」という条件文なので空想の断定でもない。

**real と思う理由 / refuted されうる条件:** 上記は親の写しに依存しない静的再確認。現行 scope と新歴史 scope が同文になる紛らわしさは残るが、現行文面の訂正は今回の scope 外。

**成果物影響 1 行:** 宣言順・新 scope・既存否定テストについて、追加修正が必要な成果物上の誤りは見つからなかった。

## 総括

最も危険なのは B-2：中央 admission の成功を材料レポートの読取り成功と扱うこと。  
判定は**補正後に採用可**。固定 known-answer、間接 consumer の限界、実 3 本の確認到達点を明記すべき。  
production 2 module への実装集中と実装子 1 本は維持できる。  
ファイル変更・pytest・admission 実走は行っていない。