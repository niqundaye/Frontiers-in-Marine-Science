from fishery_repro.figures import _style, figure_01, make_all_figures


def test_all_ten_figures_render(tmp_path):
    paths = make_all_figures(
        output_dir=tmp_path / "figures",
        data_dir=tmp_path / "data",
        formats=("png",),
        dpi=80,
        step=50,
    )
    assert len(paths) == 10
    assert all(path.exists() and path.stat().st_size > 10_000 for path in paths)


def test_svg_render_is_byte_deterministic(tmp_path):
    _style()
    first = figure_01(tmp_path / "first", ("svg",), 80)[0]
    second = figure_01(tmp_path / "second", ("svg",), 80)[0]
    assert first.read_bytes() == second.read_bytes()
