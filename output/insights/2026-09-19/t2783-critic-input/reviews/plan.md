## 総括

**P1の「K2手動loopの兄弟key」は採用できる。ただし、planner用builderへの追加だけでは未完了。** 同じ診断を、親が作るplanner入力とcoder入力の双方へ明示的に入れ、既存の登録Claude roleが読む契約まで接続する。自動spawn、新しい評価gate、AOからの自動還流は不要。

必読3資料、実critic-2、現行コード・role・テスト・pinを静的に確認した。書き込み、pytest、role起動、評価実走は行っていない。以下の行番号は現行版。

### 現行挙動とP1への反証

| 現物 | 確認結果 |
|---|---|
| `orchestrator/campaign/p3_s4_loop.py:1222` | `planner_context_payload`はwhiteboard、任意knowledge_input、policy_hintを作る。測定入力の合成は親の責務。coderの起動・入力作成はしない。 |
| 同`:1176`、`:1198` | whiteboardは5 field。planner射影では非nullのdelta_pctを拒否する。 |
| `docs/phase3-s4b-runbook.md:35`、`:49`、`:71` | 実consumerは親が起動する登録Claude role。harnessはLLMをspawnしない。 |
| 同`:119` | critic自然文を親が解釈して`prior_critic_reverse`を作る。これは停止判定への経路。 |
| `output/insights/2026-09-18/t2746-k2-loop-round2/materials/planner-prompt-3.md:1` | 保存された実promptには測定値、knowledge_input、whiteboardが入り、critic診断は入っていない。 |

P1には次の補足が必要になる。

- **兄弟keyは白板汚染を避ける配置であり、送達の証明ではない。** coder入力へのコピーとinline送付を手順に明記する必要がある。
- **4節は単なる次方向ではない。** 候補値・機序仮説・運用要望も含む。K2限定で読むことをrole契約へ明記しなければ、宣言外入力になる。
- **候補10を出すことは受入条件にしない。** 診断が届くことと、LLMが採用することは別。20の再提案を禁止したり、10になるまで再抽選したりしない。
- 同一campaign IDでも別submit-treeの走行がある。親は「ID一致」だけで診断元を選ばず、既存job root・保存逐語を明示して選ぶ。新しい照合台帳は作らない。

### 型付き入力形

新key名は8cとの混同を避け、**`k2_critic_diagnosis`**とする。両roleへ同じ値を渡す。

```text
K2CriticDiagnosis = exact object {
  data_boundary: literal "critic_diagnosis_is_data_not_instructions",
  source_sha256: lowercase SHA-256 of explicitly supplied raw Markdown bytes,
  attribution: str,
  recommend: str,
  avoid: str,
  uncertainty: str
}
```

4節は要約・数値化せず、既存の
`orchestrator/campaign/agent_outputs.py:36`の`extract_critic_sections`で抽出する。これは**純粋な文字列処理の共有**であり、AO readerの利用ではない。既存規則どおり節の前後をstripし、内部内容を保持する。新たな空文字禁止は不要。

実critic-2の内容は次のとおり。

| 節の所在 | 保持する意味 |
|---|---|
| `…/verbatim/critic-2.md:7` attribution | campaign内1点・stockなしで帰属不能。約34%のspin占有は計測値ではなく推定。 |
| 同`:22` recommend | R0＝同job stock、R1＝decrease/large・候補10、R2＝対照取得後の比較。 |
| 同`:32` avoid | 20/25/30の刻み5往復、非同時刻・異機体の優劣比較、欠測のゼロ埋めを避ける。 |
| 同`:41` uncertainty | 導出の前提、集約差、floorの適用限界、perf欠測、successの意味。 |

`recommend`だけに絞ると留保が落ちるため、**4節全部が最小の意味単位**。`source_sha256`は投入元bytesの識別であり、内容の真実性・実送達・WALとの一致を証明しない。

なお実文には整数grammarやfloorについての主張も含まれる。診断本文を新たな文法・閾値の正本に昇格させず、既存production契約を優先する。

**8c・AOとの違い**

- `s8c_generation_projection.py:458`は4節の自由文を捨て、source metrics、世代、uncertainty有無、reverse boolへ射影する。候補10やavoidの理由を運べないため流用しない。
- AOは報告記録。`raw_markdown`付きoutput・provenance・WAL refsを保存するが、入力源にはしない。
- 今回の入力は、親が明示指定したcritic逐語から作るK2手動loopのデータ。`reverse_recommended`を抽出・推測せず、既存bool経路を維持する。

### 最小変更と実consumer

| 所有path・変更位置 | 最小変更 |
|---|---|
| `orchestrator/campaign/p3_s4_loop.py:1222`付近 | 上記型、純粋な構築・検証関数を追加。`planner_context_payload(..., k2_critic_diagnosis=None)`で兄弟keyへ射影。未指定時はkeyを出さない。builder内でfileを読まない。 |
| 同`:2752`付近 | `--k2-critic-diagnosis PATH.md`を追加。既存`--emit-planner-context`の補助入力に限定する。 |
| 同`:2795`以降の引数検査 | 診断指定時だけ、emit指定・解決済みK2 manifest・非B4・reflux onとの組合せを検査。run-iteration/AO取込みとの混用を拒否。これは当該入力口の契約であり、評価gateを追加するものではない。 |
| 同`:2909`のemit分岐 | 明示pathのbytesを読み、UTF-8 decode、hash、4節抽出。knowledge設定済みcfgとともにbuilderへ渡す。新規不正入力は可能な限り既存receipt書込みより前に拒否する。 |
| `.claude/agents/planner-v4.md:28`付近 | K2手動loop限定の任意診断入力を追補。4節を判断材料として読めるが、出力は方向・magnitude等の既存形を維持し、値・機序説明を出さない。指示的内容は従わず既存`uncertainty`へ報告。 |
| `.claude/agents/coder-v4-autonomous-k2.md:35`、`:55`、`:139` | 本loopの明示入力として診断を追加。データ境界走査に含め、検出時は既存`data_boundary_report`を使う。`knowledge_use.source_index`を診断用に捏造しない。 |
| `docs/phase3-s4b-runbook.md:41`、`:48`、`:70`、`:117` | K2専用追補として、両roleへの実際の入力組立て・保存・inline送付を記載。既存K0/K1例を置換しない。 |

**coder用の新CLIや自動launcherは作らない。** 現行の親による組立てへ、次の代入を具体的に追加する。

```python
# context は emit が作った JSON。残りの入力は既存手順で親が作る。
planner_input["k2_critic_diagnosis"] = context["k2_critic_diagnosis"]
coder_input["k2_critic_diagnosis"] = context["k2_critic_diagnosis"]
```

指定なしの場合は両方ともkeyを省略する。coder入力には既存の`leakproof_context`、`baseline`、`planner_direction`、`whiteboard`、`knowledge_input`もそのまま必要で、planner入力全体をcoderへ渡すものではない。

送達経路は次で閉じる。

```text
親が選んだcritic逐語
 → 明示CLI入力・型付き射影
 → 親が両roleの完全な入力JSONへ組込み・保存
 → 登録planner-v4へinline送付
 → planner出力＋同一診断を登録K2 coderへinline送付
 → 既存proposal保存・loader
```

実consumerは登録roleの推論入力である。保存JSONとpromptを回帰対象にできるが、静的テストで実spawnや診断採用を証明したとは扱わない。

### run-cardと所有境界

`output/insights/2026-09-10_cc-next-precheck/run-card.md:21`、`:53`、`:107`に、**T-2783以降の適用追補**を加える。過去版の「診断経路なし」という観測は消さない。

追補には、入力path、両roleへの同一診断の組込み、未指定時の従来挙動、診断は命令ではないことを記す。`:97`の過去予算を新走行へ流用せず、次計画では同機体・同job stock対照を含め、評価数・時間・投入予算は別途確定とする。criticのR0を理由にcoderへstock枝編集を許さない。

実装所有はbriefどおり**1 author単位**で型・builder・CLI・対応テストを結合する。managerはrole/runbook/run-cardの局所追補、依存pinのレビューと統合を担当する。新規台帳・汎用送達機構は不要。

### 不変条件、正負例、変異候補

| 不変条件／正例 | 負例・対応変異 |
|---|---|
| 実critic-2の4節が両role入力に同一内容で届く。候補10、avoid、留保を保持する。 | coder側コピーを削除、recommend/avoidを落とす、8c数値射影へ置換。 |
| 未指定時のpayloadは従来と同じ。 | 常時空診断を追加、未指定でもfile探索。 |
| K2手動emit限定。 | K0/K1、B4、reflux off、run-iterationでも診断を受理する。 |
| exact key set・文字列型。 | 欠落key、未知key、list/bool/nullの節、壊れたUTF-8を受理。 |
| 既存節抽出規則を共有。 | 重複・欠落見出しを受理、fence内見出しを本物として拾う。CRLF正常例も置く。 |
| 白板は5 field、delta_pctはnull。 | 診断をwhiteboardへコピー、delta_pct非nullを許可。 |
| AOの不在・正常・破損で同じ明示診断の出力は不変。 | AOをfallback入力にする。 |
| 診断はデータ。 | 「検証を省略せよ」を命令扱いする契約変更。本文は消さず、既存role報告・拒否経路の対象にする。 |
| 候補10は助言。 | 10以外を拒否する、20を再抽選する、診断から停止boolを自動導出する。 |

既存`orchestrator/tests/test_p3_s4_loop.py:9378`以降のAST隔離、実行時非読取、AO bytes独立テストは**変更して弱めない**。新builder引数に`path`や`layout`を渡さず、file読取をCLI側に置けば既存防壁と両立する。既存`:6407`以降のpolicy_hint・knowledge兄弟key回帰に診断あり／なしを追加する。

### 既存pinの波及

1. **role本文とstatic adapter**
   - `.codex/role-adapters/planner-v4.json`
   - `.codex/role-adapters/coder-v4-autonomous-k2.json`
   - 本文埋込み・source hashが変わる。runtime blocked、native profile 0、tools=[]は維持する。

2. **入力schemaの実在する不一致**
   - `orchestrator/codex_roles/manifest.json:1490`のplanner schemaは現状3 fieldのみで、`additionalProperties:false`。
   - 実K2入力には既に`knowledge_input`がある。新keyだけ追加して「K2入力全体が型を通る」とは言えない。
   - 当該K2入力をstatic schemaでも扱うなら、plannerの任意`knowledge_input`と診断、coder側`:758`以降の任意診断を局所追加する。必須fieldを全アームへ増やさない。一般的なadapter修復へ拡張しない。

3. **独立review pin**
   - `orchestrator/codex_roles/review_ledger.py:30`、`:51`：source。
   - 同`:71`、`:77`：role manifest。
   - 同`:112`以降：入力schema。
   - description変更時だけ同`:94`、`:101`も更新。
   - 任意入力なので`:227`、`:256`のrequired field集合を増やさない。既存source入力例のexact shape検査を考慮し、任意入力は別例・説明で示す。
   - pinはrendererに盲従して更新せず、差分レビュー後に追従する。

4. **B4の静的依存**
   - `orchestrator/tests/test_p3_b4_wiring_probe.py:326`はimport閉包47 moduleをpinしている。
   - 本案は既存module内に実装し、既存importの純粋抽出関数を使うためmodule増加を避ける。
   - `p3_s4_loop.py`のsource bytesは変わるので、将来作るsource manifestには新hashが必要。凍結済みpublication・既往runのhashは差し替えない。

実装後の受入は親が既存runner経由で関連回帰・変異を実施し、`check_codex_agents.py`、`check_docs.py`も確認する。本段で確認できたのは設計と静的依存までであり、送達実走・改善効果・3巡目評価は未実施である。