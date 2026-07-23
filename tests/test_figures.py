from fishery_repro.figures import make_all_figures


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

