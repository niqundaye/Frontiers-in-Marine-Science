from fishery_repro.integrity import hash_mode, sha256_file


def test_text_hash_is_stable_across_line_endings(tmp_path):
    lf = tmp_path / "lf.csv"
    crlf = tmp_path / "crlf.csv"
    lf.write_bytes(b"a,b\n1,2\n")
    crlf.write_bytes(b"a,b\r\n1,2\r\n")
    assert hash_mode(lf) == "text_lf"
    assert sha256_file(lf) == sha256_file(crlf)


def test_binary_hash_preserves_raw_bytes(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"\x89PNG\r\n")
    second.write_bytes(b"\x89PNG\n")
    assert hash_mode(first) == "binary"
    assert sha256_file(first) != sha256_file(second)
