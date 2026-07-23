from fishery_repro.config import ROOT


def test_each_figure_has_code_input_when_needed_and_results():
    for number in range(1, 11):
        folder = ROOT / "implementations" / f"figure_{number:02d}"
        assert (folder / "README.md").is_file()
        assert (folder / "run.py").is_file()
        assert len(list(folder.glob("*.png"))) == 1
        assert len(list(folder.glob("*.svg"))) == 0
        generated = folder / "generated_from_processed_data"
        assert len(list(generated.glob("*.png"))) == 1
        assert len(list(generated.glob("*.svg"))) == 1
        if number > 1:
            assert (folder / "input_data.csv").is_file()


def test_each_paper_table_has_data_and_validator():
    for number in range(1, 5):
        folder = ROOT / "implementations" / f"table_{number:02d}"
        assert (folder / "data.csv").is_file()
        assert (folder / "validate.py").is_file()
