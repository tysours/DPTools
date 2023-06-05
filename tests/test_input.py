import os
import pytest
import importlib
import argparse
import json

test_dir = os.path.abspath(os.path.dirname(__file__))

inputs = [os.path.join(test_dir, 'files', '00_ABW.db'),
          os.path.join(test_dir, 'files', '00_JBW.db')]

@pytest.fixture(scope='session')
def dataset(tmp_path_factory):
    dataset_dir = tmp_path_factory.mktemp('data')
    return dataset_dir

def get_cli(command):
    CLI = importlib.import_module(f'dptools.cli.{command}').CLI
    cli = CLI(argparse.ArgumentParser())
    return cli

def get_mock_hpc():
    return {'SBATCH_COMMENT': 'testing'}


# TODO: add API unit tests instead of just checking CLI command output
def test_input(dataset):
    cli = get_cli('input')
    args = argparse.Namespace(inputs=inputs, n=None, path=dataset, append=False)
    cli.main(args)

    assert 'type_map.json' in os.listdir(dataset)
    assert '00_ABW' in os.listdir(dataset)
    assert '00_JBW' in os.listdir(dataset)
    assert 'type.raw' in os.listdir(dataset / '00_ABW/test')

def test_train_single(tmp_path, dataset, monkeypatch):
    cli = get_cli('train')
    monkeypatch.setattr(cli, 'get_hpc_info', get_mock_hpc)
    train_dir = (tmp_path / 'train')
    args = argparse.Namespace(dataset=dataset, ensemble=False,
            submit=False, path=train_dir, input=None)

    cli.main(args)
    assert 'dptools.train.sh' in os.listdir(train_dir)
    assert 'in.json' in os.listdir(train_dir)

def test_train_ensemble(tmp_path, dataset, monkeypatch):
    cli = get_cli('train')
    monkeypatch.setattr(cli, 'get_hpc_info', get_mock_hpc)
    train_dir = (tmp_path / 'train')
    args = argparse.Namespace(dataset=dataset, ensemble=True,
            submit=False, path=train_dir, input=None)

    cli.main(args)
    ens_dirs = [os.path.join(train_dir, d) for d in ['00', '01', '02', '03']]
    seeds = []
    for d in ens_dirs:
        with open(os.path.join(d, 'in.json')) as file:
            in_json = json.loads(file.read())
        seed = in_json["model"]["descriptor"]["seed"]
        if seed not in seeds:
            raise ValueError("Missing unique values for seeds")
        seeds.append(seed)
