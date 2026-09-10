## Ketsuron

Seiteki kensa no kekka, (A)(B) tomo genzai wa jisshi funou de aru. Pytest wa jissou shite inai tame, green no houkoku wa shinai.

Genzai tree dake de naku `git log --all`, `git rev-list --objects --all`, zen branch no tree mo kensaku shita ga, reviewed spec, manifest candidate, v2 generation, approval, active pointer wa ichido mo kakunin dekinakatta.

## 1. Jisshi suru baai no tejun

### (A) Reviewed spec shoudaku

1. Jissai no 8b preregistration ni motozuku candidate spec bytes o kakutoku shi, naiyou o review suru.

   - Schema validator wa `orchestrator/campaign/s8b_oracle_spec.py:105-179`.
   - Canonical serializer helper wa `orchestrator/campaign/s8b_oracle_spec.py:98-102`.
   - Genzai no repo ni candidate artifact wa nai.
   - Production no candidate producer, writer, CLI wa nai. Kono dan wa `keiro nashi`.

2. Review zumi no exact canonical bytes o `output/s8b-oracle-spec/reviewed_spec.json` ni oku.

   - Canonical path wa `orchestrator/campaign/s8b_oracle_spec.py:18-23`.
   - Production writer wa nai. Test-only writer wa `orchestrator/tests/s8b_oracle_spec_fixture.py:102-121` nado.
   - Jissai no reviewed bytes ga nai genzai, fixture kara no seisei wa review jittai o tsukuranai tame tsukaenai.

3. Exact raw bytes no SHA-256 o keisan shi, `APPROVED_SPEC_SHA256` ni literal de kinyuu suru.

   - Pin wa `orchestrator/campaign/s8b_oracle_spec.py:21-23`.
   - Loader wa pin fuzai, file fuzai, hash mismatch o `orchestrator/campaign/s8b_oracle_spec.py:182-200` de kyohi shi, canonical bytes to schema o `orchestrator/campaign/s8b_oracle_spec.py:258-275` de saikenshou suru.

4. Durable artifact contract o mitasu.

   - Genzai no test wa `output/s8b-oracle-spec/` no file o mujouken ni shuushuu shi, 1 file demo areba shippai suru: `orchestrator/tests/test_s8b_oracle_manifest_contract.py:128-144`.
   - `SCHEMA_VERSION` o kaeru dake dewa dame de aru. Kono test wa schema literal o sanshou shite inai.
   - D302 wa durable hakko go no henko ni schema bump to saihakko ga hitsuyou to sadameru: `docs/decisions.md:14018-14019`.
   - Seishiki na v2 schema migration nara `orchestrator/campaign/s8b_oracle_artifacts.py:20` kara no schema zentai koushin to, onaji kenshutsuryoku o motsu atarashii strict contract ga hitsuyou. Tada shi sono migration no existing function/CLI wa nai. Kono shoudaku turn dake dewa `keiro nashi`.

`build-approved` wa spec producer dewa nai. Active freeze to sude ni pinned na spec o yomikomi, manifest candidate o kaku consumer de aru (`orchestrator/campaign/s8b_oracle_manifest.py:1170-1232`). CLI no nyuuryoku mo `--output` dake (`orchestrator/campaign/s8b_oracle_manifest.py:1235-1254`).

### (B) Freeze v2 approval / active pointer

1. Mazu v2 g1 candidate no zentei o sorou.

   - Budget approval path wa `output/s8b-freeze-budget-approvals/g1.json`, pin wa genzai `None`: `orchestrator/campaign/s8b_holdout_freeze.py:47-50`.
   - Pin ga `None` nara `budget-approval-not-ratified`: `orchestrator/campaign/s8b_holdout_freeze.py:1161-1168`.
   - Official floor result wa `mode=official` kaつ `eligible_for_refreeze=true` ga hitsuyou: `orchestrator/campaign/s8b_holdout_freeze.py:1245-1263`.
   - Genzai wa official no juri shuugou ga kara de, pilot artifact wa refreeze ni tsukaenai: `docs/phase3.md:118-123`.
   - Budget approval record, pin, official floor result ga nai tame, koko de teishi suru.

2. Zentei ga sorotta ato dake, existing producer o tsukaeru.

   - CLI: `generate-v2-candidate --floor-result PATH --budget PATH`
   - Parser/main: `orchestrator/campaign/s8b_holdout_freeze.py:1561-1602`.
   - Builder/writer: `orchestrator/campaign/s8b_holdout_freeze.py:1368-1448`, `1536-1547`.
   - Output wa fixed candidate path `output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`: `orchestrator/campaign/s8b_holdout_freeze.py:47`.

3. Reviewed candidate no exact bytes o canonical generation path `output/s8b-freeze/holdout_freeze.v2.g1.json` ni oku.

   - Canonical path builder wa `orchestrator/campaign/s8b_ratified_freeze.py:1040-1041`.
   - Candidate kara canonical generation e promote suru production CLI/writer wa nai. Kono sou作 wa `keiro nashi`.
   - Generation commit G wa non-merge, `AI-Agent: none` dewa naku, structured `AI-Agent` o motsu hitsuyou ga aru: `orchestrator/campaign/s8b_ratified_freeze.py:552-570`.
   - Candidate ga capture shita `frozen_at_head` wa G no chokusetsu parent de nakereba naranai: `orchestrator/campaign/s8b_ratified_freeze.py:948-961`.

4. G commit go ni generation bytes hash o keisan shi, approval to pointer o canonical JSON de tsukuru.

   - Exact key sets wa `orchestrator/campaign/s8b_ratified_freeze.py:113-117`.
   - Canonical bytes keiyaku wa `orchestrator/campaign/s8b_ratified_freeze.py:398-415`.
   - Approval path wa `approvals/<generation-sha256>.json`; pointer path wa `active/<pointer-bytes-sha256>.json`: `orchestrator/campaign/s8b_ratified_freeze.py:85-89`.
   - Approval/pointer writer ya CLI wa nai. Record sakusei wa `keiro nashi`.

5. Approval to pointer o onaji betsu commit A de tsuika suru.

   - G to A wa onaji commit ni dekinai: `orchestrator/campaign/s8b_ratified_freeze.py:1199-1204`.
   - A no diff wa approval to pointer no 2 tsuika dake: `orchestrator/campaign/s8b_ratified_freeze.py:1205-1211`.
   - A wa non-merge de, exact `AI-Agent: none` ga 1 hon dake hitsuyou: `orchestrator/campaign/s8b_ratified_freeze.py:525-547`.

6. Commit go ni `resolve_active_generation` kara `load_ratified_freeze` o toosu.

   - Resolver wa `orchestrator/campaign/s8b_ratified_freeze.py:1214-1312`.
   - Loader wa `orchestrator/campaign/s8b_ratified_freeze.py:1315-1330`.

Kono tejun wa shorai no keiro de ari, genzai wa step 1 de teishi suru. Sara ni, AI ga approval no jisshitsuteki handan o suru kono irai dewa step 5 no provenance o shoujiki ni mitasenai.

## 2. Fuzai shucho no real/refuted

### A-2

Hantei: `real` for production keiro zero.

Production de `s8b_oracle_spec` o yomu keiro wa loader/validator dake de, writer ya subcommand wa nai. `build-approved` mo pinned spec no consumer de aru (`orchestrator/campaign/s8b_oracle_manifest.py:1170-1188`).

Tada shi, "`s8b_oracle_spec_fixture.py` 1 file nomi ga kakite" to iu chikugo inventory wa `refuted`. Test module jitai ni mo direct writer ga aru (`orchestrator/tests/test_s8b_oracle_manifest.py:264-268`, `1102-1106`, `1148-1156`). Subete synthetic matawa negative test you de, production keiro no hanshou niwa naranai.

### A-3

Hantei: `real`.

File ga aru dake de `durable_files` ni hairi, `assert durable_files == []` ga shippai suru (`orchestrator/tests/test_s8b_oracle_manifest_contract.py:128-144`). Schema version ni yoru branch wa nai.

Schema literal no koushin dake de red o sakeru jouken wa sonzai shinai. Separate schema migration to strict contract no sai-sekkei ga hitsuyou de, genzai no approval turn ni tsukaeru existing keiro wa nai.

### B-1

Hantei: `real`.

Pointer ga shimesu generation ga generations index ni nai baai, `pointer-generation` de kanarazu kyohi sareru (`orchestrator/campaign/s8b_ratified_freeze.py:1232-1239`). Approval dake nara active pointer ga nai tame `no-active` (`1253-1256`). Generation to approval/pointer o onaji commit ni oku keiro mo `1199-1204` de tojite iru.

Shorai no generation candidate producer wa aru ga, genzai wa budget approval pin, approval record, official floor result ga nai tame jissou dekinai.

### B-2

Hantei: `real`.

Production de exact `AI-Agent: none` o byte-for-byte ni youkyuu shite iru (`orchestrator/campaign/s8b_ratified_freeze.py:525-547`).

Provenance seihon wa AI ga jisshitsuteki ni kanyo shita commit ni structured `AI-Agent` o youkyuu shi, `AI-Agent: none` to no heiki o kinshi suru (`docs/ai-provenance.md:19-44`). Yotte AI ga approval handan o okonau baai, ryouritsu suru trailer no kakikata wa nai.

Narrow na reigai wa, user ga exact bytes to shoudaku o dokuritsu ni kakutei shi, AI ga Git operation dake o kikai-teki ni daikou suru baai de aru (`docs/ai-provenance.md:71-74`). Sono baai wa AI ga approval o jisshi shita no dewa nai tame, konkai no inin no tassei niwa naranai.

D328 mo naosenai. Hold wa `HELD=True`, release wa explicit user command dake (`orchestrator/campaign/freeze_verification_hold.py:14-15`, `54-65`). Active ka sareba report/judge kara `reverify_published_freeze` ga reachable ni naru (`orchestrator/campaign/s8b_oracle_report.py:1759-1769`, `s8b_oracle_judge.py:370-378`). Konkai no inin ni D328 release wa fukumarete inai.

## Soukatsu

- (A): jisshi funou - candidate producer ga naku, file o oku to `orchestrator/tests/test_s8b_oracle_manifest_contract.py:128-144` ga mujouken ni kyohi suru.
- (B): jisshi funou - generation fuzai wa `orchestrator/campaign/s8b_ratified_freeze.py:1232-1239` de kyohi sare, AI approval commit wa `525-547` to `docs/ai-provenance.md:37-44` o douji ni mitasenai.