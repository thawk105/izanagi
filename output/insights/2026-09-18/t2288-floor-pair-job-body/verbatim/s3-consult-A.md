## 所見

以下の `driver:行番号` は `orchestrator/campaign/floor_pair_driver.py` を指す。静的読解のみで、実行結果は主張しない。

1. **3 段同一 HEAD は、現計画では運用条件であり、投入時の機械保証ではない。 — must-fix**

   **対象:** brief「不変条件」・P4/P5、plan §1 checkout・§3・§8、driver:1212、2229–2234、2700–2722。

   submitter は投入のたびに現在の HEAD を取得するため、w1 を H1、w2 を H2 から投入すると、各 job の `HEAD == FP_EXPECTED_HEAD` と driver の `runtime_head == loaded_head` は両方通る。`loaded_head_mismatch` は同一呼出し内の変化を検出するもので、w1 と w2 の HEAD の違いは検出しない。finalize の header 照合で初めて拒否される。

   誤りは、brief が `loaded_head` 検査を「3 段同一 HEAD」の予防的な権威として扱う点。plan の同一 detached checkout を維持する運用は正しいが、機械的には固定されない。最低限、この境界を明記し、H を固定した checkout を途中変更しない手順を必須にする。実装で予防するなら、w2 の投入前・job 起動前に既存 w1 header の HEAD と照合する狭い前段検査が候補となる。driver の全 validator の複製は不要。

   **成果物への影響:** H1/H2 の窓 JSONL が双方 create-only で確定すると、どちらの HEAD で finalize しても整合せず、summary・集約へ進めない。

2. **finalize は terminal 欠落を拒否するが、`incomplete` terminal は受理して summary を作る。 — must-fix（説明の訂正）**

   **対象:** brief P3/P4、plan §3「両窓の完全性…は driver に任せる」・§8 P3、driver:2679–2686、2737–2746、2772–2789、2808–2814、3006–3011、3083–3087。

   現物は両窓について予定 session の exact な列と terminal を要求する。したがって、未作成・書込み途中・terminal 無しの窓を渡した早すぎる finalize は、summary を確保する前に拒否される。この経路で summary が `not_generated_*` として先に作られる、という懸念は成立しない。

   一方、FATAL 後は残りを `not_run` として埋め、`incomplete` terminal を書く（driver:2275–2297、2323–2339）。この構造的に完結した失敗窓は validator を通り、`not_generated_missing_samples` の summary が作られる。欠測率超過等でも summary は作成される。plan の「完全性」は「正常完了」と誤読できるため訂正が必要。

   これは既存 driver の失敗記録契約であり、成功窓だけに finalize を限定する変更は勧めない。失敗 summary も一回限りであることを投入手順に明記する。

   **成果物への影響:** terminal 欠落なら summary path は温存されるが、妥当な失敗 terminal なら summary path は消費され、成功 summary への再生成には使えない。

3. **10h を超える走行が必ず欠測率で不採用になる、という P2 の理由は成立しない。 — must-fix**

   **対象:** brief「所要の実測分布」・P2、plan §8 P2、凍結 spec の `reps=5`・`timeout_s=120`、driver:1970–2019、2133–2182。

   本走の予定 rep 数は、1 窓につき `62 × 2 side × 2 measurement × 5 rep = 1,240`。較正時の 3.5〜4.5 秒を掛けた 1.21〜1.55h は算術的には整合するが、本走全体の実測分布ではない。brief 自身が同一 regime を主張しないと書いた点は正しい。

   P2 の「44.4h の regime は 5% 判定で不採用」は、10h 上限の十分な根拠にならない。例えば全 rep が成功しても各 30 秒なら bench だけで約10.33hとなる。欠測率は経過時間の上限ではない。

   また「全 probe timeout」「全 rep timeout」は全予定呼出しへの予算の外挿として扱うべきで、実際には probe 失敗で測定が省略され、最初の測定失敗で次の測定が省略される。44.4h を実経路の厳密な最悪時間とも呼べない。

   plan が10hを「成功保証でない運用上限」とした訂正は支持する。ただし採用可能な窓も失いうると明記する。決定材料は、同じ workload・records・binary・node/割当条件での rep wall の裾、probe・初期化・検証・JSONL fsync の時間、session/窓全体の wall と要求時間の関係である。本 wave では測らず後続へ残す。

   **成果物への影響:** 欠測率条件を満たしうる走行でも10hで中断され、terminal 無しの JSONL と未生成 summary が残りうる。

4. **窓の不等号は条件付きで正しいが、walltime と実時計の前提が不足している。 — should**

   **対象:** brief P4/P5、plan §2、driver:2091–2106、2273–2286。

   `now >= not_before` と正の `duration` に対する `now + duration <= not_after` は、採取した `now` を半開区間内に置く。さらに、全 session 開始時刻 `s` が `s < now + duration` を満たすなら、`s < not_after` が従う。したがって `<=` 自体を誤りとはしない。

   ただし `elapstim_req` は要求値であり、それだけで driver の session 開始に厳密な締切を設けるものではない。実際の walltime 起算・終了猶予・signal 配送が未確認なら、この十分条件の前提は未証明である。`date +%s` の秒未満切捨てと driver の高精度時刻の差も、等号境界では無視できない。

   queue 待ちは compute 側の再検査で吸収できる。plan §2 の「scratch 後、driver 直前にも…呼べば」は実装要件に確定し、拒否時は driver 未起動を検査する。ただし loader 実行や時計の前進・後退まで含む無条件保証にはならない。

   `date -u` と timezone 付き ISO の変換は TZ に依存しない。login と compute の時計差は compute 再検査で一部吸収されるが、compute 時計の正確さ・走行中の安定性までは確認しない。末端を避ける運用余裕と未検証の前提を明記する。

   **成果物への影響:** 再検査後に窓外へ達すると、driver は JSONL 作成後に `outside_window` を記録し、その窓を消費する。

5. **別 nonce の二重投入を nonce directory は排除しない。ただし同一 path の上書きは driver が防ぐ。 — should**

   **対象:** brief P1/P4/P6、plan §3、driver:517–535、1685–1691、2273。

   nonce は attempt の識別子であり、spec × window の一意性ではない。二つの submitter は別 nonce で同じ窓を投入できる。window 成果物の存在確認も plan にない。

   同じ checkout・同じ path なら `O_EXCL` により一方だけが writer となり、敗者は測定ループへ入らない。従って「二重投入で既存 JSONL が truncate される」は成立しない。ただし先着 job が失敗しても後着 job は引き継げない。

   既存 JSONL の不在確認を submitter/job に加えるのは無駄な投入の早期拒否として有用だが、同時投入を排除する検査ではない。新しい台帳や予約機構を要求せず、同一 spec × window は一回だけ投入し、不明な qsub 結果を自動再投入しない運用を明記する。別 checkout では実 path が異なり、`O_EXCL` による相互排除もない。

   **成果物への影響:** 同一 checkout では先着一件だけが path を消費する。別 checkout では同名の競合する実験証拠が生成されうる。

6. **前段検査は実際に driver 検査と重複する。変異の検出範囲を分けて説明する必要がある。 — should**

   **対象:** brief「規律2」・P4/P5/P10、plan §1末尾・§5/6、D2069 理由節、driver:1232–1241、1666–1682、2111–2117、2229–2234。

   spec SHA、HEAD、binary SHA、site の検査は意味として重複する。「driver の検証実装はコピーしない」ことと「同じ不正入力を前段で拒否する」ことは別である。driver 側の検査を削除した変異を全 script の負例で試すと、前段拒否に隠れて検出できない場合があり、D2069 の指摘がそのまま当てはまる。

   ただし D2069 の具体的な複製禁止は `place → store_binaries` の経路である。本件の早期拒否を一律禁止する根拠とはしない。前段には無駄な割当てを避ける役割があり、driver の検査を削除・置換しない限り、規律2の緩和にもならない。

   M1〜M6 は shell・登録簿・文書の契約を検出するものとして報告し、driver の検査強度を証明したと扱わない。driver の変異は driver に直接到達する既存検査で評価すべきである。

   **成果物への影響:** 現計画だけで成果物が改変されるわけではないが、検査の効力を誤認すると、将来の driver 検査欠落を見逃しうる。

7. **signal 対応と create-only は、成果物の完結性を保証しない。summary の書込み途中死も残る。 — 情報**

   **対象:** brief P5、plan §1 trap・§7、driver:1694–1713、2324–2339、3086–3087。

   plan の「shell から追加 kill を送らない」「SIGKILL まで receipt を保証しない」は正しい。writer は途中のファイルを削除せず、レコードを書いて fsync する。window だけでなく、finalize が summary を exclusive-create した直後の障害でも空または部分的な summary が残りうる。

   job-result の保存や driver rc の回収は、凍結成果物の修復にはならない。救出のために既存出力を削除・再実行する手順は追加しない。

   **成果物への影響:** terminal 無しの JSONL、または不完全な summary が永久に path を占有し、正常な集約材料が揃わない。

8. **`--assume-now` 不採用は支持する。ただし dry-run 専用注入が必ず実投入を偽装するわけではない。 — 情報**

   **対象:** brief P8、plan §2/3/5、driver:2091–2092、3132–3138。

   plan は CLI に時刻注入を設けず、純粋関数の snippet に限定している。実投入は実時計、driver も `_utc_now` を使うため、今回の設計にその seam はない。

   仮に導入しても、非 dry-run で必ず拒否し、dry-run から qsub に到達せず、job へ注入時刻を伝播しないなら、直ちに実投入の迂回にはならない。ただし追加の分岐と検証責任が生まれ、今回は必要性がない。不採用が妥当である。

   **成果物への影響:** 計画どおりなら注入時刻による凍結 JSONL・summary の作成はない。

9. **所有範囲の訂正と実測境界は plan が妥当。ただし brief の「止めているのは job body だけ」は限定すべき。 — should**

   **対象:** brief「研究前進」・P6・起動確認、plan §3/7/9、F660、D1974、driver:3140–3144。

   P6 は submit receipt 等を同じ leaf に置きながら「投入側は mkdir 以外置かない」とする矛盾がある。plan のファイルごとの所有分担が正しい。

   plan は qsub 受理・env 伝播・compute 正例・実 signal 配送を未観測としており、「実装したふり」は認めない。login hook が先に拒否した場合も、hostname gate 到達と区別している。F660 の後半には既登録 generic による別 probe の例外があるが、今回の新規 job body の実測禁止を迂回する根拠にはならない。

   brief の「job body だけ」は不足している実装部品の説明に限定する。実走には admission、binary の可用性、時間予算、同一 H、証拠確認がなお必要である。driver rc=0 と床値生成成功の区別も plan §9 のとおり残す。

   **成果物への影響:** 契約検査の成功だけでは JSONL・summary・集約の生成も採用も確定しない。

## 経路表

| 経路 | submitter が止める段 | job body が止める段 | driver の最終挙動 | 未被覆部分の分類 |
|---|---|---|---|---|
| (i) 投入時点で窓前・残時間不足 | §3 時刻 gate | §1 time、§2 再検査 | 呼ばなければ JSONL 未作成 | **実装で止めるべき**。直前再検査を必須化 |
| (i) queue 待ちで窓外・残時間不足 | 止めない | compute 実時計の再検査 | 同上 | **実装で止めるべき** |
| (i) 最終再検査後の時計変化・終了猶予中の窓逸脱 | 止めない | 全 session は監視しない | 作成済み JSONL に `outside_window`、残り `not_run`、`incomplete` terminal | 時計・末端余裕は**運用に残す**。実 scheduler の確認は**scope 外** |
| (ii) walltime・SIGTERM・node 障害による途中死 | 10h の要求のみ | trap は完結を保証しない | terminal 無しの JSONL が残り、再作成不可 | 復旧機構は**scope 外**。時間予算の限界は**運用に残す** |
| (iii) 同一 spec × 窓、別 nonce、同一 checkout | nonce gate は止めない | identity/time gate は止めない | `O_EXCL` の先着のみ作成。敗者は測定前に拒否 | 一回投入は**運用に残す**。既存出力の早期拒否は **should** |
| (iii) 同一 spec × 窓、別 checkout | 止めない | 止めない | 異なる実 path のため両方作成可能 | 同一測定 checkout の維持を**運用に残す** |
| (iv) 窓未作成・terminal 無しで finalize | summary 不在だけでは止めない | 専用 readiness gate 無し | 両窓検証で拒否、summary 未作成 | 保護は既存 driver で成立。投入順は**運用に残す** |
| (iv) 両窓が構造的に完結、一方が `incomplete` | 止めない | 止めない | `not_generated_missing_samples` summary を作成 | 既存の失敗記録契約として**運用に残す**。説明訂正必須 |
| (iv) summary 作成中の障害 | 止めない | trap では修復不能 | 空・部分 summary が path を消費 | 救出・再凍結は**scope 外** |
| (v) 投入後、job の HEAD 検査前に H が変化 | 投入時以降は見ない | `HEAD != expected` で拒否 | 未起動なら出力未作成 | **実装で止めるべき**。計画にある |
| (v) loader 後から runtime 検査までに H が変化 | 止めない | 既に検査済み | `loaded_head_mismatch`、JSONL 未作成 | 既存 driver で保護 |
| (v) w1=H1、w2=H2 を別々に正常投入 | 各回の現在 H を受理 | 各 expected H を受理 | 両 JSONL を作成。finalize header 照合で拒否 | 同一 H は**運用に残す**。予防するなら既存 w1 header 照合を実装 |
| (v) job の HEAD 検査後、loader 前に H が変化 | 止めない | 再検査なし | loader/runtime が共に新 H なら一致しうる | checkout の走行中不変を**運用に残す**。module bytes の保証は**scope 外** |

## 裁定パッケージ候補

- **本走の時間予算:** 10h を成功保証のない上限として採るか。後続で同等条件の時間証拠を得る方法、採用可能な窓も失う限界、途中死後は上書きしない扱いを一組にする。
- **着地後の実行経路確認:** main 登録後の実 qsub、8 変数の伝播、実効 walltime・signal 配送、compute 上の interpreter/import、receipt 保存。今回の静的契約検査と区別する。
- **凍結成果物を失った場合の扱い:** terminal 欠落・部分 summary・異なる HEAD の窓を保存し、失敗または未実施として記録する。窓延長・既存 path の削除による救出は行わず、必要なら別 commit の新しい凍結を扱う。
- **測定後の採用と集約:** D1974／申し送り6・7に従う n、欠測率、実 timestamp の24時間以上の分離、環境一致、D2138 の期待 spec 3 組による集約。正常な入力だけに間引かない。

これらは既存委任内で処理できる事項を含み、すべてを新しい人間承認事項にする趣旨ではない。

## 総括

plan は前段拒否・create-only・実測未検証の区別を概ね保っている。  
必須訂正は、3 段同一 HEAD の保証範囲、失敗 terminal からも summary が作られる事実、10h の根拠である。  
terminal 欠落時の早すぎる finalize は、現 driver が summary 作成前に拒否する。  
二重投入・途中死・時計と walltime の関係は完全には閉じず、経路表の運用条件と後続確認が必要となる。  
指定資料は読解済み。ファイル変更・pytest・qsub・実測は行っていない。