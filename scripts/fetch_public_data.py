from fishery_repro.public_data import download_public_data


if __name__ == "__main__":
    for name, path in download_public_data().items():
        print(f"{name}: {path.resolve()}")
