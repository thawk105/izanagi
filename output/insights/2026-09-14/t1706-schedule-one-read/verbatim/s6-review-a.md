## 契約との逐条照合

基準 `f5423e2` と照合しました。提供patchと現在の差分は一致しています。

| 条項 | 静的照合結果 |
|---|---|
| V2-1 | [`_artifact_path`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/tools/codex_reasoning_ab.py:9008)は原文一致。姉妹helperは署名・読み取り値の保持・返却値以外のASTが一致し、検査順序・rc・reasonに差を生む固定入力は構成できませんでした。`read_bytes()`は1箇所です。 |
| V2-2 | [7634行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/tools/codex_reasoning_ab.py:7634)の既存枝、7639行のfresh枝ともfrozenの読み取り値がauthorityです。`run-root schedule bytes changed`と`RC_ROUTING`は不変です。 |
| V2-3 | [11170行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/tools/codex_reasoning_ab.py:11170)で取得したbytesを解析・SHAに使用。manifest SHA、frozen path、mtime、launch SHAの検査は残っています。 |
| V2-4 | [11733行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/tools/codex_reasoning_ab.py:11733)のinline枝と旧packet-only経路に変更はありません。 |
| V2-5 | 3入口ともschedule解析に`data=`を指定しています。変異検証の契約不一致は所見2です。 |

1. **nit — 差し替え位置が段4裁定の「SHA算出直後」と異なる。**
   **file:line:** [test_codex_reasoning_ab.py:1965](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:1965)
   wrapperは最初のreadの返却前にBを書きます。実際のSHA算出はその後のproduction 9057行／7640行です。したがって段4のB-1で指定された差し替え時点を再現していません。
   **成果物への影響:** 指定した観測時点の検証証跡にはなりません。ただし、この時点差だけで今回の変異検出が失われる反例は確認できず、nitとします。

## 受理集合への所見

固定された読み取り可能なファイルについて、受理・拒否・rc・reasonの差は構成できませんでした。

- 非canonicalな空白、末尾改行、BOM、非UTF-8列、重複key、空ファイルは、従来と同じbytesが同じ`json.loads`へ渡ります。SHAも再serializationを介しません。
- [`_load_json_object`:8976](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/tools/codex_reasoning_ab.py:8976)は`data is None`判定です。省略時は従来のread・例外処理を通り、`b""`は再読せず解析エラーになります。
- path帰属はsupervisorの7641行、replayの11173行、packetsの11738行で追跡しました。各pathに対応するreadの返却bytesを渡しており、source bytesをfrozenのpath名で解析する呼び方はありません。
- 巨大ファイルにもサイズ制限や解析方式の変更はありません。ただしbytesの保持期間は延びるため、メモリ枯渇を含めた挙動同一性までは静的検査で保証できません。

## 既存テストの保全

基準版のテスト関数定義は**418件**、変更後は**420件**でした。削除・改名・同名重複はありません。

追加された[1944行以降](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:1944)のclass、helper、テスト2関数を除くと、**テストモジュール全体のASTが基準版と一致**します。既存の期待値・decorator・fixtureを緩めた変更は検出していません。

## 実装子の自己申告の裏取り

M1〜M6の表にある「readが2となり、[2119行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:2119)で落ちる」は、各変異の制御フローと整合します。

| 変異 | 静的に追跡した追加read |
|---|---|
| M1／M2／M3 | `data=`を外したloaderがBを再読 |
| M4 | helperのreturnでBを再読 |
| M5 | replayの後段SHA算出でBを再読 |
| M6 | supervisorのSHA算出でBを再読 |

実測値自体は再検証していません。

2. **must-fix — M4・M5の単一理由性が未達のまま変異検証を完了扱いしている。**
   **file:line:** [test_codex_reasoning_ab.py:2119](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/orchestrator/tests/test_codex_reasoning_ab.py:2119)、[codex_reasoning_ab.py:11188](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1706-impl/tools/codex_reasoning_ab.py:11188)
   M4ではhelperがBを返すため、解析も後段SHAもBになります。一方manifest・launchはfixtureでAに結び付けており、既存SHA検査でも拒否されます。さらにread計数assertionを除いても、2125行の`duplicate slot_id: s01`期待が失敗します。M5もAのduplicate拒否に加えてBのSHAによる別理由が生じます。
   これは[stage4-ruling.md:119](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t1706-schedule-bytes-toctou/dev-wave-job-t1706/stage4-ruling.md:119)の単一理由性・再照準条件を満たしません。実装子の「単一とは主張しません」という留保は正直ですが、契約の履行にはなりません。
   **成果物への影響:** M4・M5の赤を、要求された独立したgate検証の完了証拠として採用できません。既存の静的正例などへ変異の検証先を再照準し、単一理由性を確認する必要があります。

共有fixture consumer未登録という報告は、指定資料だけでは登録側を独立確認できません。解消済みとも扱っていません。

## 総括

**blocker 0件、must-fix 1件、nit 1件。**

最も危険なのは所見2です。read計数による検出と、契約が要求した単一理由の検証が混同されています。productionの固定入力に対する正しさの退行は、確認した範囲では構成できませんでした。

pytest・変異実走は行っていません。