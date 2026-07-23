from fishery_repro.manifest import write_manifest


def test_manifest_supports_output_root_outside_repository(tmp_path):
    output = tmp_path / "external_output"
    output.mkdir()
    (output / "value.txt").write_text("auditable\n", encoding="utf-8")
    manifest = write_manifest(output, output / "MANIFEST.csv")
    text = manifest.read_text(encoding="utf-8")
    assert "value.txt" in text
    assert "auditable" not in text
