#!/usr/bin/env python3
"""Focused parser, schema, duplicate-ingest, and denominator negative checks."""
import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import stage9_coverage as cov
import prepare_stage9 as prep
import prepare_stage9_recovery as recovery
import run_stage6_enabled as stage6_runner
import run_stage7_enabled as stage7_runner
import verify_stage9_final_dispatch as final_dispatch
with patch.object(sys,"argv",["run_stage4_4.py","--sim","xsim"]):
    import run_stage4_4 as stage4_runner


def binrow(bin_id="ARCH.OP.ADD",configs=cov.CONFIGS["rv32im"],reach="reachable"):
    return {"bin_id":bin_id,"dictionary_version":cov.DICTIONARY_VERSION,"coverage_class":"architectural",
            "definition":"unit test bin","applicable_configurations":configs,"evidence_source":"synthetic fixture",
            "reachability":reach,"reachability_reason":"test fixture"}


def obs(test_id="stage5:one",count=1,config=cov.CONFIGS["rv32im"],sim="verilator"):
    return {"identity":{"test_id":test_id,"simulator":sim,"configuration":config,"scenario":"unit",
            "schema_version":cov.SCHEMA_VERSION,"dictionary_version":cov.DICTIONARY_VERSION,
            "seed":"","suite":"unit","observed_cycles":1,"runtime_seconds":"",
            "status":"PASS","validation_status":"PASS","evidence_sha256":"0"*64,
            "evidence_sources":"unit.trace","validation_report":"unit.txt",
            "validation_report_sha256":"1"*64,"validated_source_provenance_sha256":"1"*64},
            "counts":{"ARCH.OP.ADD":count} if count else {}}


class CoverageValidationTests(unittest.TestCase):
    def test_dictionary_ids_are_unique_and_versioned(self):
        rows=cov.dictionary_rows()
        ids=[r["bin_id"] for r in rows]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertTrue(all(r["dictionary_version"]==cov.DICTIONARY_VERSION for r in rows))
        for i in range(16): self.assertIn(f"P.PIPE_EVENT.{i:02d}",ids)

    def test_privileged_gap_classification_and_original_denominator(self):
        bins={r["bin_id"]:r for r in cov.dictionary_rows()}
        self.assertEqual(bins["ARCH.OP.WFI"]["reachability"],"unsupported")
        self.assertIn("Stage 7",bins["ARCH.OP.WFI"]["reachability_reason"])
        self.assertTrue(cov.config_applicable(bins["ARCH.OP.WFI"],cov.CONFIGS["stage8"]))
        self.assertFalse(cov.applicable(bins["ARCH.OP.WFI"],cov.CONFIGS["stage8"]))
        self.assertEqual(cov.trap_instruction_bins([
            {"raw":"00000073","mcause":"0000000b"},
            {"raw":"00100073","mcause":"00000003"},
            {"raw":"00000073","mcause":"8000000b"}]),
            {"ARCH.OP.ECALL":1,"ARCH.OP.EBREAK":1})

    def test_stage5_c_a_m_operand_bins_accept_only_validated_reconstructed_reference(self):
        row={b["bin_id"]:b for b in cov.dictionary_rows()}["A.OP.MUL"]
        config=cov.CONFIGS["rv32imac"]
        self.assertEqual(cov.bin_evidence_policy(row,config,"stage5")[0],"unavailable")
        self.assertEqual(cov.bin_evidence_policy(row,config,"stage5",m_operand_reference=True)[0],"required")

    def test_saved_reconstructed_iss_replay_is_trace_matched_for_both_simulators(self):
        path=cov.ROOT/"reports/stage9_coverage/recovery_prepared_iss_replay.json"
        self.assertTrue(path.is_file())
        index=json.loads(path.read_text(encoding="utf-8"))
        for sim in ("verilator","xsim"):
            with self.subTest(sim=sim):
                item=index["simulators"][sim]["stage5"]
                side_dir=cov.validate_stage5_iss_replay(
                    item["reconstructed_m_reference"],sim,cov.ROOT/item["outdir"])
                self.assertEqual(len(list(side_dir.glob("*.iss.m.tsv"))),39)
                self.assertEqual(item["reconstructed_m_reference"]["evidence_status"],
                                 "RECONSTRUCTED_REFERENCE_TRACE_MATCHED")

    def test_dynamic_ifid_entries_disambiguate_reexecution_and_reject_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"dynamic.mcov"
            path.write_text("MCOV_VERSION 2 DYNAMIC_IFID_ENTRY\n"
                            "C ENTER 1 00000010 ff418213 4\n"
                            "C ENTER 2 00000010 ff418213 4\n",encoding="ascii")
            records=cov.parse_sidecar(path)
            ids=[int(row[2]) for row in records["C ENTER"]]
            self.assertEqual(ids,[1,2])
            path.write_text("MCOV_VERSION 2 DYNAMIC_IFID_ENTRY\n"
                            "C ENTER 1 00000010 ff418213 4\n"
                            "C ENTER 1 00000010 ff418213 4\n",encoding="ascii")
            with self.assertRaisesRegex(ValueError,"duplicate or nonsequential"):
                cov.parse_sidecar(path)

    def test_supplemental_run_replaces_legacy_observation_once_and_keeps_c_cases_historical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); historical=root/"historical"; fresh=root/"fresh"
            historical.mkdir(); fresh.mkdir()
            manifest=[{"name":"legacy_one","suite":"rv32im"},
                      {"name":"legacy_two","suite":"rv32im"},
                      {"name":"c_case","suite":"rv32imc"}]
            for name in ("legacy_one","legacy_two","c_case"):
                (historical/f"{name}.pipe.trace").write_text("old",encoding="ascii")
            for name in ("legacy_one","legacy_two"):
                (fresh/f"{name}.pipe.trace").write_text("new",encoding="ascii")
            chosen=cov.stage5_evidence_selection(manifest,historical,fresh)
            self.assertEqual(len(chosen),3)
            self.assertEqual(chosen["legacy_one"],fresh)
            self.assertEqual(chosen["legacy_two"],fresh)
            self.assertEqual(chosen["c_case"],historical)
            with self.assertRaisesRegex(ValueError,"identity set mismatch"):
                cov.stage5_evidence_selection(manifest,historical,root)

    def test_unknown_bin_is_rejected(self):
        row=obs(); row["counts"]={"ARCH.OP.NOT_REAL":1}
        with self.assertRaisesRegex(ValueError,"unknown coverage bin"):
            cov.validate_observations([row],[binrow()])

    def test_duplicate_ingestion_is_rejected_before_aggregation(self):
        one=obs()
        with self.assertRaisesRegex(ValueError,"duplicate test identity"):
            cov.aggregate_observations([one,one],[binrow()])

    def test_aggregate_uses_applicable_valid_test_denominator(self):
        rows=[obs("stage5:a",1),obs("stage5:b",0)]
        result=cov.aggregate_observations(rows,[binrow()])[0]
        self.assertEqual((result["applicable_tests"],result["hit_tests"],result["event_count"]),(2,1,1))

    def test_unavailable_lifecycle_evidence_is_not_converted_to_zero(self):
        one=obs("stage6:ambiguous",0,config=cov.CONFIGS["stage6"])
        one["unavailable_bins"]=["ARCH.OP.ADD"]
        one["unavailable_reasons"]={"ARCH.OP.ADD":"fixture ambiguity"}
        two=obs("stage6:observed",1,config=cov.CONFIGS["stage6"])
        rows=cov.aggregate_observations([one,two],[binrow(configs=cov.CONFIGS["stage6"])])
        result=rows[0]
        self.assertEqual((result["applicable_tests"],result["evidence_tests"],result["unavailable_tests"],result["hit_tests"]),(2,1,1,1))

    def test_wrong_schema_and_configuration_are_rejected(self):
        row=obs(); row["identity"]["schema_version"]="old"
        with self.assertRaisesRegex(ValueError,"schema version"):
            cov.validate_observations([row],[binrow()])
        row=obs(); row["identity"]["configuration"]="rv32imac+future"
        with self.assertRaisesRegex(ValueError,"unknown configuration"):
            cov.validate_observations([row],[binrow()])

    def test_failed_run_cannot_contribute(self):
        row=obs(); row["identity"]["validation_status"]="FAIL"
        with self.assertRaisesRegex(ValueError,"invalid run"):
            cov.validate_observations([row],[binrow()])

    def test_malformed_and_unknown_sidecar_records_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"bad.mcov"
            path.write_text("C ATTEMPT 00000000 00000013\n",encoding="ascii")
            with self.assertRaisesRegex(ValueError,"malformed C ATTEMPT"):
                cov.parse_sidecar(path)
            path.write_text("Q UNKNOWN 00000000\n",encoding="ascii")
            with self.assertRaisesRegex(ValueError,"unknown evidence event"):
                cov.parse_sidecar(path)

    def test_missing_required_simulation_log_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,"missing simulator log"):
                cov.pass_log(Path(tmp)/"missing.log")

    def test_instruction_classifier_uses_expanded_compressed_record(self):
        self.assertEqual(cov.instruction_name(0x00000001,2,0x00000013),"addi")
        self.assertEqual(cov.instruction_name(0x003100b3,4,0x003100b3),"add")

    def test_stage5_legacy_trace_format_is_parsed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"legacy.trace"
            lines=["00000000 00200193 03 00000002 0 00000000 00000000","HALT 1 00000004"]
            lines += [f"REG {i} 00000000" for i in range(1,32)]
            path.write_text("\n".join(lines)+"\n",encoding="ascii")
            rows,state=cov.parse_trace(path)
            self.assertEqual((rows[0]["pc"],rows[0]["raw"],rows[0]["length"],rows[0]["rd"]),
                             (0,0x00200193,4,3))
            self.assertEqual(len(state),32)

    def test_stage5_legacy_c_disabled_has_explicit_per_bin_evidence_policy(self):
        bins={r["bin_id"]:r for r in cov.dictionary_rows()}
        self.assertEqual(cov.bin_evidence_policy(bins["ARCH.OP.ADD"],cov.CONFIGS["rv32im"])[0],"required")
        self.assertEqual(cov.bin_evidence_policy(bins["PIPE.RETIRED"],cov.CONFIGS["rv32im"])[0],"required")
        state,reason=cov.bin_evidence_policy(bins["PIPE.HAZARD.DIV_HOLD"],cov.CONFIGS["rv32im"])
        self.assertEqual(state,"unavailable")
        self.assertIn("emitted no detailed pipeline sidecar",reason)
        self.assertEqual(cov.bin_evidence_policy(bins["A.C.HINT.RETIRED"],cov.CONFIGS["rv32im"])[0],"inapplicable")

    def test_stage5_c_disabled_ccov_is_inapplicable_but_c_enabled_ccov_is_required(self):
        self.assertFalse(cov.stage5_sidecar_policy("rv32im")[".pipe.ccov"])
        self.assertTrue(cov.stage5_sidecar_policy("rv32imc")[".pipe.ccov"])
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)
            self.assertEqual(cov.check_required_sidecars(out,"branch_backward",cov.stage5_sidecar_policy("rv32im")),[])
            missing=cov.check_required_sidecars(out,"branch_backward",cov.stage5_sidecar_policy("rv32imc"))
            self.assertEqual(missing,[str(out/"branch_backward.pipe.ccov")])
            (out/"branch_backward.pipe.ccov").write_text("",encoding="ascii")
            self.assertEqual(cov.check_required_sidecars(out,"branch_backward",cov.stage5_sidecar_policy("rv32imc")),[])

    def test_recovery_legacy_gap_audit_and_collection_share_ccov_sidecar(self):
        index_path=cov.ROOT/"reports/stage9_coverage/recovery_prepared_pathfix.json"
        self.assertTrue(index_path.is_file(),"recovery preparation index is required for this integration regression")
        index=json.loads(index_path.read_text(encoding="utf-8"))
        cov.audit_saved_evidence(index)
        manifest_dir=cov.ROOT/index["simulators"]["verilator"]["stage5"]["outdir"]
        manifest=cov.read_stage5_manifests(manifest_dir)
        row=next(r for r in manifest if r["name"]=="branch_backward" and r["suite"]=="rv32im")
        for sim in ("verilator","xsim"):
            with self.subTest(sim=sim):
                item=index["simulators"][sim]["stage5"]
                gap_dir=cov.ROOT/item["legacy_outdir"]
                selected=cov.stage5_evidence_selection(manifest,manifest_dir,gap_dir)
                self.assertEqual(selected[row["name"]],gap_dir)
                audit_path=cov.evidence_path(gap_dir,row["name"],"stage5",".pipe.ccov")
                collect_path=cov.evidence_path(gap_dir,row["name"],"stage5",".pipe.mcov")
                self.assertEqual(audit_path,collect_path)
                self.assertEqual(audit_path.suffix,".ccov")
                self.assertTrue(audit_path.is_file())
                observation=cov.collect_test(
                    "stage5",sim,gap_dir,row["name"],row,row["suite"],row["name"],None,
                    cov.ROOT/item["legacy_report"])
                self.assertEqual(observation["identity"]["test_id"],"stage5:branch_backward")

    def test_ordered_lifecycle_preserves_repeated_pc_retirements(self):
        a=["C", "ATTEMPT", "00000010", "ff418213", "4"]
        r=["C", "RETIRE", "00000010", "ff418213", "4"]
        result=cov.analyze_ordered_lifecycle([("C ATTEMPT",a),("C RETIRE",r),
                                               ("C ATTEMPT",a),("C RETIRE",r)])
        self.assertEqual(result["attempt_count"],2)
        self.assertEqual(result["terminal_count"],2)

    def test_ordered_squash_then_same_pc_reexecution_can_retire(self):
        a=["C", "ATTEMPT", "00000010", "ff418213", "4"]
        s=["C", "SQUASH_REDIRECT", "00000010", "ff418213", "4"]
        r=["C", "RETIRE", "00000010", "ff418213", "4"]
        result=cov.analyze_ordered_lifecycle([("C ATTEMPT",a),("C SQUASH_REDIRECT",s),
                                               ("C ATTEMPT",a),("C RETIRE",r)])
        self.assertEqual(result["attempt_count"],2)
        self.assertEqual(result["terminal_count"],2)
        self.assertFalse(result["ambiguous_attempt_keys"])

    def test_ordered_divider_abort_then_same_pc_restart_can_retire(self):
        a=["C", "ATTEMPT", "00000020", "0262c233", "4"]
        abort=["M", "DIV_ABORT", "00000020", "0262c233"]
        r=["C", "RETIRE", "00000020", "0262c233", "4"]
        result=cov.analyze_ordered_lifecycle([("C ATTEMPT",a),("M DIV_ABORT",abort),
                                               ("C ATTEMPT",a),("C RETIRE",r)])
        self.assertEqual(result["attempt_count"],2)
        self.assertFalse(result["ambiguous_attempt_keys"])

    def test_overlapping_same_pc_lifecycle_is_ambiguous_without_dynamic_id(self):
        a=["C", "ATTEMPT", "00000010", "ff418213", "4"]
        b=["C", "ATTEMPT", "00000014", "00000013", "4"]
        r=["C", "RETIRE", "00000010", "ff418213", "4"]
        result=cov.analyze_ordered_lifecycle([("C ATTEMPT",a),("C ATTEMPT",b),
                                               ("C ATTEMPT",a),("C RETIRE",r)])
        self.assertIsNone(result["attempt_count"])
        self.assertIn((0x10,0xff418213,4),result["ambiguous_attempt_keys"])

    def test_terminal_without_prior_attempt_is_a_provable_lifecycle_violation(self):
        r=["C", "RETIRE", "00000010", "ff418213", "4"]
        with self.assertRaisesRegex(ValueError,"no prior ordered attempt"):
            cov.analyze_ordered_lifecycle([("C RETIRE",r)])


class PreparationManifestTests(unittest.TestCase):
    def test_final_batch_dispatches_xsim_to_windows_and_rejects_wsl(self):
        batch=cov.ROOT/"scripts/simulation/run_stage9_final_209.bat"
        final_dispatch.check_dispatch(batch)
        source=batch.read_text(encoding="utf-8")
        xsim_line=next(line for line in source.splitlines() if "set \"CMD_GAPX=" in line)
        wsl_line='set "CMD_GAPX="C:\\Windows\\System32\\wsl.exe" --distribution Ubuntu --exec python3 scripts/simulation/run_stage4_4.py --sim xsim --stage9-legacy-gap"'
        bad=source.replace(xsim_line,wsl_line)
        self.assertNotEqual(source,bad,"XSim dispatch mutation fixture did not apply")
        with tempfile.TemporaryDirectory(prefix="stage9_dispatch_",dir=cov.ROOT/"reports") as tmp:
            changed=Path(tmp)/"bad_dispatch.bat"
            changed.write_text(bad,encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"XSim-under-WSL|XSim must launch Windows Python"):
                final_dispatch.check_dispatch(changed)

    def test_stage5_selection_round_trips_real_c_and_a_producer_metadata(self):
        out=cov.ROOT/"sim_out_stage9_ca_xsim_20261110T120117Z"
        crows=cov.read_csv(out/"c_manifest.csv")
        arows=cov.read_csv(out/"a_manifest.csv")
        selected=([stage4_runner.selection_record("rv32imc",row) for row in crows]+
                  [stage4_runner.selection_record("rv32imac",row) for row in arows])
        with tempfile.TemporaryDirectory(prefix="stage9_s5_selection_roundtrip_",dir=cov.ROOT/"reports") as tmp:
            target=Path(tmp)/"selection_manifest.csv"
            stage4_runner.write_selection_manifest(target,selected)
            with target.open(newline="",encoding="utf-8") as stream:
                reader=csv.DictReader(stream)
                self.assertEqual(tuple(reader.fieldnames),stage4_runner.STAGE5_SELECTION_FIELDS)
                self.assertEqual(list(reader),selected)
        with self.assertRaisesRegex(ValueError,"producer row schema mismatch"):
            stage4_runner.selection_record("rv32imc",{**crows[0],"unexpected":"cannot drop"})
        legacy=cov.read_csv(out/"manifest_all.csv")
        with tempfile.TemporaryDirectory(prefix="stage9_legacy_selection_roundtrip_",dir=cov.ROOT/"reports") as tmp:
            target=Path(tmp)/"selection_manifest.csv"
            record=stage4_runner.selection_record("rv32im",legacy[0])
            stage4_runner.write_selection_manifest(target,[record],legacy=True)
            with target.open(newline="",encoding="utf-8") as stream:
                reader=csv.DictReader(stream)
                self.assertEqual(tuple(reader.fieldnames),stage4_runner.LEGACY_SELECTION_FIELDS)
                self.assertEqual(list(reader),[record])

    def test_stage6_selection_manifest_round_trips_real_prepared_schema(self):
        source=cov.ROOT/"sim_out_stage8_prepare_mem_footerfix/stage7/stage6_compat/z_manifest.csv"
        rows=stage6_runner.read_stage6_manifest(source)
        self.assertEqual(tuple(rows[0]),stage6_runner.STAGE6_MANIFEST_FIELDS)
        self.assertEqual(len(rows),11)
        with tempfile.TemporaryDirectory(prefix="stage9_s6_selection_roundtrip_",dir=cov.ROOT/"reports") as tmp:
            target=Path(tmp)/"selection_manifest.csv"
            stage6_runner.write_stage6_selection_manifest(target,rows)
            self.assertEqual(stage6_runner.read_stage6_manifest(target),rows)
            with target.open(newline="",encoding="utf-8") as stream:
                self.assertEqual(tuple(next(csv.reader(stream))),stage6_runner.STAGE6_MANIFEST_FIELDS)

    def test_stage6_selection_writer_rejects_unmodeled_metadata(self):
        row={field:"0" for field in stage6_runner.STAGE6_MANIFEST_FIELDS}
        row.update(name="extra_check",hexpath="image.hex",extra="must_not_disappear")
        with tempfile.TemporaryDirectory(prefix="stage9_s6_selection_schema_",dir=cov.ROOT/"reports") as tmp:
            with self.assertRaisesRegex(ValueError,"schema mismatch"):
                stage6_runner.write_stage6_selection_manifest(Path(tmp)/"selection.csv",[row])

    def test_stage6_preparation_comparison_accepts_path_relocation_with_matching_artifact_hashes(self):
        fields=stage6_runner.STAGE6_MANIFEST_FIELDS
        with tempfile.TemporaryDirectory(prefix="stage9_s6_semantic_",dir=cov.ROOT/"reports") as tmp:
            base=Path(tmp); old=base/"old"; new=base/"new"
            old_manifest=old/"z_manifest.csv"; new_manifest=new/"z_manifest.csv"
            row={"name":"stage6_case","expect_cause":"3","check_gp":"0","hexpath":"",
                 "atomics":"1","z_events":"2","retired":"4"}
            for directory in (old,new):
                (directory/"z_hex").mkdir(parents=True)
                (directory/"z_iss").mkdir()
                (directory/"z_hex"/"stage6_case.hex").write_bytes(b"same image\n")
                for suffix in ("trace","a.tsv","z.tsv"):
                    (directory/"z_iss"/f"stage6_case.{suffix}").write_bytes(f"same {suffix}\n".encode())
            with old_manifest.open("w",newline="",encoding="utf-8") as stream:
                writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n");writer.writeheader()
                writer.writerow({**row,"hexpath":str(old/"z_hex"/"stage6_case.hex")})
            with new_manifest.open("w",newline="",encoding="utf-8") as stream:
                writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n");writer.writeheader()
                writer.writerow({**row,"hexpath":str(new/"z_hex"/"stage6_case.hex")})
            result=recovery.compare_stage6_manifest_inputs(old_manifest,old_manifest,new_manifest)
            self.assertEqual(result["status"],"SEMANTICALLY_IDENTICAL_INPUTS")
            self.assertEqual(result["hexpath_relocations"],1)
            self.assertEqual(result["image_and_reference_hashes_compared"],4)
            self.assertNotEqual(hashlib.sha256(old_manifest.read_bytes()).hexdigest(),
                                hashlib.sha256(new_manifest.read_bytes()).hexdigest())

    def test_stage6_preparation_comparison_rejects_changed_metadata_and_reference(self):
        fields=stage6_runner.STAGE6_MANIFEST_FIELDS
        with tempfile.TemporaryDirectory(prefix="stage9_s6_semantic_reject_",dir=cov.ROOT/"reports") as tmp:
            base=Path(tmp); old=base/"old"; new=base/"new"
            for directory in (old,new):
                (directory/"z_hex").mkdir(parents=True);(directory/"z_iss").mkdir()
                (directory/"z_hex"/"stage6_case.hex").write_bytes(b"same image\n")
                for suffix in ("trace","a.tsv","z.tsv"):
                    (directory/"z_iss"/f"stage6_case.{suffix}").write_bytes(f"same {suffix}\n".encode())
            def save(directory,expect_cause="3"):
                path=directory/"z_manifest.csv"
                row={"name":"stage6_case","expect_cause":expect_cause,"check_gp":"0",
                     "hexpath":str(directory/"z_hex"/"stage6_case.hex"),"atomics":"1","z_events":"2","retired":"4"}
                with path.open("w",newline="",encoding="utf-8") as stream:
                    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator="\n");writer.writeheader();writer.writerow(row)
                return path
            old_manifest=save(old);new_manifest=save(new,expect_cause="1")
            with self.assertRaisesRegex(ValueError,"semantic fields changed"):
                recovery.compare_stage6_manifest_inputs(old_manifest,old_manifest,new_manifest)
            new_manifest=save(new)
            (new/"z_iss"/"stage6_case.z.tsv").write_text("changed reference\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"reference content changed"):
                recovery.compare_stage6_manifest_inputs(old_manifest,old_manifest,new_manifest)
            (new/"z_iss"/"stage6_case.z.tsv").write_text("same z.tsv\n",encoding="utf-8")
            (new/"z_hex"/"stage6_case.hex").write_bytes(b"changed image\n")
            with self.assertRaisesRegex(ValueError,"image content changed"):
                recovery.compare_stage6_manifest_inputs(old_manifest,old_manifest,new_manifest)

    def test_stage7_and_stage8_selection_round_trip_real_released_and_seeded_rows(self):
        released_path=cov.ROOT/"sim_out_stage7_prepare_decoder_units/m_manifest.csv"
        released=stage7_runner.read_prepared_manifest(released_path,stage8=False)
        combined_path=cov.ROOT/"sim_out_stage9_recovery_prepare_2173_18870/stage7/m_manifest.csv"
        combined=stage7_runner.read_prepared_manifest(combined_path,stage8=True)
        released8=[row for row in combined if row["suite"]=="stage7_enabled"]
        seeded8=[row for row in combined if row["suite"]=="stage8_seeded"]
        self.assertEqual((len(released),len(released8),len(seeded8)),(13,13,10))
        with tempfile.TemporaryDirectory(prefix="stage9_s7_s8_roundtrip_",dir=cov.ROOT/"reports") as tmp:
            root=Path(tmp)
            for label,rows,extended in (("stage7_released",released,False),
                                        ("stage8_released",released8,True),
                                        ("stage8_seeded",seeded8,True)):
                target=root/f"{label}.csv"
                stage7_runner.write_selection_manifest(target,rows,stage8=extended)
                self.assertEqual(stage7_runner.read_prepared_manifest(target,stage8=extended),rows)

    def test_stage7_selection_writer_rejects_unmodeled_metadata(self):
        row={field:"0" for field in stage7_runner.STAGE7_MANIFEST_FIELDS}
        row.update(name="extra_case",hexpath="case.hex",extra="must_not_disappear")
        with tempfile.TemporaryDirectory(prefix="stage9_s7_selection_schema_",dir=cov.ROOT/"reports") as tmp:
            with self.assertRaisesRegex(ValueError,"schema mismatch"):
                stage7_runner.write_selection_manifest(Path(tmp)/"selection.csv",[row])

    def test_stage8_preparation_freshness_rejects_changed_source_hash(self):
        with tempfile.TemporaryDirectory(prefix="stage9_prep_freshness_",dir=cov.ROOT/"reports") as tmp:
            stage7=Path(tmp)/"stage7";stage7.mkdir()
            source=Path(tmp)/"producer.py";source.write_text("producer v1\n",encoding="utf-8")
            manifest=stage7/"m_manifest.csv";manifest.write_text("name\ncase\n",encoding="utf-8")
            digest=hashlib.sha256(source.read_bytes()).hexdigest()
            rel=source.relative_to(cov.ROOT).as_posix()
            (stage7/"stage7_preparation.txt").write_text(f"STAGE7_PREPARATION READY\nsha256 {rel}={digest}\n",encoding="utf-8")
            manifest_hash=hashlib.sha256(manifest.read_bytes()).hexdigest()
            (stage7/"stage8_preparation.txt").write_text(
                f"STAGE8_PREPARATION READY\nsha256 {rel}={digest}\n"
                f"artifact_sha256 @PREPARED@/m_manifest.csv={manifest_hash}\n",encoding="utf-8")
            self.assertEqual(prep.verify_stage8_preparation(manifest)[1],1)
            source.write_text("producer v2\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"preparation source hash is stale"):
                prep.verify_stage8_preparation(manifest)

    def test_saved_provenance_recovery_selection_is_exactly_39_11_23(self):
        s5=cov.read_stage5_manifests(cov.ROOT/"sim_out_stage5_a_verilator_20261110T053612Z")
        s5_selected=[r for r in s5 if r["suite"]!="rv32im"]
        s6=cov.read_csv(cov.ROOT/"sim_out_stage8_prepare_mem_footerfix/stage7/stage6_compat/z_manifest.csv")
        s8=cov.read_csv(cov.ROOT/"sim_out_stage8_prepare_mem_footerfix/stage7/m_manifest.csv")
        self.assertEqual((len(s5_selected),len({r["name"] for r in s5_selected})),(39,39))
        self.assertEqual((len(s6),len({r["name"] for r in s6})),(11,11))
        self.assertEqual((len(s8),len({r["name"] for r in s8})),(23,23))
        self.assertEqual(len(set(r["name"] for r in s5_selected)&set(r["name"] for r in s6)),0)
        self.assertEqual(len(set(r["name"] for r in s6)&set(r["name"] for r in s8)),0)

    def test_check_report_rejects_manifest_missing_required_headers(self):
        with tempfile.TemporaryDirectory(prefix="stage9_manifest_test_",dir=cov.ROOT/"reports") as tmp:
            outdir=Path(tmp)
            (outdir/"manifest_all.csv").write_text("name,hexpath\none,image.hex\n",encoding="utf-8")
            fixture=outdir/"fixture.txt"
            fixture.write_text("fixture\n",encoding="utf-8",newline="\n")
            digest=hashlib.sha256(fixture.read_bytes()).hexdigest()
            provenance=outdir/"provenance.txt"
            provenance.write_text(f"simulator=verilator\nsha256 {fixture.relative_to(cov.ROOT).as_posix()}={digest}\n",
                                  encoding="utf-8",newline="\n")
            marker="STAGE5_A_PIPELINE_VERILATOR PASS legacy=209 c_cases=21 a_cases=18 full_trace_comparisons=496 units=8"
            report=outdir/"stage5_report.txt"
            report.write_text(f"Simulator: verilator\noutput_dir={outdir.as_posix()}\n"
                              f"provenance_file={provenance.as_posix()}\n{marker}\n",
                              encoding="utf-8",newline="\n")
            with self.assertRaisesRegex(ValueError,"manifest missing required header"):
                prep.check_report(report,marker,"verilator","stage5",outdir)

    def test_manifest_reader_reports_malformed_row_number(self):
        with tempfile.TemporaryDirectory(prefix="stage9_manifest_row_",dir=cov.ROOT/"reports") as tmp:
            path=Path(tmp)/"manifest.csv"
            path.write_text("name,expect_cause,check_gp,hexpath\none,1\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,r"malformed row at .*:2"):
                cov.read_manifest(path,{"name","expect_cause","check_gp","hexpath"})

    def _write_stage5_manifests(self, outdir, duplicate=False, missing_legacy=False):
        legacy=[f"legacy_{i:03d}" for i in range(209-(1 if missing_legacy else 0))]
        c_names=[f"c_{i:02d}" for i in range(21)]
        a_names=[f"a_{i:02d}" for i in range(18)]
        if duplicate: a_names[0]=legacy[0]
        with (outdir/"manifest_all.csv").open("w",encoding="utf-8",newline="") as f:
            f.write("name,expect_cause,check_gp,hexpath\n")
            for n in legacy: f.write(f"{n},1,0,legacy/{n}.hex\n")
        with (outdir/"c_manifest.csv").open("w",encoding="utf-8",newline="") as f:
            f.write("name,expect_cause,check_gp,suite,hexpath\n")
            for i,n in enumerate(c_names): f.write(f"{n},1,0,{'rv32imc' if i<12 else 'rv32imc_pipeline'},c/{n}.hex\n")
        with (outdir/"a_manifest.csv").open("w",encoding="utf-8",newline="") as f:
            f.write("name,expect_cause,check_gp,suite,hexpath\n")
            for i,n in enumerate(a_names):
                suite="rv32ima_software" if i<13 else "rv32imac_software" if i==13 else "rv32imac_pipeline_a"
                f.write(f"{n},1,0,{suite},a/{n}.hex\n")

    def test_stage5_real_three_manifest_layout_combines_to_248_unique_cases(self):
        with tempfile.TemporaryDirectory(prefix="stage9_three_manifests_",dir=cov.ROOT/"reports") as tmp:
            outdir=Path(tmp); self._write_stage5_manifests(outdir)
            rows=cov.read_stage5_manifests(outdir)
            self.assertEqual(len(rows),248)
            self.assertEqual(len({r["name"] for r in rows}),248)
            self.assertEqual((sum(r["suite"]=="rv32im" for r in rows),
                              sum(r["suite"].startswith("rv32imc") for r in rows),
                              sum(r["suite"].startswith("rv32ima") or r["suite"].startswith("rv32imac") for r in rows)),
                             (209,21,18))
            configs={cov.canonical_config("stage5",r["suite"]) for r in rows}
            self.assertEqual(configs,{"rv32im","rv32imc","rv32ima","rv32imac"})

    def test_stage5_combiner_rejects_cross_manifest_duplicate_and_missing_cases(self):
        with tempfile.TemporaryDirectory(prefix="stage9_manifest_reject_",dir=cov.ROOT/"reports") as tmp:
            outdir=Path(tmp); self._write_stage5_manifests(outdir,duplicate=True)
            with self.assertRaisesRegex(ValueError,"248 unique tests"):
                cov.read_stage5_manifests(outdir)
            self._write_stage5_manifests(outdir,missing_legacy=True)
            with self.assertRaisesRegex(ValueError,"legacy manifest must contain 209"):
                cov.read_stage5_manifests(outdir)


class ReportProvenanceTests(unittest.TestCase):
    def _fixture(self, directory, contents=b"validated-source\n"):
        source=directory/"source.sv"
        source.write_bytes(contents)
        return source,hashlib.sha256(contents).hexdigest(),source.relative_to(cov.ROOT).as_posix()

    def test_inline_stage6_provenance_validates(self):
        with tempfile.TemporaryDirectory(prefix="stage9_inline_prov_",dir=cov.ROOT/"reports") as tmp:
            directory=Path(tmp); _,digest,rel=self._fixture(directory)
            report=directory/"stage6.txt"
            report.write_text(f"Stage 6 validation simulator=verilator\nsha256 {rel}={digest}\n",encoding="utf-8")
            result=cov.validate_report_provenance(report,expected_sim="verilator")
            self.assertEqual(result["source_hashes_checked"],1)
            self.assertEqual(Path(result["provenance_path"]),report)

    def test_external_provenance_resolves_windows_and_wsl_paths(self):
        with tempfile.TemporaryDirectory(prefix="stage9_external_prov_",dir=cov.ROOT/"reports") as tmp:
            directory=Path(tmp); _,digest,rel=self._fixture(directory)
            provenance=directory/"provenance.txt"
            provenance.write_text(f"simulator=xsim\nsha256 {rel}={digest}\n",encoding="utf-8")
            relative=directory.relative_to(cov.ROOT).as_posix()
            references=(f"C:\\RISC-V-ML-Test-Selection\\{relative}\\provenance.txt",
                        f"/mnt/c/RISC-V-ML-Test-Selection/{relative}/provenance.txt")
            for ref in references:
                with self.subTest(reference=ref):
                    report=directory/("report_"+str(references.index(ref))+".txt")
                    report.write_text(f"Simulator: xsim\nprovenance_file={ref}\n",encoding="utf-8")
                    result=cov.validate_report_provenance(report,expected_sim="xsim")
                    self.assertEqual(result["source_hashes_checked"],1)
                    self.assertEqual(Path(result["provenance_path"]),provenance)

    def test_wsl_producer_snapshot_paths_resolve_for_windows_validation(self):
        with tempfile.TemporaryDirectory(prefix="stage9_wsl_snapshot_",dir=cov.ROOT/"reports") as tmp:
            directory=Path(tmp)
            source=directory/"producer.sv"
            archived_bytes=b"historical RTL bytes\n"
            source.write_bytes(b"current RTL bytes\n")
            digest=hashlib.sha256(archived_bytes).hexdigest()
            relative=directory.relative_to(cov.ROOT).as_posix()
            wsl_root=f"/mnt/c/{cov.ROOT.name}/{relative}"
            archived=directory/"producer_snapshot"/"source"/"producer.sv"
            archived.parent.mkdir(parents=True)
            archived.write_bytes(archived_bytes)
            snapshot=directory/"producer_snapshot"/"snapshot.json"
            snapshot_doc={"schema":"stage9-producer-snapshot-1","command":[],"files":[{
                "kind":"source","path":f"{wsl_root}/producer.sv",
                "snapshot":f"{wsl_root}/producer_snapshot/source/producer.sv",
                "sha256":digest}]}
            snapshot.write_text(json.dumps(snapshot_doc),encoding="utf-8")
            snapshot_digest=hashlib.sha256(snapshot.read_bytes()).hexdigest()
            provenance=directory/"provenance.txt"
            provenance.write_text(f"simulator=verilator\nsha256 {relative}/producer.sv={digest}\n",
                                  encoding="utf-8")
            report=directory/"report.txt"
            report.write_text("Simulator: verilator\n"
                              f"provenance_file={wsl_root}/provenance.txt\n"
                              f"producer_snapshot={wsl_root}/producer_snapshot/snapshot.json\n"
                              f"producer_snapshot_sha256={snapshot_digest}\n",encoding="utf-8")
            result=cov.validate_report_provenance(report,expected_sim="verilator")
            self.assertEqual(result["source_hashes_checked"],1)

    def test_missing_external_file_and_missing_source_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="stage9_missing_prov_",dir=cov.ROOT/"reports") as tmp:
            directory=Path(tmp); report=directory/"report.txt"
            report.write_text("Simulator: xsim\nprovenance_file=missing.txt\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"missing referenced provenance file"):
                cov.validate_report_provenance(report,expected_sim="xsim")
            report.write_text("Stage 6 validation simulator=verilator\nsha256 reports/no-such-stage9-source=0000000000000000000000000000000000000000000000000000000000000000\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"missing provenance source file"):
                cov.validate_report_provenance(report,expected_sim="verilator")

    def test_mismatched_inline_and_external_hashes_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="stage9_bad_hash_",dir=cov.ROOT/"reports") as tmp:
            directory=Path(tmp); _,digest,rel=self._fixture(directory)
            bad="0"*64 if digest!="0"*64 else "1"*64
            report=directory/"inline.txt"
            report.write_text(f"Stage 6 validation simulator=verilator\nsha256 {rel}={bad}\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"source provenance hash mismatch"):
                cov.validate_report_provenance(report,expected_sim="verilator")
            provenance=directory/"provenance.txt"
            provenance.write_text(f"simulator=xsim\nsha256 {rel}={bad}\n",encoding="utf-8")
            report.write_text(f"Simulator: xsim\nprovenance_file={provenance.as_posix()}\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"source provenance hash mismatch"):
                cov.validate_report_provenance(report,expected_sim="xsim")

    def test_historical_report_stays_strict_while_fresh_supplemental_producer_validates(self):
        with tempfile.TemporaryDirectory(prefix="stage9_old_and_fresh_prov_",dir=cov.ROOT/"reports") as tmp:
            directory=Path(tmp); source=directory/"producer.py"
            source.write_text("historical producer\n",encoding="utf-8")
            old_hash=hashlib.sha256(source.read_bytes()).hexdigest()
            historical_prov=directory/"historical.prov"
            historical_prov.write_text(f"simulator=verilator\nsha256 {source.relative_to(cov.ROOT).as_posix()}={old_hash}\n",encoding="utf-8")
            historical=directory/"historical.txt"
            historical.write_text(f"Simulator: verilator\nprovenance_file={historical_prov.as_posix()}\n",encoding="utf-8")
            source.write_text("fresh supplemental producer\n",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"source provenance hash mismatch"):
                cov.validate_report_provenance(historical,expected_sim="verilator")
            fresh_hash=hashlib.sha256(source.read_bytes()).hexdigest()
            fresh_prov=directory/"fresh.prov"
            fresh_prov.write_text(f"simulator=verilator\nsha256 {source.relative_to(cov.ROOT).as_posix()}={fresh_hash}\n",encoding="utf-8")
            fresh=directory/"fresh.txt"
            fresh.write_text(f"Simulator: verilator\nprovenance_file={fresh_prov.as_posix()}\n",encoding="utf-8")
            self.assertEqual(cov.validate_report_provenance(fresh,expected_sim="verilator")["source_hashes_checked"],1)

    def test_committed_historical_producer_snapshot_validates_without_current_source_match(self):
        rel="scripts/simulation/run_stage4_4.py"
        head=subprocess.run(["git","rev-parse","HEAD"],cwd=cov.ROOT,text=True,stdout=subprocess.PIPE,check=True).stdout.strip()
        snap=subprocess.run(["git","show",f"{head}:{rel}"],cwd=cov.ROOT,stdout=subprocess.PIPE,check=True).stdout
        digest=hashlib.sha256(snap).hexdigest()
        with tempfile.TemporaryDirectory(prefix="stage9_git_snapshot_prov_",dir=cov.ROOT/"reports") as tmp:
            directory=Path(tmp); provenance=directory/"provenance.txt"
            provenance.write_text(f"git_head={head}\nsimulator=verilator\nsha256 {rel}={digest}\n",encoding="utf-8")
            report=directory/"report.txt"
            report.write_text(f"Simulator: verilator\nprovenance_file={provenance.as_posix()}\n",encoding="utf-8")
            self.assertEqual(cov.validate_report_provenance(report,expected_sim="verilator")["source_hashes_checked"],1)

    def test_saved_historical_reports_stay_strict_and_supplemental_gap_is_reviewed(self):
        recorded_stage5="371a36b25d832c4a6581b8e96f3fa304243c256d1b9ce45c2da3524bde7385b6"
        recorded_supplement="443850e1bac59743145307e38e16302417341e0c701ded81612d707b045098e0"
        current=hashlib.sha256((cov.ROOT/"scripts/simulation/run_stage4_4.py").read_bytes()).hexdigest()
        self.assertNotEqual(recorded_stage5,current)
        self.assertNotEqual(recorded_supplement,current)
        for sim,stage5,gap in (
            ("verilator","reports/stage5_a_pipeline_verilator_20261110T053612Z.txt","reports/stage9_gap_verilator_20261110T102959Z.txt"),
            ("xsim","reports/stage5_a_pipeline_xsim_20261110T054111Z.txt","reports/stage9_gap_xsim_20261110T103419Z.txt")):
            old=cov.ROOT/stage5
            with self.subTest(sim=sim),self.assertRaisesRegex(ValueError,"source provenance hash mismatch: .*run_stage4_4.py"):
                cov.validate_report_provenance(old,expected_sim=sim)
            supplemental=cov.ROOT/gap
            text=supplemental.read_text(encoding="utf-8",errors="replace")
            with self.subTest(sim=sim,kind="supplemental"):
                result=cov.validate_saved_legacy_supplemental(supplemental,text,sim)
                self.assertEqual(result["source_hashes_checked"],303)
                self.assertEqual(result["source_provenance_status"],"DOCUMENTED_LIMITATION_RUNNER_SNAPSHOT_UNAVAILABLE")
                self.assertEqual(result["unresolved_source_hashes"],[{
                    "path":"scripts/simulation/run_stage4_4.py",
                    "recorded_sha256":recorded_supplement,
                    "status":"SOURCE_SNAPSHOT_UNAVAILABLE"}])

    def test_final_recovery_index_selects_snapshot_verified_gaps_and_all_73_reuses(self):
        expected={"verilator":"reports/stage9_gap_verilator_20261110T170227Z.txt",
                  "xsim":"reports/stage9_gap_xsim_20261110T173739Z.txt"}
        index=json.loads((cov.ROOT/"reports/stage9_coverage/recovery_prepared_recollected.json").read_text(encoding="utf-8"))
        self.assertEqual(index["provenance_policy"]["strict_source_provenance_closure"],"PASS")
        for sim,rel in expected.items():
            item=index["simulators"][sim]["stage5"]
            self.assertEqual(item["legacy_report"],rel)
            self.assertEqual(item["legacy_source_provenance_status"],"PASS")
            report=cov.ROOT/rel
            text=report.read_text(encoding="utf-8",errors="replace")
            provenance=cov.validate_report_provenance(report,text,sim)
            self.assertEqual(provenance["source_provenance_status"],"PASS")
            cov.validate_provenance_record(item|{
                "source_provenance_status":item["legacy_source_provenance_status"],
                "unresolved_source_hashes":item["legacy_unresolved_source_hashes"]},f"{sim} legacy")
            self.assertEqual(len(list((cov.ROOT/item["legacy_outdir"]).glob("*.pipe.trace"))),209)
            self.assertEqual(sum(len(list((cov.ROOT/index["simulators"][sim][stage]["outdir"]).glob("*.pipe.trace")))
                                 for stage in ("stage5","stage6","stage8")),73)
            with (cov.ROOT/f"reports/stage9_coverage/{sim}/runs.csv").open(newline="",encoding="utf-8") as source:
                runs=list(csv.DictReader(source))
            self.assertEqual(len(runs),282)
            self.assertEqual(sum(row.get("source_provenance_status")=="PASS" for row in runs),282)
            report_text=(cov.ROOT/f"reports/stage9_coverage/{sim}/report.txt").read_text(encoding="utf-8")
            self.assertIn("strict_provenance_closure=PASS unresolved_test_identities=0",report_text)
            self.assertIn("coverage_closure=CLOSED",report_text)

    def test_provenance_status_schema_rejects_missing_and_inconsistent_status(self):
        with self.assertRaisesRegex(ValueError,"missing or unsupported"):
            cov.validate_provenance_record({"unresolved_source_hashes":[]},"fixture")
        with self.assertRaisesRegex(ValueError,"conflicts"):
            cov.validate_provenance_record({"source_provenance_status":"PASS",
                                            "unresolved_source_hashes":[{"path":"runner.py"}]},"fixture")


if __name__=="__main__": unittest.main(verbosity=2)
