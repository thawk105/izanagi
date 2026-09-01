---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t1712-exclusion-invisibility
seq: 1
title: [T-1712] 除外 2 field の対照実験を launch contract の面で実測した — 不可視性は証明されず、事前登録本文も D834 も据え置く (コード + テスト + insight、branch worktree-dev-wave-t1712-exclusion-invisibility、変異 6/6 KILLED)
---

## 本文

- D972 のユーザー裁定「先に対照実験で測る」に対する実測。除外している 2 field
  (`argv.mcp_config_path`、`kwargs.cwd`) を操作変数にし、それ以外の明示 call arguments と
  role 向け候補面が byte 一致するかを測った。実装は既存 test file への 589 行の純追加で、
  production code・事前登録本文・除外集合の文言はいずれも変更していない。
- **結果は緑だが、これは不可視性の証明ではない。** 段 3 の敵対検証が D962 と D833 を持ち出し、
  親の当初 brief が「実測すれば事前登録本文へ書ける/書けないを決められる」と一般化していた点を
  覆した。D962 は argv / stdin を「送る依頼の本体」と再定義することを禁じ、D833 は
  「test double の runner 境界で見た同一性を provider request の byte 同一性と呼ぶ」ことを
  却下済み選択肢として明記している。さらに事前登録 §4 の領域 (iii) は
  「role からも provider の応答からも不可視」という連言であり、fake runner は provider 応答を
  持たないため後者も測れない。**したがって今回の結果は連言のどちらも満たさない。**
  D834 の「role からの不可視性は未証明である」は据え置き、`docs/phase3-8c-preregistration.md` の
  本文は変更せず、B-6 は「変化なし」のままとする。親はこの一般化を段 4 で撤回した。
- 段 6 のレビューが 3 件の real を出した。(1) 比較 helper が面を落としても緑になる
  (`raw_call_arguments` の `"timeout"` を `None` に潰す 1 行変異が生存する)、(2) treatment が
  除外 2 field 以外に artifact root と invocation ID も変えており因果帰属が弱い、
  (3) fail-fast のため否定的結果のとき最初の差分より後ろが「未到達」か「問題なし」か
  区別できない。3 件とも fix で閉じた。(3) は**実測が不可視性を否定した場合に全体像を
  正直に書けるようにするため**の修正である。
- レビューが挙げた `_Runner` の positional / keyword 区別の欠如は**直さないと裁定した**。
  本 wave が持ち込んだ欠陥ではなく共有 helper の既存の限界であり、production は positional
  呼出しなので keyword 化は仮想リスクである。要求外の仮想リスクへ gate を足さず、
  代わりに主張の側を狭めた — 記録では「exact な呼出し形まで固定した」とは書かず
  「runner が受け取った値を比較した」と書く。
- artifact root の 3 分離は残した。`invoke` が `artifact_root/payload_{invocation_id}.json` を
  O_EXCL で作るため同一 root では 2 回目が失敗する。artifact root は argv・env・cwd・stdin の
  どの観測面にも現れないため交絡源にならない。invocation ID は 3 capture で共通にした。
- 「変えない条件」は provider を `close()` して neutral root を消してから同じ pathname を
  作り直す時系列で作った。`_write_bytes_bound` の O_EXCL と「neutral cwd は invocation ごとの
  空 directory」の両方を通る。`tempfile.mkdtemp` の差し替えは、pathname を決める注入 seam が
  provider に無いため最後の手段として採った (DW-O14)。
- 変異は 6/6 KILLED、MISMATCH 0、baseline PASSED。うち 5 件は既存 T-1354 テストも同時に落とすため
  冗長 gate と明記した。新テストだけが落とす変異は 1 件で、**除外対象でない argv 要素へ
  mcp path の「長さ」を漏らす**変異である。既存テストは全 provider の path 長が同じなので
  検出できず、新テストは control と treatment の path 長を変えているので検出する。
  当初「一時 directory の親を漏らす」変異が新テスト専用だと予測したが外れた
  (既存テストが env の key 集合を厳密に固定しているため)。予測を外した記録として残す。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 2、focus 1)。
  すべて `gpt-5.6-sol` / `xhigh`。子は sandbox で pytest を実走できず、実走はすべて親が行った。
- 逐語と変異台帳は
  `output/insights/2026-09-01_t1712-exclusion-invisibility-controlled-experiment/`。

## 次の一手差分

### 更新

- [T-1712] **P2・裁定済み (2026-08-26 /rulings 全件、測定を先行) — 測定は完了、結論は「書けない」**:
  除外 2 field の対照実験を launch contract の面で実測した (2026-09-01)。除外 2 field だけを
  変えても他の明示 call arguments と role 向け候補面は byte 一致し、path 値と canary の複製も
  観測されなかった。**しかしこれは D972 が問うた role 不可視性の証明ではない。** D962 は
  argv / stdin を「本体」と再定義することを禁じ、事前登録 §4 領域 (iii) は
  「role からも provider の応答からも不可視」の連言を要求するが、実 CLI 内部と provider 応答は
  この面から観測できない。したがって**凍結事前登録本文への field 列挙は依然として行えず**、
  D834 の「未証明」表記も据え置く。残る手番は、実 CLI が組み立てる remote serialization bytes を
  捕捉する観測点を設けるかどうかの設計判断であり、これは D962 が
  「独立した設計であり本裁定は塞がない」とした範囲である。
  base: f6df707719097302639609b00a96fdcca7ebdcfa30871e73f83c1dfa36e0fdfa

### 新規

- {{T:remote-serialization-capture-design}} **P2・新規 (ユーザー裁定待ち)**: 実 Claude CLI が
  組み立てる remote serialization bytes を捕捉する観測点を設けるか。D962 は捕捉機構を
  「独立した設計」とし本裁定では塞がないとした。[T-1712] の実測は launch contract の面で
  止まっており、これを設けない限り事前登録 §4 の領域 (ii) と (iii) は open のままである。
  設計上の制約として、外部 provider へ向けた通信の傍受は従量経路や代替 provider 配線を
  作らない形でなければならない。
- {{T:provider-response-invisibility-check}} **P2・新規 (ユーザー裁定待ち)**: 事前登録 §4 領域 (iii) の
  連言のうち「provider の応答からも不可視」を測る手段を設けるか。現行の対照実験は fake runner を
  使うため provider 応答を持たず、連言の片方も測れていない。
