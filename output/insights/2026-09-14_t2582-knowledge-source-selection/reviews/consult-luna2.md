## M-01 — 規律の掲載先と manifest 作成時の導線がつながっていない

- **判定: real。** `CLAUDE.md:37` 以降の起動順は現行 phase の該当節へ進み、`docs/phase3.md:372` は実走手順として段4b runbook を指定する。しかし同 runbook には K2 節への参照がない。driver の help も `orchestrator/campaign/p3_s4_loop.py:2572` の「commit/path/raw-byte SHA を検証して条件付き bind」までで、選定規律へ誘導しない。`docs/README.md:78` に architecture の一般索引はあるが、同書冒頭は毎セッション必読ではないと明記する。**plan の「K2 節だけ」では、manifest 作成時に読む契機を欠く「恒真な文書」になる。**
- **成果物への影響:** 設計説明入り source の再投入を防ぐ運用上の差分が届かず、既知の consumer 停止が再発し得る。既存 certified 判定を変える問題ではなく、次の評価結果・WAL が得られない問題である。
- **最小修正:** runbook の入力構築前に「K2 manifest を作成・差し替える場合は `docs/agent-architecture.md` §coder-v4-autonomous-k2 の『manifest 作成側の知識源選定』に従う」という参照を一つ置く。本文は複製しない。これは scope 内の docs 差分であり、新節・新機構は不要。brief の「新節が要る＝名指しの変更を超える」という推論は成立しない。

## M-02 — 「測定記録」の定義が機械生成の説明文を扱い切れていない

- **判定: real。** plan:22–28 は観測値・判定・対応情報を許し、人間／AI の「自由文フィールド」を除く。しかし機械が固定テンプレートから出力した運用説明の扱いが明示されていない。

指定された4ファイルはすべて実際に開いた。以下のパスは `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/` 相対である。

| ファイル | plan の定義による判定 |
|---|---|
| `campaign.lock:1` | **対象外。** `spec_content` が planner・coder・critic の振る舞いを説明する自由文。 |
| `loop_state.json:2` | **対象内と読む。** 試行番号と型付き方向・magnitude・結果の対応記録。方向は AI 由来でも自由文ではない。生成元は `p3_s4_loop.py:1176`、保存形は同:1318。 |
| `runs/wal.jsonl:1` | **対象内。** 全15レコードは build・verify・bench・commit の記録。コマンド文字列も実行条件の記録であり、それだけで自由文説明とは扱えない。 |
| `s4_loop_digest.txt:35` | **判定が割れる。** 測定表・集計結果としては対象内だが、「異常かどうかは読み手が stock 対照比で判断」という運用説明も含む。これは `orchestrator/critic/digest.py:1597` の固定文で、自由文フィールドの単純な除外では分類が定まらない。 |

- **成果物への影響:** 運用者によって digest を選ぶか WAL を選ぶかが変わり、manifest digest・source 参照・受領証が変わる。digest の実投入で指示検出が発火するかは未実測であり、断定しない。
- **最小修正:** 「機械生成の固定文でも、読み手の振る舞いを定める設計・運用説明が同居する成果物は選ばない」と選定本文を明確化する。digest を加工せず、既存 WAL を選ぶ。ファイル名の許可リストにはしない。

## M-03 — brief の「運用文書に無い」には現物の反証がある

- **判定: real。** `docs/phase3.md:379` が指す `output/insights/2026-09-10_cc-next-precheck/run-card.md:40` 以降は、wal-only manifest、source の commit/path/hash、WAL 1件を具体的に指定する。同:46 は「全文を解決して使い、設計説明の混入・指示検出をすり抜ける加工はしない」と既に書いている。brief の「その判断は運用文書に無い」「書かれていないので次の K2 走行は…再び止まる」は広すぎる。
- **成果物への影響:** この誤認単独で値が変わることは**示せない（nit）**。ただし、既存 run-card に従う次走と、新しい manifest を作る将来走を混同している。
- **最小修正:** 純増を「個別 run-card にある選定判断の常設規律化と導線追加」と訂正する。歴史的 run-card の入力指定を変更したり、規律本文を再掲したりしない。

## M-04 — 既存の知識境界の言い直しだけで純増ゼロ、という疑い

- **判定: refuted。** `docs/agent-architecture.md:118` は受け手の利用可能範囲、`docs/roadmap.md:29` は出所の記録と信頼境界を定める。D1429（`docs/decisions.md:45351`）、D1493（同:46590）、D1559（同:48118）は束縛・検証責任・射影の契約であり、投入ファイルを測定記録へ限定する選定規律ではない。送り手に適用する具体化には純増がある。
- **成果物への影響:** 重複による値・受理集合の変化は**示せない（nit）**。
- **最小修正:** 選定義務・判定境界・正本への参照に絞る。routing 5（`docs/skill-self-improvement.md:36`）は全文複製を禁じるが、M-01 の参照追加を禁じていない。

## M-05 — アンカー・byte 予算・whole-file pin の再検証

- **判定: refuted（一部説明不足）。** A1 の節名と「構造遮断は撤去しない」bullet は現物の `docs/agent-architecture.md:105`、同:126 に一致する。`tools/check_docs.py:148` の living doc 列挙、同:6722 の行番号参照禁止、同:6728 以降の現況表記・pin literal・D番号・パス検査も確認した。反映先を対象とする byte 予算や whole-file SHA-256 pin は確認されなかった。whole-file pin の適用先は同:6568、同:6574 の cleanup 系などであり、architecture ではない。
- **成果物への影響:** architecture の予算・pin が編集を阻むという問題はない。brief の予算対象一覧には dev-wave 層予算（同:354）等の省略があるが、成果物影響は**示せない（nit）**。
- **最小修正:** 「反映先は予算・whole-file pin の対象外」と限定して記す。A2 の `docs/spool/` は既存 bullet ではなく段7の記録先指定として区別する。なお、docs 検査の緑は M-01 の導線や M-02 の意味を保証しない。

## M-06 — docs-only では閉じず、実装変更が必要という疑い

- **判定: refuted。ただし plan の編集範囲では不足。** `knowledge_manifest.py:428` は指定 blob の bytes と digest を検証し、同:490 は本文を射影する。`p3_s4_loop.py:1520` は既存 manifest を読み、同:1531 以降で identity・受領証へ束縛する。適合する既存 WAL を選ぶ経路は存在する。
- **成果物への影響:** source 選択によって manifest digest・campaign identity・受領証の参照は変わるが、正しさ・identity・性能ゲートの受理規則を変更する必要はない。
- **最小修正:** M-01 の参照と M-02 の定義を docs 内で補う。driver help の変更、producer／consumer の変更、新しい検査は必要条件ではない。

## 総括

blocker 級は M-01 の作成時導線欠落と M-02 の測定記録の分類穴。
plan はそのまま採用不可。規律本文一か所＋runbook の参照一つで修正できる。
brief の既存被覆評価は、個別 run-card の現存を踏まえて訂正する。
docs-only は維持可能。ファイル変更・commit・検査実行は行っていない。